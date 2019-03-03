package common;

import org.apache.commons.io.FileUtils;
import org.json.JSONObject;

import java.io.File;
import java.io.IOException;

public class Util {
    private static JSONObject jsonObject1 = null;
    private static JSONObject jsonObject2 = null;
    private static String configPath = "src\\main\\resources\\config\\config.json";
    private static String secretConfigPath = "src\\main\\resources\\config\\secret-config.json";

    public static Object getConfig(String name) {
        if (jsonObject1 == null){
            try {
                String content;
                File file = new File(configPath);
                content = FileUtils.readFileToString(file, "UTF-8");
                jsonObject1 = new JSONObject(content);
                file = new File(secretConfigPath);
                content = FileUtils.readFileToString(file, "UTF-8");
                jsonObject2 = new JSONObject(content);
            } catch (IOException e) {
                e.printStackTrace();
                System.exit(1);
            }
        }
        try{
            return jsonObject1.get(name);
        }catch (org.json.JSONException e){
            return jsonObject2.get(name);
        }
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
