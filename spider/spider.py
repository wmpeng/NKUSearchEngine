import os
import re
import string
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
from http.client import HTTPResponse
from queue import Queue
from typing import Set
from urllib.parse import quote

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FireFoxOptions

from myparser import MyHTMLParser
from mytool import Config, MyUtil
from redis_access import MyRedisUtil


class Spider:
    valid_rul = Config.get("spider.valid_url")
    invalid_file_type = Config.get("spider.invalid_file_type")
    page_folder = Config.get("path.page")
    doc_folder = Config.get("path.document")

    def __init__(self):
        self.bfs_queue = Queue()
        self.visited: Set[str] = set()
        MyUtil.create_folders()
        options = FireFoxOptions()
        options.add_argument('--headless')
        self.driver = webdriver.Firefox(options=options)
        self.driver.set_window_size(1920, 1080 * 100)

    def quit(self):
        self.driver.quit()

    @classmethod
    def url_validation(cls, url: str) -> bool:
        return url is not None and re.search(cls.valid_rul, url)

    @classmethod
    def file_type_validation(cls, url: str) -> bool:
        return not bool(re.search(cls.invalid_file_type, url.split(".")[-1]))

    @classmethod
    def write_data(cls, response: HTTPResponse, ext: str) -> bytes:
        data = response.read()
        path = cls.page_folder + MyUtil.md5(response.geturl()) + "." + ext
        MyUtil.write_data(data, path)
        return data

    @classmethod
    def write_page(cls, text: str, path: str):
        MyUtil.write_str(text, path)

    @classmethod
    def write_doc(cls, text: str, path: str):
        MyUtil.write_str(text, path)

    @staticmethod
    def need_webdriver(html_text: str) -> bool:
        soup = BeautifulSoup(html_text, "lxml")
        len_html = len(html_text)
        len_script = len("".join([str(_) for _ in soup.find_all("script")]))
        return not soup.find("title") or len_script / len_html > 0.5

    def process_html_text(self, html_text: str, url: str):
        parser = MyHTMLParser(url)
        parser.feed(html_text)
        for new_url in parser.new_urls:
            if new_url not in self.visited and self.url_validation(new_url):
                self.bfs_queue.put(new_url)

        doc_path = self.doc_folder + MyUtil.md5(url) + ".txt"
        page_path = self.page_folder + MyUtil.md5(url) + ".html"
        if not os.path.exists(doc_path) or not MyRedisUtil.is_visited(url):
            MyRedisUtil.first_time(url)
            self.write_page(html_text, page_path)
            self.write_doc(parser.text, doc_path)
        else:
            old_text = MyUtil.read_str(doc_path)
            diff_ratio = MyUtil.diff_ratio(old_text, parser.text)
            if diff_ratio > 0.99:
                MyRedisUtil.unchanged(url)
            else:
                MyRedisUtil.changed(url)
                self.write_page(html_text, page_path)
                self.write_doc(parser.text, doc_path)

    def process_html_by_webdriver(self, url: str):
        print("process_html_by_webdriver")
        self.driver.get(url)
        html_text = self.driver.page_source
        self.process_html_text(html_text, url)

    def process_html(self, response: HTTPResponse, url: str) -> bool:
        print("process_html")
        content_type = response.getheader('Content-Type')
        charset = "UTF-8" if "charset=" not in content_type \
            else content_type.split("charset=")[-1]
        data = response.read()
        if self.need_webdriver(data.decode(charset, 'ignore')):
            return False

        self.process_html_text(data.decode(charset, 'ignore'), url)
        return True

    def process_file(self, response: HTTPResponse, url: str):
        if self.file_type_validation(url):
            self.write_data(response, response.geturl().split(".")[-1])

    def process_one_url(self, url: str):
        url = quote(url, safe=string.printable)
        headers = {'User-Agent': Config.get("spider.browser_user_agent")}
        req = urllib.request.Request(url=url, headers=headers)
        response: HTTPResponse = urllib.request.urlopen(req)
        content_type = response.getheader('Content-Type')
        if "text/html" in content_type:  # html
            if not self.process_html(response, url):
                self.process_html_by_webdriver(url)
        else:  # other file
            self.process_file(response, url)

    def search(self, url: str):
        self.visited.add(url)
        if not MyRedisUtil.need_search(url):
            return

        try:
            self.process_one_url(url)
        except (urllib.error.HTTPError, urllib.error.URLError, ConnectionResetError) as error:
            MyRedisUtil.set_known_exception(url, error)
            MyRedisUtil.exceptional(url)
            print("[exception]", type(error), error)
        except BaseException as error:
            MyRedisUtil.set_unknown_exception(url, error)
            MyRedisUtil.exceptional(url)
            print("[exception]", type(error), error)
            traceback.print_exc()

    def new_job(self):
        MyRedisUtil.flush()
        self.bfs_queue.put(Config.get("job.start_url"))

    def resume_batch(self):
        self.bfs_queue = MyRedisUtil.get_queue()
        self.visited = MyRedisUtil.get_visited()

    def new_batch(self):
        all_urls = MyRedisUtil.get_all_urls()
        if all_urls:
            for url in all_urls:
                self.bfs_queue.put(url)
        else:
            self.bfs_queue.put(Config.get("job.start_url"))

    def run(self, mode: str, max_doc_num: int = 2 ** 20):
        assert (mode in ["new_job", "resume", "new_batch"])

        if mode == "new_job":
            self.new_job()
        elif mode == "resume" and MyRedisUtil.stored_breakpoint():
            self.resume_batch()
        else:
            self.new_batch()

        for doc_cnt in range(max_doc_num):
            print("count", doc_cnt, "queue_size", self.bfs_queue.qsize())
            if self.bfs_queue.empty():
                break
            curr_url: str = MyUtil.normalize_url(self.bfs_queue.get())
            print(time.time(), "searching: ", curr_url)
            self.search(curr_url)

        MyRedisUtil.store_visited(self.visited)
        MyRedisUtil.store_queue(self.bfs_queue)


if __name__ == "__main__":
    print("begin")
    spider = Spider()
    # begin_url = "http://cs.nankai.edu.cn/index.php/zh/2016-12-07-18-31-35/1588-2019-2"
    # begin_url = "http://www.nankai.edu.cn/"
    # begin_url = "http://cs.nankai.edu.cn/"
    spider.run("new_job", 1)
    # spider.quit()
    # spider.run("new_batch", 10)
    # spider.run("resume", 10)
    print("end")
