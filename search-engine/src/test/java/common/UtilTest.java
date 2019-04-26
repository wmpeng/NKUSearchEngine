package common;

import junit.framework.TestCase;

public class UtilTest extends TestCase {

    /**
     * Should be same as config/prod/secret-config -> redis.host
     */
    public void testGetConfig() {
        Util.setEnv("prod");
        System.out.println(Util.getConfig("redis.host"));
    }

    public void testMd5() {
        Util.setEnv("prod");
        System.out.println(Util.md5((String)Util.getConfig("job.start_url")));
    }
}