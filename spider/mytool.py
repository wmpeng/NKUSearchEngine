import codecs
import hashlib
import json
import os
from typing import Dict
import difflib


class Config:
    conf_dict: Dict[str, str] = dict()

    @classmethod
    def read_json(cls):
        if not cls.conf_dict:
            with open("../config/config.json", "r") as f:
                json_str = f.read()
                cls.conf_dict = json.loads(json_str)

    # @classmethod
    # def doc_path(cls) -> str:
    #     return cls.conf_dict["path.document"]
    #
    # @classmethod
    # def page_path(cls) -> str:
    #     return cls.conf_dict["path.page"]
    #
    # @classmethod
    # def default_interval(cls) -> float:
    #     return float(cls.conf_dict["redis.default_interval"])

    @classmethod
    def get(cls, key: str) -> str:
        val = cls.conf_dict.get(key)
        assert val is not None
        return val

    @classmethod
    def set(cls, key: str, val: str):
        cls.conf_dict[key] = val


Config.read_json()
Config.conf_dict["job.start_url"] = "http://www.nankai.edu.cn"


class MyUtil:
    @staticmethod
    def md5(s: str):
        m = hashlib.md5()
        m.update(s.encode("utf8"))
        return m.hexdigest()

    @staticmethod
    def create_folders():
        for path_name, path in Config.conf_dict.items():
            if path_name.startswith("path.") and not os.path.exists(path):
                os.makedirs(path)

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

    @staticmethod
    def read_str(path) -> str:
        f = open(path, "r", encoding="UTF-8")
        ret = f.read()
        f.close()
        return ret

    @staticmethod
    def diff_ratio(str1: str, str2: str) -> float:
        return difflib.SequenceMatcher(None, str1, str2).ratio()

    @staticmethod
    def normalize_url(url: str) -> str:
        if url.endswith("/"):
            return url[:-1]
        else:
            return url


def print_info(fn):
    def print_name(*args):
        print("[fn_name]", fn.__name__)
        result = fn(*args)
        print("[fn_return]", result)
        return result

    return print_name
