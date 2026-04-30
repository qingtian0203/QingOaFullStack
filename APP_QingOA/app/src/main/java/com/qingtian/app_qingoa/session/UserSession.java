package com.qingtian.app_qingoa.session;

import android.content.Context;
import android.content.SharedPreferences;

import com.google.gson.Gson;
import com.qingtian.app_qingoa.model.UserInfo;

/**
 * 用户会话管理器（单例）。
 * 负责 Token 和用户信息的持久化读写（SharedPreferences）。
 * 使用 Gson 序列化 UserInfo 对象存储为 JSON 字符串。
 */
public class UserSession {

    private static final String PREF_NAME = "qingoa_session";
    private static final String KEY_TOKEN = "token";
    private static final String KEY_USER_INFO = "user_info";

    private static volatile UserSession sInstance;

    private SharedPreferences mPrefs;
    private final Gson mGson = new Gson();

    // 内存缓存，避免频繁读磁盘
    private String mToken;
    private UserInfo mUserInfo;

    private UserSession() {}

    public static UserSession getInstance() {
        if (sInstance == null) {
            synchronized (UserSession.class) {
                if (sInstance == null) {
                    sInstance = new UserSession();
                }
            }
        }
        return sInstance;
    }

    /**
     * 必须在 Application.onCreate() 或 SplashActivity 初始化时调用一次。
     */
    public void init(Context context) {
        mPrefs = context.getApplicationContext()
                .getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
        // 从磁盘恢复内存缓存
        mToken = mPrefs.getString(KEY_TOKEN, null);
        String json = mPrefs.getString(KEY_USER_INFO, null);
        if (json != null) {
            mUserInfo = mGson.fromJson(json, UserInfo.class);
        }
    }

    /** 登录成功后保存 Token 和用户信息 */
    public void saveSession(String token, UserInfo userInfo) {
        mToken = token;
        mUserInfo = userInfo;
        mPrefs.edit()
                .putString(KEY_TOKEN, token)
                .putString(KEY_USER_INFO, mGson.toJson(userInfo))
                .apply();
    }

    /** 登出或 Token 过期时清除会话 */
    public void clearSession() {
        mToken = null;
        mUserInfo = null;
        mPrefs.edit().clear().apply();
    }

    public String getToken() { return mToken; }
    public UserInfo getUserInfo() { return mUserInfo; }
    public boolean isLoggedIn() { return mToken != null && !mToken.isEmpty(); }
}
