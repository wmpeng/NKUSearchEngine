package common;

import org.apache.commons.io.FileUtils;
import org.json.JSONObject;

import java.io.File;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

public class Util {
    private static Map<String, Object> jsonMap = null;
    private static String configPath = "src\\main\\resources\\config\\config.json";
    private static String localConfigPath = "src\\main\\resources\\config\\local-config.json";
    private static String secretConfigPath = "src\\main\\resources\\config\\secret-config.json";

    private static Map<String, Object> readJson(String path){
        String content;
        File file = new File(path);
        try {
            content = FileUtils.readFileToString(file, "UTF-8");
        } catch (IOException e) {
            content="";
        }
        JSONObject jsonObject = new JSONObject(content);
        return jsonObject.toMap();
    }

    public static Object getConfig(String name) {
        if (jsonMap == null){
            jsonMap = new HashMap<>();
            jsonMap.putAll(readJson(configPath));
            jsonMap.putAll(readJson(localConfigPath));
            jsonMap.putAll(readJson(secretConfigPath));
        }
        try{
            return jsonMap.get(name);
        }catch (org.json.JSONException e){
            return null;
        }
    }

    public static void main(String[] argv) throws IOException {
//        System.out.println("document: " + getConfig("path.document"));
//        System.out.println("index: " + getConfig("path.index"));
//        double d = (double) getConfig("double");
//        System.out.println("double: " + getConfig("double"));
//        int i = (int) getConfig("int");
//        System.out.println("int: " + i);
        getConfig("redis.port");
    }
}
