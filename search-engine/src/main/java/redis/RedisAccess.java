package redis;

import common.Util;
import redis.clients.jedis.Jedis;

public class RedisAccess {
    public static String getUrl(String md5) {
        Jedis jedis = new Jedis((String) Util.getConfig("redis.host"), (int) Util.getConfig("redis.port"));
        String val = jedis.hget("url", md5);
        jedis.close();
        return val;
    }

    public static void main(String[] args) {
        System.out.println(getUrl("ab"));
    }
}
