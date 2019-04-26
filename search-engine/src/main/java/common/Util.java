package common;

import org.apache.commons.io.IOUtils;
import org.json.JSONObject;

import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.security.MessageDigest;
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
            content = new String(IOUtils.toByteArray(input));
        } catch (Exception e) {
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

    public static String md5(String url) {
        try {
            MessageDigest md = MessageDigest.getInstance("MD5");
            // 计算md5函数
            md.update(url.getBytes());
            // digest()最后确定返回md5 hash值，返回值为8为字符串。因为md5 hash值是16位的hex值，实际上就是8位的字符
            // BigInteger函数则将8位的字符串转换成16位hex值，用字符串来表示；得到字符串形式的hash值
            return new BigInteger(1, md.digest()).toString(16);
        }catch (Exception ignored) {
            return "";
        }
    }
}
