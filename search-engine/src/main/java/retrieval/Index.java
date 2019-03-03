package retrieval;

import common.Util;
import org.apache.commons.io.FileUtils;
import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.document.Document;
import org.apache.lucene.document.Field;
import org.apache.lucene.document.TextField;
import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;

import java.io.File;
import java.io.IOException;
import java.nio.file.FileSystems;
import java.util.ArrayList;
import java.util.List;

import static org.apache.lucene.index.IndexWriterConfig.OpenMode.CREATE_OR_APPEND;

public class Index {
    private static String docFolder = (String) Util.getConfig("path.document");
    private static String indexFolder = (String) Util.getConfig("path.index");

    private List<Document> readDocuments() throws IOException {
        List<Document> docs = new ArrayList<>();
        File folder = new File(docFolder);
        assert folder.isDirectory();

        File[] files = folder.listFiles();
        assert files != null;
        for (File file : files)
            if (file.isFile()) {
                String content = FileUtils.readFileToString(file, "UTF-8");
                Field fieldContent = new TextField("content", content, Field.Store.YES);

                Document doc = new Document();
                doc.add(fieldContent);
                docs.add(doc);
            }

        return docs;
    }

    private void createIndex() throws IOException {
        List<Document> docs = readDocuments();

        Directory directory = FSDirectory.open(FileSystems.getDefault().getPath(indexFolder));
        Analyzer standardAnalyzer = new StandardAnalyzer();
        IndexWriterConfig indexWriterConfig = new IndexWriterConfig(standardAnalyzer);
        indexWriterConfig.setOpenMode(IndexWriterConfig.OpenMode.CREATE);
        IndexWriter indexWriter = new IndexWriter(directory, indexWriterConfig);

        for (Document document : docs)
            indexWriter.addDocument(document);

        indexWriter.close();
        directory.close();
    }

    public static void main(String[] args) throws IOException {
        Index index = new Index();
        index.createIndex();
    }
}
