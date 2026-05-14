package com.qingtian.app_qingoa.net;

import com.google.gson.annotations.SerializedName;

public class MarkReadRequest {
    @SerializedName("last_read_message_id")
    private final Integer lastReadMessageId;

    public MarkReadRequest(Integer lastReadMessageId) {
        this.lastReadMessageId = lastReadMessageId;
    }
}
