package retrieval;

import common.Util;
import junit.framework.TestCase;

import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.PrintWriter;
import java.net.Socket;
import java.util.List;

public class SearchServerTest extends TestCase {

    /**
     * Run SearchServer.main firstly.
     */
    public void testStart() throws IOException, ClassNotFoundException {
        Util.setEnv("dev");

        int port = (int) Util.getConfig("search_server.port");
        String host = (String) Util.getConfig("search_server.host");
        Socket socket = new Socket(host, port);
        System.out.println("new Socket.");

        PrintWriter serverWriter=new PrintWriter(socket.getOutputStream());
        serverWriter.println("总书记");
        serverWriter.flush();
        System.out.println("Sent to server.");

        ObjectInputStream serverReceiver = new ObjectInputStream(socket.getInputStream());
        List<List<String>> result= (List<List<String>>) serverReceiver.readObject();
        System.out.println("Receive from server.");
        for (List<String> snippet : result) {
            for(String s: snippet)
                System.out.println(s);
            System.out.println();
        }

        serverReceiver.close();
        serverWriter.close();
        socket.close();
    }
}