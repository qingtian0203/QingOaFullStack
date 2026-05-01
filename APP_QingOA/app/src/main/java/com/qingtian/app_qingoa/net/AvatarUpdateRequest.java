package com.qingtian.app_qingoa.net;

import com.google.gson.annotations.SerializedName;

/** v1.6A：头像 URL 更新请求体。 */
public class AvatarUpdateRequest {

    @SerializedName("avatar_url")
    private final String avatarUrl;

    public AvatarUpdateRequest(String avatarUrl) {
        this.avatarUrl = avatarUrl;
    }
}
