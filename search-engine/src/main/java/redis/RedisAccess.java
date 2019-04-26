package redis;

import common.Util;
import redis.clients.jedis.Jedis;

import java.util.stream.StreamSupport;

public class RedisAccess {
    private static String getHashVal(String name,String key) {
        if (((String) Util.getConfig("redis.host")).equals("no_host"))
            return "http://example.url";
        Jedis jedis = new Jedis((String) Util.getConfig("redis.host"), (int) Util.getConfig("redis.port"));
        String val = null;
        for (int i = 0; i <= 3; i++) {
            try {
                val = jedis.hget(name, key);
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

    private static Boolean isSetMember(String name, String key) {
        if (((String) Util.getConfig("redis.host")).equals("no_host"))
            return true;
        Jedis jedis = new Jedis((String) Util.getConfig("redis.host"), (int) Util.getConfig("redis.port"));
        Boolean val = null;
        for (int i = 0; i <= 3; i++) {
            try {
                val = jedis.sismember(name, key);
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

    private static boolean setRemove(String name, String key) {
        if (((String) Util.getConfig("redis.host")).equals("no_host"))
            return true;
        Jedis jedis = new Jedis((String) Util.getConfig("redis.host"), (int) Util.getConfig("redis.port"));
        Boolean val = null;
        for (int i = 0; i <= 3; i++) {
            try {
                System.out.println(key);
                Long tmp = jedis.srem(name, key);
                val = true;
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

    public static String getUrl(String md5) {
        String val = getHashVal("url", md5);
        return val;
    }

    public static Boolean needIndex(String md5) {
        System.out.println("! "+Util.md5((String)Util.getConfig("job.start_url"))+"_need_index");
        Boolean val = isSetMember(Util.md5((String)Util.getConfig("job.start_url"))+"_need_index", md5);
        return val;
    }

    public static Boolean needIndexSetFalse(String md5) {
        Boolean val = setRemove(Util.md5((String)Util.getConfig("job.start_url"))+"_need_index", md5);
        return val;
    }
}
