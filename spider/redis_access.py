import redis
import time

from mytool import Config


class MyRedisUtil:
    host = Config.get("redis.host")
    port = int(Config.get("redis.port"))
    pool = redis.ConnectionPool(host=host, port=port, decode_responses=True)
    r = redis.Redis(connection_pool=pool)
    default_interval = float(Config.get("redis.default_interval"))

    @classmethod
    def _set(cls, name: str, key: str, value: str):
        cls.r.hset(name, key, value)

    @classmethod
    def _get(cls, name: str, key: str) -> str:
        return cls.r.hget(name, key)

    @classmethod
    def _set_url(cls, md5: str, url: str):
        cls._set("md5_url", md5, url)

    @classmethod
    def _get_url(cls, md5: str):
        cls._get("md5_url", md5)

    @classmethod
    def _set_visited(cls, md5: str, ts: float):
        cls._set("visited", md5, str(ts))

    @classmethod
    def _set_next_time(cls, md5: str, ts: float):
        cls._set("next_time", md5, str(ts))

    @classmethod
    def _get_next_time(cls, md5: str) -> float:
        return float(cls._get("next_time", md5))

    @classmethod
    def _set_interval(cls, md5: str, interval: float):
        cls._set("interval", md5, str(interval))

    @classmethod
    def _get_interval(cls, md5: str) -> float:
        return float(cls._get("interval", md5))

    @classmethod
    def _visit(cls, md5: str, interval: float):
        ts = time.time()
        cls._set_visited(md5, ts)
        cls._set_interval(md5, interval)
        cls._set_next_time(md5, ts + interval)

    @classmethod
    def changed(cls, md5: str):
        interval = cls._get_interval(md5)
        assert interval is not None
        interval /= 2
        cls._visit(md5, interval)

    @classmethod
    def unchanged(cls, md5):
        interval = cls._get_interval(md5)
        assert interval is not None
        interval *= 2
        cls._visit(md5, interval)

    @classmethod
    def first_time(cls, md5: str):
        interval = cls.default_interval
        cls._visit(md5, interval)

    @classmethod
    def need_search(cls, md5: str) -> bool:
        ts = cls._get_next_time(md5)
        curr_ts = time.time()
        return ts is None or curr_ts >= ts


if __name__ == "__main__":
    print("begin")

    # host = "123.207.141.211"
    # pool = redis.ConnectionPool(host=host, port=6379,
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

    print("end")
