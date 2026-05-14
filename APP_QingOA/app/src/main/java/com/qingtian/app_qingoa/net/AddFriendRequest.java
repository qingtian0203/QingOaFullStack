package com.qingtian.app_qingoa.net;

import com.google.gson.annotations.SerializedName;

public class AddFriendRequest {
    @SerializedName("friend_user_id")
    private final int friendUserId;

    public AddFriendRequest(int friendUserId) {
        this.friendUserId = friendUserId;
    }
}
