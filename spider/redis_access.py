from typing import Union, List

import redis
import time

from mytool import Config, MyUtil, print_info


# service redis stop
class MyRedisUtil:
    _host = Config.get("redis.host")
    _port = int(Config.get("redis.port"))
    _pool = redis.ConnectionPool(host=_host, port=_port, decode_responses=True)
    _redis = redis.Redis(connection_pool=_pool)
    _default_interval = float(Config.get("job.default_interval"))
    _min_interval = float(Config.get("job.min_interval"))
    _max_interval = float(Config.get("job.max_interval"))
    _start_md5 = MyUtil.md5(MyUtil.normalize_url(Config.get("job.start_url")))

    @classmethod
    def _set(cls, name: str, key: str, val: str):
        cls._redis.hset(cls._start_md5 + "_" + name, key, val)

    @classmethod
    def _get(cls, name: str, key: str) -> str:
        return cls._redis.hget(cls._start_md5 + "_" + name, key)

    @classmethod
    def _hvals(cls, name: str):
        return cls._redis.hvals(cls._start_md5 + "_" + name)

    @classmethod
    def _set_url(cls, md5: str, url: str):
        cls._set("url", md5, url)

    @classmethod
    def _get_url(cls, md5: str):
        cls._get("url", md5)

    @classmethod
    def _set_visited(cls, md5: str, ts: float):
        cls._set("visited", md5, str(ts))

    @classmethod
    def _get_visited(cls, md5: str) -> Union[float, None]:
        val = cls._get("visited", md5)
        if val is None:
            return val
        else:
            return float(val)

    @classmethod
    def _set_next_time(cls, md5: str, ts: float):
        cls._set("next_time", md5, str(ts))

    @classmethod
    def _get_next_time(cls, md5: str) -> Union[float, None]:
        val = cls._get("next_time", md5)
        if val is None:
            return val
        else:
            return float(val)

    @classmethod
    def _set_interval(cls, md5: str, interval: float):
        cls._set("interval", md5, str(interval))

    @classmethod
    def _get_interval(cls, md5: str) -> Union[float, None]:
        val = cls._get("interval", md5)
        if val is None:
            return val
        else:
            return float(val)

    @classmethod
    def _visit(cls, md5: str, interval: float):
        ts = time.time()
        cls._set_visited(md5, ts)
        cls._set_interval(md5, interval)
        cls._set_next_time(md5, ts + interval)

    @classmethod
    @print_info
    def is_visited(cls, url: str):
        md5 = MyUtil.md5(url)
        cls._set_url(md5, url)

        return bool(cls._get_visited(md5))

    @classmethod
    @print_info
    def changed(cls, url: str):
        md5 = MyUtil.md5(url)
        cls._set_url(md5, url)

        interval = cls._get_interval(md5)
        assert interval is not None
        interval = max(cls._min_interval, interval / 2)
        cls._visit(md5, interval)

    @classmethod
    @print_info
    def unchanged(cls, url: str):
        md5 = MyUtil.md5(url)
        cls._set_url(md5, url)

        interval = cls._get_interval(md5)
        assert interval is not None
        interval = min(cls._max_interval, interval * 2)
        cls._visit(md5, interval)

    @classmethod
    @print_info
    def first_time(cls, url: str):
        md5 = MyUtil.md5(url)
        cls._set_url(md5, url)

        interval = cls._default_interval
        assert interval is not None
        cls._visit(md5, interval)

    @classmethod
    @print_info
    def need_search(cls, url: str) -> bool:
        md5 = MyUtil.md5(url)
        cls._set_url(md5, url)

        ts = cls._get_next_time(md5)
        curr_ts = time.time()
        return ts is None or curr_ts >= ts

    @classmethod
    def get_all_urls(cls) -> List[str]:
        all_urls = cls._hvals("url")
        if all_urls is None:
            return []
        else:
            return all_urls

    @classmethod
    def flush_all(cls):
        cls._redis.flushall()


if __name__ == "__main__":
    print("begin")

    # host = "123.207.141.211"
    # pool = redis.ConnectionPool(host=host, port=18888,
    #                             decode_responses=True)  # host是redis主机，需要redis服务端和客户端都起着 redis默认端口是6379
    # r = redis.Redis(connection_pool=pool)
    # r.set('gender', 'male')  # key是"gender" value是"male" 将键值对存入redis缓存
    # print(r.get('gender'))  # gender 取出键male对应的值

    # r.hset("hash1", "a1", "aa")
    # print(type(r.hget("hash1", "a1")))
    # print(type(r.hget("hash1", "a2")))
    # print(Config.default_interval())

    # MyRedisUtil._set("hash1", "a3", "aa")
    # print(MyRedisUtil._get("hash1", "a3"))
    # MyRedisUtil.flush_all()
    # print(MyRedisUtil._get("hash1", "a3"))
    # print(MyRedisUtil._redis._hvals("md5_url"))
    MyRedisUtil.flush_all()

    print("end")
