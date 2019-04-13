package retrieval;

import common.Util;
import org.apache.lucene.queryparser.classic.ParseException;
import org.apache.lucene.search.highlight.InvalidTokenOffsetsException;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.ObjectOutputStream;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.ArrayList;
import java.util.List;

public class SearchServer {
    public static int start() {
        int port = (int) Util.getConfig("search_server.port");
        ServerSocket server = null;
        try {
            server = new ServerSocket(port);
            while (true) {
                Socket socket;
                socket = server.accept();
                BufferedReader clientReader = new BufferedReader(new InputStreamReader(socket.getInputStream(),"UTF-8"));
                String queryStr = clientReader.readLine();
                System.out.println("QueryStr: " + queryStr);

                List<List<String>> queryRes;
                queryRes = Search.query(queryStr);

                ObjectOutputStream clientSender = new ObjectOutputStream(socket.getOutputStream());
                clientSender.writeObject(queryRes);
                clientSender.flush();

                clientSender.close();
                clientReader.close();
            }

        } catch (IOException e) {
            e.printStackTrace();
            return -1;
        } finally {
            if (server != null)
                try {
                    server.close();
                } catch (IOException e) {
                    e.printStackTrace();
                }
        }
    }

    public static void main(String[] args) {
        Util.setEnv("dev");
        System.out.println("Listening...");
        start();
    }
}
