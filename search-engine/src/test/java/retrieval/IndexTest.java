package retrieval;

import common.Util;
import junit.framework.TestCase;

import java.util.Arrays;

public class IndexTest extends TestCase {

    public void testCreateIndex() {
        Util.setEnv("dev");
        assert Index.createIndex();
    }

    public void testNewline() {
        String s1 = "abc\ndef";
        System.out.println(Arrays.toString(s1.split("(\r\n)|(\n)")));
        System.out.println(s1.split("(\r\n)|(\n)").length);
        System.out.println(s1);
        String s2 = "abc\ndef";
        System.out.println(Arrays.toString(s2.split("(\r\n)|(\n)")));
        System.out.println(s2.split("(\r\n)|(\n)").length);
        System.out.println(s2);
    }
}