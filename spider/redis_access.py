import queue
from typing import Union, List, Set, Optional

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
    def _set(cls, name: str, key: str, val: str, prefix: bool = True):
        if prefix:
            cls._redis.hset(cls._start_md5 + "_" + name, key, val)
        else:
            cls._redis.hset(name, key, val)

    @classmethod
    def _get(cls, name: str, key: str, prefix: bool = True) -> str:
        if prefix:
            return cls._redis.hget(cls._start_md5 + "_" + name, key)
        else:
            return cls._redis.hget(name, key)

    @classmethod
    def _del(cls, name: str):
        cls._redis.delete(cls._start_md5 + "_" + name)

    @classmethod
    def _hvals(cls, name: str) -> List[str]:
        return cls._redis.hvals(cls._start_md5 + "_" + name)

    @classmethod
    def _push_list(cls, name, val: List[str]):
        cls._redis.rpush(cls._start_md5 + "_" + name, *val)

    @classmethod
    def _get_list(cls, name) -> List[str]:
        return cls._redis.lrange(cls._start_md5 + "_" + name, 0, -1)

    @classmethod
    def _pop_list(cls, name) -> str:
        return cls._redis.lpop(cls._start_md5 + "_" + name)

    @classmethod
    def _push_set(cls, name: str, val: str):
        cls._redis.sadd(cls._start_md5 + "_" + name, val)

    @classmethod
    def _pop_set(cls, name: str) -> str:
        ret = cls._redis.spop(cls._start_md5 + "_" + name)
        return ret

    @classmethod
    def _check_set(cls, name: str, val: str) -> bool:
        return cls._redis.sismember(cls._start_md5 + "_" + name, val)

    @classmethod
    def _set_number(cls, name) -> int:
        return cls._redis.scard(cls._start_md5 + "_" + name)

    @classmethod
    def _set_url(cls, md5: str, url: str):
        cls._set("url", md5, url)
        cls._set("url", md5, url, False)

    @classmethod
    def _get_url(cls, md5: str) -> str:
        return cls._get("url", md5)

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
        assert val is not None
        return float(val)

    @classmethod
    def _set_exception(cls, md5: str, prefix: str, exception_info: str):
        cls._set(prefix + "exception", md5, exception_info)

    @classmethod
    def _visit(cls, md5: str, interval: float):
        ts = time.time()
        cls._set_visited(md5, ts)
        cls._set_interval(md5, interval)
        cls._set_next_time(md5, ts + interval)

    @classmethod
    # @print_info
    def is_visited(cls, url: str):
        md5 = MyUtil.md5(url)
        cls._set_url(md5, url)

        return bool(cls._get_visited(md5))

    @classmethod
    # @print_info
    def changed(cls, url: str):
        md5 = MyUtil.md5(url)
        cls._set_url(md5, url)

        interval = cls._get_interval(md5)
        interval = max(cls._min_interval, interval / 2)
        cls._visit(md5, interval)

    @classmethod
    # @print_info
    def unchanged(cls, url: str):
        md5 = MyUtil.md5(url)
        cls._set_url(md5, url)

        interval = cls._get_interval(md5)
        interval = min(cls._max_interval, interval * 2)
        cls._visit(md5, interval)

    @classmethod
    # @print_info
    def first_time(cls, url: str):
        md5 = MyUtil.md5(url)
        cls._set_url(md5, url)

        interval = cls._default_interval
        cls._visit(md5, interval)

    @classmethod
    def exceptional(cls, url: str):
        if cls.is_visited(url):
            cls.unchanged(url)
        else:
            cls.first_time(url)

    @classmethod
    # @print_info
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
    def set_known_exception(cls, url: str, error: BaseException):
        md5 = MyUtil.md5(url)
        cls._set_url(md5, url)

        cls._set_exception(md5, "known", str(type(error)) + "  " + str(error))

    @classmethod
    def set_unknown_exception(cls, url: str, error: BaseException):
        md5 = MyUtil.md5(url)
        cls._set_url(md5, url)

        cls._set_exception(md5, "unknown", str(type(error)) + "  " + str(error))

    @classmethod
    def flush_all(cls):
        cls._redis.flushall()

    @classmethod
    def flush(cls):
        cls._del("url")
        cls._del("visited")
        cls._del("interval")
        cls._del("next_time")
        # cls._del("snap_visited")
        # cls._del("snap_queue")
        cls._del("store_need_search")
        cls._del("store_visited")

    @classmethod
    def store_visited(cls, val: Set[str]):
        cls._del("snap_visited")
        if len(val) != 0:
            cls._push_list("snap_visited", list(val))

    @classmethod
    def get_visited(cls) -> Set[str]:
        return set(cls._get_list("snap_visited"))

    @classmethod
    def store_queue(cls, q: queue.Queue):
        val = list(q.queue)
        cls._del("snap_queue")
        if len(val) != 0:
            cls._push_list("snap_queue", val)

    @classmethod
    def get_queue(cls) -> queue.Queue:
        val = cls._get_list("snap_queue")
        q = queue.Queue()
        q.queue = queue.deque(val)
        return q

    @classmethod
    def stored_breakpoint(cls) -> bool:
        return bool(cls.get_visited() and cls.get_queue())

    @classmethod
    def push_need_search(cls, url) -> None:
        md5 = MyUtil.md5(url)
        cls._set_url(md5, url)

        cls._push_set("store_need_search", md5)

    @classmethod
    def pop_need_search(cls) -> Optional[str]:
        md5 = cls._pop_set("store_need_search")
        if md5 is None:
            return None
        url = cls._get_url(md5)
        return url

    @classmethod
    def need_search_num(cls) -> int:
        return cls._set_number("store_need_search")

    @classmethod
    def set_visited(cls, url: str) -> None:
        md5 = MyUtil.md5(url)
        cls._set_url(md5, url)

        cls._push_set("store_visited", md5)

    @classmethod
    def check_visited(cls, url: str) -> bool:
        md5 = MyUtil.md5(url)
        cls._set_url(md5, url)

        return cls._check_set("store_visited", md5)

    @classmethod
    def visited_num(cls) -> int:
        return cls._set_number("store_visited")


if __name__ == "__main__":
    print("begin")

    # host = "123.207.141.211"
    # pool = redis.ConnectionPool(host=host, port=18888,
    #                             decode_responses=True)  # host是redis主机，需要redis服务端和客户端都起着 redis默认端口是6379
    # r = redis.Redis(connection_pool=pool)
    # r.rpush("list1", *["1", "2", "3", "4", "5"])
    # print(r.lindex("list1", 0))
    # print(list(r.lrange("list1", 0, -1)))
    #
    # r.delete("list1")

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

    # MyRedisUtil.store_list("list1", ["aa", "bb", "c"])
    # MyRedisUtil.get_list("list1")

    # MyRedisUtil.flush_all()
    # MyRedisUtil.push_need_search("a1")
    # MyRedisUtil.push_need_search("a2")
    # MyRedisUtil.push_need_search("a3")

    url_ = MyRedisUtil.pop_need_search()
    print(url_)
    MyRedisUtil.set_visited(url_)

    print(MyRedisUtil.check_visited("a1"))
    print(MyRedisUtil.check_visited("a2"))
    print(MyRedisUtil.check_visited("a3"))

    print("end")
