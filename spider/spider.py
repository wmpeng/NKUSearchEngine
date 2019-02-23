import codecs
import http.client
import urllib.parse
import urllib.request
from queue import Queue
from typing import Set

from mytool import Config, MyUtil
from myparser import MyHTMLParser


class Spider:
    def __init__(self):
        self.bfs_queue = Queue()
        self.visited_url: Set[str] = set()
        MyUtil.create_folders()

    @staticmethod
    def url_validation(url: str) -> bool:
        return url is not None

    @staticmethod
    def file_type_validation(url: str) -> bool:
        return url.split(".")[-1] != "mp4"

    @staticmethod
    def write_data(data: bytes, path: str):
        f = codecs.open(path, 'wb')
        f.write(data)
        f.close()

    @staticmethod
    def write_str(text: str, path: str):
        f = open(path, "w", encoding="UTF-8")
        f.write(text)
        f.close()

    def write_response(self, response: http.client.HTTPResponse):
        data = response.read()
        path = Config.page_path() + MyUtil.md5(response.geturl()) + ".html"
        self.write_data(data, path)

    def search(self, url: str):
        self.visited_url.add(url)
        if not self.url_validation(url):
            return

        response: http.client.HTTPResponse = urllib.request.urlopen(url)
        content_type = response.getheader('Content-Type')
        charset = content_type.split("charset=")[-1]
        if "text/html" in content_type:
            data = response.read()
            path = Config.page_path() + MyUtil.md5(response.geturl()) + ".html"
            self.write_data(data, path)

            parser = MyHTMLParser(url)
            parser.feed(data.decode(charset, 'ignore'))
            for new_url in parser.new_urls:
                if new_url not in self.visited_url:
                    self.bfs_queue.put(new_url)
            path = Config.doc_path() + MyUtil.md5(response.geturl()) + ".txt"
            self.write_str(parser.text, path)
        else:
            if self.file_type_validation(url):
                self.write_response(response)

    def run(self, start_url: str, max_doc_num: int = 2 ** 20):
        self.bfs_queue.put(start_url)
        for doc_cnt in range(max_doc_num):
            if self.bfs_queue.empty():
                break
            curr_url = self.bfs_queue.get()
            self.search(curr_url)


if __name__ == "__main__":
    print("begin")
    spider = Spider()
    spider.run("http://www.nankai.edu.cn/", 5)
    print("end")
    # print(Config.doc_path())
