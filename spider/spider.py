import http.client
import re
import urllib.parse
import urllib.request
from queue import Queue
from typing import Set

from myparser import MyHTMLParser
from mytool import Config, MyUtil


class Spider:
    valid_rul = Config.get("spider.valid_url")
    invalid_file_type = Config.get("spider.invalid_file_type")
    page_path = Config.get("path.page")
    doc_path = Config.get("spider.path.document")

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
    def write_page(cls, response: http.client.HTTPResponse) -> bytes:
        data = response.read()
        path = cls.page_path + MyUtil.md5(response.geturl()) + ".html"
        MyUtil.write_data(data, path)
        return data

    @classmethod
    def write_doc(cls, text: str, url: str):
        path = cls.doc_path + MyUtil.md5(url) + ".txt"
        MyUtil.write_str(text, path)

    def search(self, url: str):
        self.visited.add(url)

        response: http.client.HTTPResponse = urllib.request.urlopen(url)
        content_type = response.getheader('Content-Type')
        charset = content_type.split("charset=")[-1]
        if "text/html" in content_type:  # html
            data = self.write_page(response)

            parser = MyHTMLParser(url)
            parser.feed(data.decode(charset, 'ignore'))
            for new_url in parser.new_urls:
                if new_url not in self.visited and self.url_validation(new_url):
                    self.bfs_queue.put(new_url)
            self.write_doc(parser.text, url)
        else:  # other file
            if self.file_type_validation(url):
                self.write_page(response)

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
    # begin_url = "http://cs.nankai.edu.cn/index.php/zh/2016-12-07-18-31-35/1588-2019-2"
    begin_url = "http://www.nankai.edu.cn/"
    # begin_url = "http://343241324.nankai.edu.cn/"
    spider.run(begin_url, 1)
    print("\n".join(spider.visited))
    print("end")
    # print(Config.doc_path())
