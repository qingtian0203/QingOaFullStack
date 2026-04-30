package com.qingtian.app_qingoa.net;

import com.google.gson.annotations.SerializedName;

/** 登录接口请求体 */
public class LoginRequest {

    @SerializedName("username")
    private final String username;

    @SerializedName("password")
    private final String password;

    public LoginRequest(String username, String password) {
        this.username = username;
        this.password = password;
    }
}
