import time
from typing import Union, List, Optional

import redis

from mytool import Config, MyUtil


# service redis stop
class MyRedisAccessor:
    _host = Config.get("redis.host")
    _port = Config.get("redis.port")
    _pool = redis.ConnectionPool(host=_host, port=_port, decode_responses=True)
    _redis = redis.Redis(connection_pool=_pool)
    _start_md5 = MyUtil.md5(MyUtil.normalize_url(Config.get("job.start_url")))

    @classmethod
    def flush_all(cls):
        cls._redis.flushall()

    @classmethod
    def delete(cls, name: str):
        cls._redis.delete(cls._start_md5 + "_" + name)

    @classmethod
    def hash_set(cls, name: str, key: str, val: str, prefix: bool = True):
        if prefix:
            cls._redis.hset(cls._start_md5 + "_" + name, key, val)
        else:
            cls._redis.hset(name, key, val)

    @classmethod
    def hash_get(cls, name: str, key: str) -> str:
        # if prefix:
        #     return cls._redis.hget(cls._start_md5 + "_" + name, key)
        # else:
        #     return cls._redis.hget(name, key)
        return cls._redis.hget(name, key)

    @classmethod
    def hash_get_vals(cls, name: str) -> List[str]:
        return cls._redis.hvals(cls._start_md5 + "_" + name)

    @classmethod
    def list_push(cls, name, val: List[str]):
        cls._redis.rpush(cls._start_md5 + "_" + name, *val)

    @classmethod
    def list_get_vals(cls, name) -> List[str]:
        return cls._redis.lrange(cls._start_md5 + "_" + name, 0, -1)

    # @classmethod
    # def _pop_list(cls, name) -> str:
    #     return cls._redis.lpop(cls._start_md5 + "_" + name)

    @classmethod
    def set_push(cls, name: str, val: str):
        cls._redis.sadd(cls._start_md5 + "_" + name, val)

    @classmethod
    def set_pop(cls, name: str) -> str:
        ret = cls._redis.spop(cls._start_md5 + "_" + name)
        return ret

    @classmethod
    def set_check(cls, name: str, val: str) -> bool:
        return cls._redis.sismember(cls._start_md5 + "_" + name, val)

    @classmethod
    def set_size(cls, name) -> int:
        return cls._redis.scard(cls._start_md5 + "_" + name)


