package redis;

import common.Util;
import junit.framework.TestCase;

public class RedisAccessTest extends TestCase {

    /**
     * It should be "http://example.url" if redis.host is "no_host"
     */
    public void testGetUrl() {
        Util.setEnv("dev");
        System.out.println(RedisAccess.getUrl("ab"));
    }
}