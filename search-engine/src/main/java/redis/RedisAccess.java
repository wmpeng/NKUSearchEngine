package redis;

import common.Util;
import redis.clients.jedis.Jedis;

public class RedisAccess {
    public static String getUrl(String md5) {
        if (((String) Util.getConfig("redis.host")).equals("no_host"))
            return "http://example.url";
        Jedis jedis = new Jedis((String) Util.getConfig("redis.host"), (int) Util.getConfig("redis.port"));
        String val = null;
        for (int i = 0; i <= 3; i++) {
            try {
                val = jedis.hget("url", md5);
                break;
            } catch (Exception e) {
                try{
                    Thread.sleep(10);
                } catch (InterruptedException e1) {
                    e1.printStackTrace();
                }
                if (i == 3)
                    throw e;
            }
        }
        jedis.close();
        return val;
    }
}
