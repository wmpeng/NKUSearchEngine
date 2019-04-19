import os
import sys
import re
import shutil
import string
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
from urllib.request import OpenerDirector
from http.client import HTTPResponse
from urllib.parse import quote

from bs4 import BeautifulSoup
import selenium
from selenium import webdriver
from selenium.webdriver import FirefoxProfile
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FireFoxOptions

from myparser import MyHTMLParser
from mytool import Config, MyUtil
from redis_access import MyRedisUtil


class Spider:
    valid_rul = Config.get("spider.valid_url")
    invalid_file_type = Config.get("spider.invalid_file_type")
    page_folder = Config.get("path.page")
    doc_folder = Config.get("path.document")
    download_temp_folder = Config.get("path.download_temp_dir")

    def __init__(self, download_file=True, debug_mode=False):
        # self.bfs_queue = Queue()
        # self.visited: Set[str] = set()
        MyUtil.create_folders()
        base_handler = urllib.request.BaseHandler()
        proxy_handler = None if Config.get("spider.proxy_url") == "no_host" \
            else urllib.request.ProxyHandler({Config.get("spider.proxy_type"): Config.get("spider.proxy_url")})
        self.base_opener: OpenerDirector = urllib.request.build_opener(base_handler)
        self.proxy_opener: OpenerDirector = urllib.request.build_opener(proxy_handler)

        self.download_file = download_file
        if Config.get("spider.browser") == "firefox":
            self.profile = FirefoxProfile()
            if download_file:
                # 0 for desktop, 1 for system downloads folder, 2 for "browser.download.dir"
                self.profile.set_preference("browser.download.folderList", 2)
                self.profile.set_preference("browser.download.manager.showWhenStarting", False)
                self.profile.set_preference("browser.download.dir", self.download_temp_folder)
                self.profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/octet-stream")
            self.profile.set_preference("permissions.default.image", 2)  # no images
            self.profile.set_preference("permissions.default.stylesheet", 2)  # no CSS
            self.profile.set_preference("dom.ipc.plugins.enabled.libflashplayer.so", False)  # no Flash
            self.driver_options = FireFoxOptions()
            self.driver_options.add_argument('--headless')
        elif Config.get("spider.browser") == "chrome":
            self.driver_options = ChromeOptions()
            self.driver_options.add_argument('--no-sandbox')
            # self.driver_options.add_argument('--disable-dev-shm-usage')
            self.driver_options.add_argument('--disable-gpu')
            # self.driver_options.add_argument('--log-level=3')
            self.driver_options.add_argument('--headless')
            self.driver_options.add_argument('--proxy-server={}'.format(Config.get("spider.proxy_url")))
            prefs = {'profile.default_content_settings.popups': 0,
                     'download.default_directory': self.download_temp_folder,
                     "profile.managed_default_content_settings.images": 2}  # no images
            self.driver_options.add_experimental_option('prefs', prefs)
        self.driver = None

        self.log_file = None
        if not debug_mode:
            self.log_file = open(MyUtil.gen_file_name(Config.get("path.log") + "/{}.log"), "w")

    def quit(self):
        if self.driver is not None:
            self.driver.quit()
        if self.log_file is not None:
            self.log_file.close()

    @classmethod
    def url_validation(cls, url: str) -> bool:
        return url is not None \
               and bool(re.search(cls.valid_rul, url)) \
               and not bool(re.search(Config.get("spider.invalid_url"), url))

    @classmethod
    def file_type_validation(cls, url: str) -> bool:
        return not bool(re.search(cls.invalid_file_type, url.split(".")[-1]))

    @classmethod
    def write_data(cls, response: HTTPResponse, url: str, ext: str) -> bytes:
        data = response.read()
        path = cls.doc_folder + MyUtil.md5(url) + "." + ext
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
        return not soup.find("title") or len_script / len_html > 0.5 or len_html < 1000

    def process_html_text(self, html_text: str, url: str):
        # print("process_html_text")
        parser = MyHTMLParser(url)
        parser.feed(html_text)
        for new_url in parser.new_urls:
            # if new_url not in self.visited and self.url_validation(new_url):
            if self.url_validation(new_url) and not MyRedisUtil.check_visited(new_url):
                # self.bfs_queue.put(new_url)
                MyRedisUtil.push_need_search(new_url)

        # print("!")
        doc_path = self.doc_folder + MyUtil.md5(url) + ".txt"
        page_path = self.page_folder + MyUtil.md5(url) + ".html"
        if not os.path.exists(doc_path) or not MyRedisUtil.have_visited(url):
            MyRedisUtil.first_time_visit(url)
            self.write_page(html_text, page_path)
            self.write_doc(parser.text, doc_path)
        else:
            old_text = MyUtil.read_str(doc_path)
            diff_ratio = MyUtil.diff_ratio(old_text, parser.text)
            if diff_ratio > 0.99:
                MyRedisUtil.unchanged_visit(url)
            else:
                MyRedisUtil.changed_visit(url)
                self.write_page(html_text, page_path)
                self.write_doc(parser.text, doc_path)

    def process_html_by_webdriver(self, url: str):
        print("process_html_by_webdriver", file=self.log_file)
        if self.driver is None:
            if Config.get("spider.browser") == "firefox":
                self.driver = webdriver.Firefox(firefox_profile=self.profile, options=self.driver_options)
            elif Config.get("spider.browser") == "chrome":
                self.driver = webdriver.Chrome(options=self.driver_options)
            self.driver.set_window_size(1920, 1080 * 100)
            self.driver.set_page_load_timeout(Config.get("spider.driver.page_load_timeout"))  # in seconds
            self.driver.set_script_timeout(Config.get("spider.driver.script_timeout"))  # in seconds

        if self.download_file:
            for file_name in os.listdir(self.download_temp_folder):
                os.remove(self.download_temp_folder + "\\" + file_name)

        self.driver.get(url)
        try:
            self.driver.switch_to.alert.accept()
        except selenium.common.exceptions.NoAlertPresentException:
            pass
        except BaseException:
            raise

        html_text = self.driver.page_source
        self.process_html_text(html_text, url)

        if self.download_file:
            time.sleep(Config.get("spider.driver.wait_download_max_sec"))
            if os.listdir(self.download_temp_folder):
                file_name = os.listdir(self.download_temp_folder)[0]
                old_path = self.download_temp_folder + "\\" + file_name
                ext = file_name.split(".")[-1] if "." in file_name else ""
                new_file_name = MyUtil.md5(url) + "." + ext
                new_path = self.doc_folder + "\\" + new_file_name
                shutil.move(old_path, new_path)

    def process_html(self, response: HTTPResponse, url: str) -> bool:
        # print("process_html")
        content_type = response.getheader('Content-Type')
        charset = content_type.split("charset=")[-1] if "charset=" in content_type else "UTF-8"
        data = response.read()
        if self.need_webdriver(data.decode(charset, 'ignore')):
            return False

        self.process_html_text(data.decode(charset, 'ignore'), url)
        return True

    def process_file(self, response: HTTPResponse, url: str):
        if self.download_file and self.file_type_validation(url):
            self.write_data(response, url, response.geturl().split(".")[-1])

    def process_one_url(self, url: str):
        # print("process_one_url")
        url = quote(url, safe=string.printable)
        headers = {'User-Agent': Config.get("spider.browser_user_agent")}
        req = urllib.request.Request(url=url, headers=headers)
        # response: HTTPResponse = urllib.request.urlopen(req, timeout=Config.get("spider.urlopen_timeout"))
        try:
            print("try self.base_opener")
            response: HTTPResponse = self.base_opener.open(req, timeout=Config.get("spider.urlopen_timeout"))
        except urllib.error.HTTPError as e:
            if e.code == 403 and self.proxy_opener is not None:  # Forbidden
                print("try self.proxy_opener")
                response: HTTPResponse = self.proxy_opener.open(req, timeout=Config.get("spider.urlopen_timeout"))
            else:
                raise
        content_type = response.getheader('Content-Type')
        if "text/html" in content_type:  # html
            if not self.process_html(response, url):
                self.process_html_by_webdriver(url)
        else:  # other file
            self.process_file(response, url)

    def search(self, url: str):
        print(time.time(), "searching: ", url, MyUtil.md5(url), file=self.log_file)
        # self.visited.add(url)
        MyRedisUtil.push_visited(url)
        if not MyRedisUtil.need_search(url) or not self.url_validation(url):
            return

        try:
            self.process_one_url(url)
        except (urllib.error.HTTPError, urllib.error.URLError, ConnectionResetError) as e:
            MyRedisUtil.set_known_exception(url, e)
            MyRedisUtil.exceptional_visit(url)
            print("[exception]", type(e), e, file=self.log_file)
        except selenium.common.exceptions.WebDriverException as e:
            self.driver.quit()
            self.driver = None
            MyRedisUtil.set_known_exception(url, e)
            MyRedisUtil.exceptional_visit(url)
            print("[exception]", type(e), e, file=self.log_file)
        except (KeyboardInterrupt, SystemExit):
            raise
        except BaseException as e:
            MyRedisUtil.set_unknown_exception(url, e)
            MyRedisUtil.exceptional_visit(url)
            print("[exception]", type(e), e, file=self.log_file)
            traceback.print_exc(file=self.log_file)

    @staticmethod
    def new_job():
        MyRedisUtil.flush()
        # self.bfs_queue.put(Config.get("job.start_url"))
        MyRedisUtil.push_need_search(Config.get("job.start_url"))

    @staticmethod
    def resume_batch():
        # self.bfs_queue = MyRedisUtil.get_queue()
        # self.visited = MyRedisUtil.get_visited()
        pass

    @staticmethod
    def new_batch():
        all_urls = MyRedisUtil.get_all_urls()
        if all_urls:
            for url in all_urls:
                # self.bfs_queue.put(url)
                MyRedisUtil.push_need_search(url)
        else:
            # self.bfs_queue.put(Config.get("job.start_url"))
            MyRedisUtil.push_need_search(Config.get("job.start_url"))

    def run(self, mode: str, max_doc_num: int = 2 ** 20):
        assert (mode in ["new_job", "resume", "new_batch"])

        if mode == "new_job":
            self.new_job()
        elif mode == "resume":
            if MyRedisUtil.need_search_num() == 0:
                return False
            else:
                self.resume_batch()
        elif mode == "new_batch":
            self.new_batch()
        else:
            print("invalid mode")
            exit(-1)

        for doc_cnt in range(max_doc_num):
            try:
                # print("count", doc_cnt, "queue_size", self.bfs_queue.qsize(), file=self.log_file)
                queue_size = MyRedisUtil.need_search_num()
                print("count", doc_cnt, "queue_size", queue_size, file=self.log_file)
                if queue_size == 0:
                    break
                # curr_url: str = MyUtil.normalize_url(self.bfs_queue.get())
                curr_url: str = MyUtil.normalize_url(MyRedisUtil.pop_need_search())
                self.search(curr_url)
            except (KeyboardInterrupt, SystemExit):
                raise
            except BaseException as e:
                MyRedisUtil.set_unknown_exception("", e)
                print("[exception]", type(e), e, file=self.log_file)
                traceback.print_exc(file=self.log_file)

        # MyRedisUtil.store_visited(self.visited)
        # MyRedisUtil.store_queue(self.bfs_queue)
        return True


if __name__ == "__main__":
    print("begin")
    spider = Spider(download_file=False, debug_mode=True)

    try:
        mode_ = sys.argv[1]
        max_doc_num_ = int(sys.argv[2])
    except BaseException:
        print("invalid parameters")
        exit(-1)

    try:
        spider.run(mode_, max_doc_num_)
    except KeyboardInterrupt as error:
        print("Exit by KeyboardInterrupt.")

    spider.quit()
    print("end")
