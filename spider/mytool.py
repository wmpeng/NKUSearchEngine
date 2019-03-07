import codecs
import hashlib
import json
import os
import time
from typing import Dict, Any
import difflib


class Config:
    _conf_dict: Dict[str, str] = dict()

    @classmethod
    def read_json(cls):
        if not cls._conf_dict:
            with open("../config/config.json", "r") as f:
                json_str = f.read()
                cls._conf_dict = json.loads(json_str)
            with open("../config/secret-config.json", "r") as f:
                json_str = f.read()
                cls._conf_dict.update(json.loads(json_str))

    @classmethod
    def get(cls, key: str) -> Any:
        val = cls._conf_dict.get(key)
        assert val is not None
        return val

    @classmethod
    def set(cls, key: str, val: str):
        cls._conf_dict[key] = val


Config.read_json()


# Config.conf_dict["job.start_url"] = "http://www.nankai.edu.cn"
# Config.conf_dict["job.start_url"] = "http://xxgk.nankai.edu.cn/_redirect?siteId=55&columnId=2769&articleId=105109"
# Config._conf_dict["job.start_url"] = "http://cc.nankai.edu.cn"
# Config._conf_dict["job.start_url"] = "aaaa"


class MyUtil:
    @staticmethod
    def md5(s: str):
        m = hashlib.md5()
        m.update(s.encode("utf8"))
        return m.hexdigest()

    @staticmethod
    def create_folders():
        for path_name, path in Config._conf_dict.items():
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

    @staticmethod
    def gen_file_name(path: str):
        return path.format(time.strftime('%Y%m%dT%H%M%S', time.localtime()))


def print_info(fn):
    def print_name(*args):
        print("[fn_name]", fn.__name__)
        print("[fn_args]", *args)
        result = fn(*args)
        print("[fn_return]", result)
        return result

    return print_name
