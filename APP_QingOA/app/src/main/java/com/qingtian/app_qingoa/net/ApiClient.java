package com.qingtian.app_qingoa.net;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Log;

import com.qingtian.app_qingoa.BuildConfig;
import com.qingtian.app_qingoa.session.UserSession;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.logging.HttpLoggingInterceptor;
import retrofit2.Retrofit;
import retrofit2.converter.gson.GsonConverterFactory;

/**
 * 网络客户端单例。
 * 职责：
 * 1. 统一注入 Authorization: Bearer {token} Header
 * 2. 打印请求/响应日志（仅 Debug 模式）
 * 3. 提供全局唯一 ApiService 实例
 */
public class ApiClient {

    private static final String TAG = "ApiClient";
    private static final String PREF_NAME = "qingoa_api_environment";
    private static final String KEY_ENVIRONMENT = "environment";
    public static final String ENV_LOCAL = "local";
    public static final String ENV_REMOTE = "remote";
    private static final String LOCAL_BASE_URL = "http://127.0.0.1:8010/";
    private static final String REMOTE_BASE_URL = "https://oa.qingagent.top/";

    /**
     * 调试地址切换：
     *   模拟器本地  → http://10.0.2.2:8010/
     *   真机局域网  → http://192.168.x.x:8010/
     *   外网远程    → https://oa.qingagent.top/
     */
    private static SharedPreferences sPrefs;
    private static volatile ApiService sInstance;

    private ApiClient() {}

    public static synchronized void init(Context context) {
        if (sPrefs == null) {
            sPrefs = context.getApplicationContext()
                    .getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
        }
    }

    public static ApiService getService() {
        if (sInstance == null) {
            synchronized (ApiClient.class) {
                if (sInstance == null) {
                    sInstance = buildService();
                }
            }
        }
        return sInstance;
    }

    public static String getEnvironment() {
        if (!BuildConfig.DEBUG) {
            return ENV_REMOTE;
        }
        if (sPrefs == null) {
            return ENV_LOCAL;
        }
        return sPrefs.getString(KEY_ENVIRONMENT, ENV_LOCAL);
    }

    public static String getBaseUrl() {
        return ENV_REMOTE.equals(getEnvironment()) ? REMOTE_BASE_URL : LOCAL_BASE_URL;
    }

    public static synchronized boolean setEnvironment(String environment) {
        String normalized = ENV_REMOTE.equals(environment) ? ENV_REMOTE : ENV_LOCAL;
        if (!BuildConfig.DEBUG) {
            normalized = ENV_REMOTE;
        }
        String old = getEnvironment();
        if (sPrefs != null) {
            sPrefs.edit().putString(KEY_ENVIRONMENT, normalized).apply();
        }
        reset();
        return !old.equals(normalized);
    }

    public static String resolveResourceUrl(String path) {
        if (path == null || path.trim().isEmpty()) {
            return "";
        }
        String value = path.trim();
        if (value.startsWith("http://") || value.startsWith("https://")) {
            return value;
        }
        String base = getBaseUrl();
        base = base.endsWith("/") ? base : base + "/";
        if (value.startsWith("/")) {
            return base + value.substring(1);
        }
        return base + value;
    }

    private static ApiService buildService() {
        // 日志拦截器（记录完整请求 / 响应，便于调试）
        HttpLoggingInterceptor logging = new HttpLoggingInterceptor(
                message -> Log.d(TAG, message)
        );
        // 仅 Debug 包开启 BODY 日志，避免 Bearer Token 明文打印到 Logcat
        logging.setLevel(BuildConfig.DEBUG
                ? HttpLoggingInterceptor.Level.BODY
                : HttpLoggingInterceptor.Level.NONE);
        logging.redactHeader("Authorization");

        OkHttpClient client = new OkHttpClient.Builder()
                // Token 注入拦截器：每次请求自动带上 Authorization Header
                .addInterceptor(chain -> {
                    Request original = chain.request();
                    String token = UserSession.getInstance().getToken();
                    if (token != null && !token.isEmpty()) {
                        Request newReq = original.newBuilder()
                                .header("Authorization", "Bearer " + token)
                                .build();
                        return chain.proceed(newReq);
                    }
                    return chain.proceed(original);
                })
                .addInterceptor(logging)
                .build();

        return new Retrofit.Builder()
                .baseUrl(getBaseUrl())
                .client(client)
                .addConverterFactory(GsonConverterFactory.create())
                .build()
                .create(ApiService.class);
    }

    /**
     * 重置单例（测试时或切换服务器地址时调用）。
     */
    public static synchronized void reset() {
        sInstance = null;
    }
}
