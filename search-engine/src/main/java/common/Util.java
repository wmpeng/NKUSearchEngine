package common;

import org.json.JSONObject;

import java.io.IOException;
import java.io.InputStream;
import java.util.HashMap;
import java.util.Map;

public class Util {
    private static Map<String, Object> jsonMap = null;
    private static String configPathBase = "/config/%s/config.json";
    private static String localConfigPathBase = "/config/%s/local-config.json";
    private static String secretConfigPathBase = "/config/%s/secret-config.json";
    private static String configPath = null;
    private static String localConfigPath = null;
    private static String secretConfigPath = null;

    public static void setEnv(String env) {
        configPath = String.format(configPathBase, env);
        localConfigPath = String.format(localConfigPathBase, env);
        secretConfigPath = String.format(secretConfigPathBase, env);
    }

    private static Map<String, Object> readJson(String path) {
        String content;
        InputStream input = Util.class.getResourceAsStream(path);
        assert input != null : "Config path is not exist.";

        try {
            content = new String(input.readAllBytes());
        } catch (IOException e) {
            content = "";
        }
        JSONObject jsonObject = new JSONObject(content);
        return jsonObject.toMap();
    }

    public static Object getConfig(String name) {
        if (jsonMap == null) {
            jsonMap = new HashMap<>();
            assert configPath != null : "Haven't set environment.";
            jsonMap.putAll(readJson(configPath));
            jsonMap.putAll(readJson(localConfigPath));
            jsonMap.putAll(readJson(secretConfigPath));
        }
        try {
            return jsonMap.get(name);
        } catch (org.json.JSONException e) {
            return null;
        }
    }
}
