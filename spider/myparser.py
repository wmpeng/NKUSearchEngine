import re
import urllib.parse
from html.parser import HTMLParser
from typing import List


class MyHTMLParser(HTMLParser):
    def __init__(self, curr_url: str):
        super().__init__()
        self.curr_url: str = curr_url
        self.new_urls: List[str] = []
        self.text: str = ""

    # @staticmethod
    # def href_validation(val):
    #     return val not in ["", "#"] and val is not None

    @staticmethod
    def content_tag_validation(tag: str):
        return tag not in ['script', 'style']

    def handle_starttag(self, tag, attrs):
        if tag == 'a':  # link
            # attr[1] is None in some conditions
            attrs = {attr[0]: str(attr[1]).strip() for attr in attrs}
            if "href" in attrs:
                new_url = urllib.parse.urljoin(self.curr_url, attrs.get("href"))
                self.new_urls.append(new_url)

    def handle_data(self, data: str):
        if not self.content_tag_validation(self.lasttag):
            return
        text = data.strip()
        if re.search(r'\w', text):
            self.text += text + '\n'

    def error(self, message):
        print(message)
