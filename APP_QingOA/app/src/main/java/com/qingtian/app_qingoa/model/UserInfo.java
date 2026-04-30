package com.qingtian.app_qingoa.model;

import com.google.gson.annotations.SerializedName;

/** 用户信息，登录成功和 user-info 接口共用 */
public class UserInfo {

    @SerializedName("user_id")
    int userId;

    @SerializedName("username")
    String username;

    @SerializedName("name")
    String name;

    @SerializedName("dept")
    String dept;

    @SerializedName("role")
    String role;

    @SerializedName("has_punch_permission")
    boolean hasPunchPermission;

    /** 无参构造器（Gson 反序列化 + LoginData.toUserInfo() 使用） */
    public UserInfo() {}

    public int getUserId() { return userId; }
    public String getUsername() { return username; }
    public String getName() { return name; }
    public String getDept() { return dept; }
    public String getRole() { return role; }
    public boolean hasPunchPermission() { return hasPunchPermission; }
}
