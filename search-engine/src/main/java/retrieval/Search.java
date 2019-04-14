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
import org.lionsoul.jcseg.analyzer.JcsegAnalyzer;
import org.lionsoul.jcseg.tokenizer.core.JcsegTaskConfig;

import java.io.IOException;
import java.io.StringReader;
import java.nio.file.FileSystems;
import java.util.ArrayList;
import java.util.List;

public class Search {
    private static String indexFolder = (String) Util.getConfig("path.index");

    public static List<List<String>> _query(String queryStr) throws ParseException, IOException, InvalidTokenOffsetsException {
        List<List<String>> result = new ArrayList<>();

//        Analyzer analyzer = new StandardAnalyzer();

        Analyzer analyzer = new JcsegAnalyzer(JcsegTaskConfig.SIMPLE_MODE);
        //非必须(用于修改默认配置): 获取分词任务配置实例
        JcsegAnalyzer jcseg = (JcsegAnalyzer) analyzer;
        JcsegTaskConfig config = jcseg.getTaskConfig();
        //追加同义词到分词结果中, 需要在jcseg.properties中配置jcseg.loadsyn=1
        config.setAppendCJKSyn(true);
        //追加拼音到分词结果中, 需要在jcseg.properties中配置jcseg.loadpinyin=1
        config.setAppendCJKPinyin(true);

        Query query = new QueryParser("content", analyzer).parse(queryStr);
        Directory directory = FSDirectory.open(FileSystems.getDefault().getPath(indexFolder));
        IndexReader reader = DirectoryReader.open(directory);
        IndexSearcher indexSearcher = new IndexSearcher(reader);
        TopDocs topDocs = indexSearcher.search(query, (int) Util.getConfig("search.top_k"));
        ScoreDoc[] scoreDocs = topDocs.scoreDocs;

        SimpleHTMLFormatter simpleHTMLFormatter = new SimpleHTMLFormatter("<font color='red'>", "</font>");
        Highlighter highlighter = new Highlighter(simpleHTMLFormatter, new QueryScorer(query));
        highlighter.setTextFragmenter(new SimpleFragmenter((int) Util.getConfig("search.snippet_length")));

        for (ScoreDoc scoreDoc : scoreDocs) {
            int docID = scoreDoc.doc;
            Document doc = indexSearcher.doc(docID);
            String text = doc.get("content").replace("\r\n", " ");
            TokenStream tokenStream = analyzer.tokenStream("content", new StringReader(text));
            String highLightText = highlighter.getBestFragment(tokenStream, text);

            List<String> item = new ArrayList<>();
            item.add(doc.get("url"));
            item.add(doc.get("title"));
            item.add(highLightText);
            result.add(item);
        }

        return result;
    }

    public static List<List<String>> query(String queryStr){
        List<List<String>> queryRes;
        try{
            queryRes = _query(queryStr);
        } catch (ParseException e) {
            e.printStackTrace();
            queryRes = new ArrayList<>();
        } catch (IOException e) {
            e.printStackTrace();
            queryRes = new ArrayList<>();
        } catch (InvalidTokenOffsetsException e) {
            e.printStackTrace();
            queryRes = new ArrayList<>();
        } catch (Exception e){
            e.printStackTrace();
            queryRes = new ArrayList<>();
        }

        return queryRes;
    }
}
