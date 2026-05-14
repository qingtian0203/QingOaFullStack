package com.qingtian.app_qingoa.model;

import com.google.gson.annotations.SerializedName;

public class ImUser {
    @SerializedName("id")
    private int id;
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
    @SerializedName("is_friend")
    private boolean friend;

    public int getId() { return id != 0 ? id : userId; }
    public int getUserId() { return userId != 0 ? userId : id; }
    public String getUsername() { return username; }
    public String getName() { return name; }
    public String getDept() { return dept; }
    public String getRole() { return role; }
    public String getAvatarUrl() { return avatarUrl; }
    public boolean isFriend() { return friend; }

    public String displayName() {
        return name != null && !name.isEmpty() ? name : username;
    }

    public String initial() {
        String source = displayName();
        return source != null && !source.isEmpty() ? source.substring(0, 1) : "IM";
    }
}
