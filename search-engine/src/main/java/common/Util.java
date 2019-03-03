package common;

import org.apache.commons.io.FileUtils;
import org.json.JSONObject;

import java.io.File;
import java.io.IOException;

public class Util {
    private static JSONObject jsonObject = null;
    private static String configPath = "src\\main\\resources\\config\\config.json";

    public static Object getConfig(String name) {
        if (jsonObject == null) {
            File file = new File(configPath);
            String content;
            try {
                content = FileUtils.readFileToString(file, "UTF-8");
            } catch (IOException e) {
                e.printStackTrace();
                content = "";
            }
            jsonObject = new JSONObject(content);
        }
        return jsonObject.get(name);
    }

    public static void main(String[] argv) throws IOException {
        System.out.println("document: " + getConfig("path.document"));
        System.out.println("index: " + getConfig("path.index"));
        double d = (double) getConfig("double");
        System.out.println("double: " + getConfig("double"));
        int i = (int) getConfig("int");
        System.out.println("int: " + i);
    }
}
