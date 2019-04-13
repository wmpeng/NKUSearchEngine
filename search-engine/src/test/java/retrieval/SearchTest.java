package retrieval;

import common.Util;
import junit.framework.TestCase;
import org.apache.lucene.queryparser.classic.ParseException;
import org.apache.lucene.search.highlight.InvalidTokenOffsetsException;

import java.io.IOException;
import java.util.List;

public class SearchTest extends TestCase {

    public void test_query() throws ParseException, InvalidTokenOffsetsException, IOException {
        Util.setEnv("dev");
        List<List<String>> result = Search._query("南开大学");
        for (List<String> snippet : result) {
            for(String s: snippet)
                System.out.println(s);
            System.out.println();
        }
    }

    public void testQuery() {
        Util.setEnv("dev");
        List<List<String>> result = Search.query("南开大学");
        for (List<String> snippet : result) {
            for(String s: snippet)
                System.out.println(s);
            System.out.println();
        }
    }
}