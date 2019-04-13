package retrieval;

import common.Util;

public class Main {
    public static void main(String[] args) {
        if (args.length != 2) {
            System.out.println("Arguments are not correct.");
            return;
        }
        String env = args[0];
        Util.setEnv(env);

        String job = args[1];
        switch (job) {
            case "index":
                Index.createIndex();
                break;
            case "server":
                System.out.println("Listening...");
                SearchServer.start();
                break;
            case "nothing":
                break;
            default:
                System.out.println("Arguments[1] is not correct.");
                break;
        }
    }
}
