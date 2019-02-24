import http.client
import os
import re
import time
import traceback
import urllib.parse
import urllib.request
import urllib.error
from queue import Queue
from typing import Set

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

    @classmethod
    def url_validation(cls, url: str) -> bool:
        return url is not None and re.search(cls.valid_rul, url)

    @classmethod
    def file_type_validation(cls, url: str) -> bool:
        return bool(re.search(cls.invalid_file_type, url.split(".")[-1]))

    @classmethod
    def write_data(cls, response: http.client.HTTPResponse) -> bytes:
        data = response.read()
        path = cls.page_folder + MyUtil.md5(response.geturl()) + ".html"
        MyUtil.write_data(data, path)
        return data

    @classmethod
    def write_page(cls, data: bytes, path: str):
        MyUtil.write_data(data, path)

    @classmethod
    def write_doc(cls, text: str, path: str):
        MyUtil.write_str(text, path)

    def process_html(self, response: http.client.HTTPResponse, url: str):
        content_type = response.getheader('Content-Type')
        charset = content_type.split("charset=")[-1] \
            if "charset=" in content_type else "UTF-8"
        data = response.read()

        parser = MyHTMLParser(url)
        parser.feed(data.decode(charset, 'ignore'))
        for new_url in parser.new_urls:
            if new_url not in self.visited and self.url_validation(new_url):
                self.bfs_queue.put(new_url)

        doc_path = self.doc_folder + MyUtil.md5(url) + ".txt"
        page_path = self.page_folder + MyUtil.md5(url) + ".html"
        if not os.path.exists(doc_path) or not MyRedisUtil.is_visited(url):
            MyRedisUtil.first_time(url)
            self.write_page(data, page_path)
            self.write_doc(parser.text, doc_path)
        else:
            old_text = MyUtil.read_str(doc_path)
            diff_ratio = MyUtil.diff_ratio(old_text, parser.text)
            if diff_ratio > 0.99:
                MyRedisUtil.unchanged(url)
            else:
                MyRedisUtil.changed(url)
                self.write_page(data, page_path)
                self.write_doc(parser.text, doc_path)

    def process_file(self, response: http.client.HTTPResponse, url: str):
        if self.file_type_validation(url):
            self.write_data(response)

    def process_one_url(self, url: str):
        response: http.client.HTTPResponse = urllib.request.urlopen(url)
        content_type = response.getheader('Content-Type')
        if "text/html" in content_type:  # html
            self.process_html(response, url)
        else:  # other file
            self.process_file(response, url)

    def search(self, url: str):
        self.visited.add(url)
        if not MyRedisUtil.need_search(url):
            return

        try:
            self.process_one_url(url)
        except urllib.error.HTTPError as error:
            MyRedisUtil.set_exception(url, error)
        except urllib.error.URLError as error:
            MyRedisUtil.set_exception(url, error)
        except ConnectionResetError as error:
            MyRedisUtil.set_exception(url, error)
        except BaseException as error:
            MyRedisUtil.set_exception(url, error)
            print("[exception]", type(error), error)
            traceback.print_exc()

    def new_job(self, max_doc_num):
        all_urls = MyRedisUtil.get_all_urls()
        if all_urls:
            for url in all_urls:
                self.bfs_queue.put(url)
        else:
            self.bfs_queue.put(Config.get("job.start_url"))

        for doc_cnt in range(max_doc_num):
            print("count", doc_cnt, "queue_size", self.bfs_queue.qsize())
            if self.bfs_queue.empty():
                break
            curr_url: str = MyUtil.normalize_url(self.bfs_queue.get())
            print(time.time(), "searching", curr_url)
            self.search(curr_url)

    def resume_job(self, max_doc_num):
        self.bfs_queue = MyRedisUtil.get_queue()
        self.visited = MyRedisUtil.get_visited()

        for doc_cnt in range(max_doc_num):
            print("count", doc_cnt, "queue_size", self.bfs_queue.qsize())
            if self.bfs_queue.empty():
                break
            curr_url: str = MyUtil.normalize_url(self.bfs_queue.get())
            print(time.time(), "searching", curr_url)
            self.search(curr_url)

    def run(self, max_doc_num: int = 2 ** 20):
        self.resume_job(max_doc_num)
        MyRedisUtil.store_visited(self.visited)
        MyRedisUtil.store_queue(self.bfs_queue)


if __name__ == "__main__":
    print("begin")
    spider = Spider()
    # begin_url = "http://cs.nankai.edu.cn/index.php/zh/2016-12-07-18-31-35/1588-2019-2"
    # begin_url = "http://www.nankai.edu.cn/"
    # begin_url = "http://cs.nankai.edu.cn/"
    spider.run(10)
    print("end")
