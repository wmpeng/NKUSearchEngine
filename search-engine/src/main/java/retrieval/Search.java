package retrieval;

import common.Util;
import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.TokenStream;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.document.Document;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.queryparser.classic.ParseException;
import org.apache.lucene.queryparser.classic.QueryParser;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.Query;
import org.apache.lucene.search.ScoreDoc;
import org.apache.lucene.search.TopDocs;
import org.apache.lucene.search.highlight.*;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;

import java.io.IOException;
import java.io.StringReader;
import java.nio.file.FileSystems;
import java.util.ArrayList;
import java.util.List;

public class Search {
    private static String indexFolder = (String) Util.getConfig("path.index");

    public static List<String> Query(String queryStr) throws ParseException, IOException, InvalidTokenOffsetsException {
        List<String> result = new ArrayList<>();

        Analyzer analyzer = new StandardAnalyzer();
        Query query = new QueryParser("content", analyzer).parse(queryStr);
        Directory directory = FSDirectory.open(FileSystems.getDefault().getPath(indexFolder));
        IndexReader reader = DirectoryReader.open(directory);
        IndexSearcher indexSearcher = new IndexSearcher(reader);
        TopDocs topDocs = indexSearcher.search(query, (int) Util.getConfig("search.top_k"));
        ScoreDoc[] scoreDocs = topDocs.scoreDocs;
        System.out.println(topDocs.totalHits);

        SimpleHTMLFormatter simpleHTMLFormatter = new SimpleHTMLFormatter("<font color='red'>", "</font>");
        Highlighter highlighter = new Highlighter(simpleHTMLFormatter, new QueryScorer(query));
        highlighter.setTextFragmenter(new SimpleFragmenter((int) Util.getConfig("search.fragment_size")));

        for (ScoreDoc scoreDoc : scoreDocs) {
            int docID = scoreDoc.doc;
            Document doc = indexSearcher.doc(docID);
            String text = doc.get("content").replace("\r\n", " ");
            TokenStream tokenStream = analyzer.tokenStream("content", new StringReader(text));
            String highLightText = highlighter.getBestFragment(tokenStream, text);

            result.add(highLightText);
        }

        return result;
    }

    public static void main(String[] args) throws IOException, ParseException, InvalidTokenOffsetsException {
        List<String> result = Query("南开大学");
        for (String snippet : result)
            System.out.println(snippet);
    }
}
