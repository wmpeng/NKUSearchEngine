package retrieval;

import common.Util;
import org.apache.commons.io.FileUtils;
import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.document.Document;
import org.apache.lucene.document.Field;
import org.apache.lucene.document.StringField;
import org.apache.lucene.document.TextField;
import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;
import org.lionsoul.jcseg.analyzer.JcsegAnalyzer;
import org.lionsoul.jcseg.tokenizer.core.JcsegTaskConfig;
//import org.lionsoul.jcseg.core.JcsegTaskConfig;
import org.wltea.analyzer.lucene.IKAnalyzer;
import redis.RedisAccess;

import java.io.File;
import java.io.IOException;
import java.nio.file.FileSystems;
import java.util.ArrayList;
import java.util.List;

import static org.apache.lucene.index.IndexWriterConfig.OpenMode.CREATE_OR_APPEND;

public class Index {
    private static String docFolder = (String) Util.getConfig("path.document");
    private static String indexFolder = (String) Util.getConfig("path.index");

    protected static List<Document> readDocuments() throws IOException {
        List<Document> docs = new ArrayList<>();
        File folder = new File(docFolder);
        assert folder.isDirectory();

        File[] files = folder.listFiles();
        assert files != null;
        for (File file : files)
            if (file.isFile()) {
                try {
                    String md5 = file.getName().split("\\.")[0];
                    if (RedisAccess.needIndex(md5) && RedisAccess.needIndexSetFalse(md5)) {
                        String url = RedisAccess.getUrl(md5);
                        Field fieldUrl = new StringField("url", url, Field.Store.YES);
                        String content = FileUtils.readFileToString(file, "UTF-8");
                        Field fieldContent = new TextField("content", content, Field.Store.YES);
                        Field fieldTitle = new TextField("title", content.split("(\r\n)|(\n)")[0], Field.Store.YES);

                        Document doc = new Document();
                        doc.add(fieldUrl);
                        doc.add(fieldContent);
                        doc.add(fieldTitle);
                        docs.add(doc);
                    }
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }

        return docs;
    }

    private static void _createIndex() throws IOException {
        List<Document> docs = readDocuments();
        System.out.println("Built index for " + docs.size() + " documents.");

        Directory directory = FSDirectory.open(FileSystems.getDefault().getPath(indexFolder));
//        Analyzer analyzer = new StandardAnalyzer();
        Analyzer analyzer = new JcsegAnalyzer(JcsegTaskConfig.SIMPLE_MODE);
        //非必须(用于修改默认配置): 获取分词任务配置实例
        JcsegAnalyzer jcseg = (JcsegAnalyzer) analyzer;
        JcsegTaskConfig config = jcseg.getTaskConfig();
        //追加同义词到分词结果中, 需要在jcseg.properties中配置jcseg.loadsyn=1
        config.setAppendCJKSyn(true);
        //追加拼音到分词结果中, 需要在jcseg.properties中配置jcseg.loadpinyin=1
        config.setAppendCJKPinyin(true);

        IndexWriterConfig indexWriterConfig = new IndexWriterConfig(analyzer);
        indexWriterConfig.setOpenMode(IndexWriterConfig.OpenMode.CREATE_OR_APPEND);
        IndexWriter indexWriter = new IndexWriter(directory, indexWriterConfig);

        for (Document document : docs)
            indexWriter.addDocument(document);

        indexWriter.close();
        directory.close();
    }

    public static boolean createIndex() {
        try {
            _createIndex();
        } catch (IOException e) {
            e.printStackTrace();
            return false;
        }
        return true;
    }
}
