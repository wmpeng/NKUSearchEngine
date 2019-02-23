import codecs
import hashlib
import json
import os
from typing import Dict


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
        return cls.conf_dict.get(key)


Config.read_json()


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
