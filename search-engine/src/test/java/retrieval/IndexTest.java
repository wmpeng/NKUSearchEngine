package retrieval;

import common.Util;
import junit.framework.TestCase;

public class IndexTest extends TestCase {

    public void testCreateIndex() {
        Util.setEnv("dev");
        assert Index.createIndex();
    }
}