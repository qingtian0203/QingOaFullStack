package com.qingtian.app_qingoa.net;

import com.google.gson.annotations.SerializedName;

public class SingleConversationRequest {
    @SerializedName("peer_user_id")
    private final int peerUserId;

    public SingleConversationRequest(int peerUserId) {
        this.peerUserId = peerUserId;
    }
}
