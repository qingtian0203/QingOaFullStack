package com.qingtian.app_qingoa.model;

import com.google.gson.annotations.SerializedName;

/** 登录接口的 data 字段（包含 token + 用户信息） */
public class LoginData {

    @SerializedName("token")
    private String token;

    @SerializedName("user_id")
    private int userId;

    @SerializedName("username")
    private String username;

    @SerializedName("name")
    private String name;

    @SerializedName("dept")
    private String dept;

    @SerializedName("role")
    private String role;

    @SerializedName("avatar_url")
    private String avatarUrl;

    @SerializedName("has_punch_permission")
    private boolean hasPunchPermission;

    public String getToken() { return token; }
    public int getUserId() { return userId; }
    public String getUsername() { return username; }
    public String getName() { return name; }
    public String getDept() { return dept; }
    public String getRole() { return role; }
    public String getAvatarUrl() { return avatarUrl; }
    public boolean hasPunchPermission() { return hasPunchPermission; }

    /** 转换为通用 UserInfo（用于写入 UserSession） */
    public UserInfo toUserInfo() {
        // Gson 反序列化时字段已映射，直接用 Gson 构建 UserInfo 等价结构
        // 这里手动构建以避免额外依赖
        UserInfo info = new UserInfo();
        info.userId = userId;
        info.username = username;
        info.name = name;
        info.dept = dept;
        info.role = role;
        info.avatarUrl = avatarUrl;
        info.hasPunchPermission = hasPunchPermission;
        return info;
    }
}