class MyRedisUtil:
    _default_interval = float(Config.get("job.default_interval"))
    _min_interval = float(Config.get("job.min_interval"))
    _max_interval = float(Config.get("job.max_interval"))
    accessor = MyRedisAccessor()

    @classmethod
    def set_url(cls, md5: str, url: str):
        cls.accessor.hash_set("url", md5, url)
        cls.accessor.hash_set("url", md5, url, False)

    @classmethod
    def get_url(cls, md5: str) -> str:
        return cls.accessor.hash_get("url", md5)

    @classmethod
    def get_all_urls(cls) -> List[str]:
        all_urls = cls.accessor.hash_get_vals("url")
        if all_urls is None:
            return []
        else:
            return all_urls

    @classmethod
    def set_last_time(cls, md5: str, timestamp: float):
        cls.accessor.hash_set("last_time", md5, str(timestamp))

    @classmethod
    def get_last_time(cls, md5: str) -> Union[float, None]:
        val = cls.accessor.hash_get("last_time", md5)
        if val is None:
            return val
        else:
            return float(val)

    # @classmethod
    # def get_all_visit_times(cls):
    #     all_visit_times = cls.accessor.hash_get_vals("visited")
    #     if all_visit_times is None:
    #         return []
    #     else:
    #         return all_visit_times

    @classmethod
    def set_next_time(cls, md5: str, ts: float):
        cls.accessor.hash_set("next_time", md5, str(ts))

    @classmethod
    def get_next_time(cls, md5: str) -> Union[float, None]:
        val = cls.accessor.hash_get("next_time", md5)
        if val is None:
            return val
        else:
            return float(val)

    @classmethod
    def set_interval(cls, md5: str, interval: float):
        cls.accessor.hash_set("interval", md5, str(interval))

    @classmethod
    def get_interval(cls, md5: str) -> Union[float, None]:
        val = cls.accessor.hash_get("interval", md5)
        assert val is not None
        return float(val)

    @classmethod
    def add_exception(cls, md5: str, prefix: str, exception_info: str):
        cls.accessor.hash_set(prefix + "_exception", md5, exception_info)

    @classmethod
    def set_visit_info(cls, md5: str, interval: float):
        ts = time.time()
        cls.set_last_time(md5, ts)
        cls.set_interval(md5, interval)
        cls.set_next_time(md5, ts + interval)

    @classmethod
    def have_visited(cls, url: str):
        """return if have ever visited. Attention: not only in current batch."""
        md5 = MyUtil.md5(url)
        cls.set_url(md5, url)

        return bool(cls.get_last_time(md5))

    @classmethod
    def changed_visit(cls, url: str):
        md5 = MyUtil.md5(url)
        cls.set_url(md5, url)

        interval = cls.get_interval(md5)
        interval = max(cls._min_interval, interval / 2)
        cls.set_visit_info(md5, interval)

    @classmethod
    def unchanged_visit(cls, url: str):
        md5 = MyUtil.md5(url)
        cls.set_url(md5, url)

        interval = cls.get_interval(md5)
        interval = min(cls._max_interval, interval * 2)
        cls.set_visit_info(md5, interval)

    @classmethod
    def first_time_visit(cls, url: str):
        md5 = MyUtil.md5(url)
        cls.set_url(md5, url)

        interval = cls._default_interval
        cls.set_visit_info(md5, interval)

    @classmethod
    def exceptional_visit(cls, url: str):
        if cls.have_visited(url):
            cls.unchanged_visit(url)
        else:
            cls.first_time_visit(url)

    @classmethod
    def need_search(cls, url: str) -> bool:
        md5 = MyUtil.md5(url)
        cls.set_url(md5, url)

        ts = cls.get_next_time(md5)
        curr_ts = time.time()
        return ts is None or curr_ts >= ts

    @classmethod
    def set_known_exception(cls, url: str, error: BaseException):
        md5 = MyUtil.md5(url)
        cls.set_url(md5, url)

        cls.add_exception(md5, "known", str(type(error)) + "  " + str(error))

    @classmethod
    def set_unknown_exception(cls, url: str, error: BaseException):
        md5 = MyUtil.md5(url)
        cls.set_url(md5, url)

        cls.add_exception(md5, "unknown", str(type(error)) + "  " + str(error))

    @classmethod
    def flush(cls):
        cls.accessor.delete("url")
        cls.accessor.delete("last_time")
        cls.accessor.delete("interval")
        cls.accessor.delete("next_time")
        # cls._del("snap_visited")
        # cls._del("snap_queue")
        cls.accessor.delete("need_search")
        cls.accessor.delete("visited")

    # @classmethod
    # def store_visited(cls, val: Set[str]):
    #     cls.accessor.delete("snap_visited")
    #   fl) != 0:
    #         cls.accessor.list_push("snap_visited", list(val))

    # @classmethod
    # def get_visited(cls) -> Set[str]:
    #     return set(cls.accessor.list_get_vals("snap_visited"))
    # @classmethod
    # def get_visited(cls) -> Set[str]:
    #     return set(cls.accessor.list_get_vals("snap_visited"))

    # @classmethod
    # def store_queue(cls, q: queue.Queue):
    #     val = list(q.queue)
    #     cls.accessor.delete("snap_queue")
    #     if len(val) != 0:
    #         cls.accessor.list_push("snap_queue", val)

    # @classmethod
    # def get_queue(cls) -> queue.Queue:
    #     val = cls.accessor.list_get_vals("snap_queue")
    #     q = queue.Queue()
    #     q.queue = queue.deque(val)
    #     return q

    # @classmethod
    # def stored_breakpoint(cls) -> bool:
    #     return bool(cls.get_visited() and cls.get_queue())

    @classmethod
    def push_need_search(cls, url) -> None:
        md5 = MyUtil.md5(url)
        cls.set_url(md5, url)

        cls.accessor.set_push("need_search", md5)

    @classmethod
    def pop_need_search(cls) -> Optional[str]:
        md5 = cls.accessor.set_pop("need_search")
        if md5 is None:
            return None
        url = cls.get_url(md5)
        return url

    @classmethod
    def need_search_num(cls) -> int:
        return cls.accessor.set_size("need_search")

    @classmethod
    def push_visited(cls, url: str) -> None:
        md5 = MyUtil.md5(url)
        cls.set_url(md5, url)

        cls.accessor.set_push("visited", md5)

    @classmethod
    def check_visited(cls, url: str) -> bool:
        md5 = MyUtil.md5(url)
        cls.set_url(md5, url)

        return cls.accessor.set_check("visited", md5)

    @classmethod
    def visited_num(cls) -> int:
        return cls.accessor.set_size("visited")


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

    # MyRedisUtil.hash_set("hash1", "a3", "aa")
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

    # url_ = MyRedisUtil.pop_need_search()
    # print(url_)
    # MyRedisUtil.push_visited(url_)
    #
    # print(MyRedisUtil.check_visited("a1"))
    # print(MyRedisUtil.check_visited("a2"))
    # print(MyRedisUtil.check_visited("a3"))
    #
    # print("end")
