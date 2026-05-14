package com.qingtian.app_qingoa.net;

import com.google.gson.annotations.SerializedName;

public class SendImMessageRequest {
    @SerializedName("message_type")
    private final String messageType;
    @SerializedName("content")
    private final String content;
    @SerializedName("file_id")
    private final String fileId;

    public static SendImMessageRequest text(String content) {
        return new SendImMessageRequest("text", content, null);
    }

    public static SendImMessageRequest image(String fileId) {
        return new SendImMessageRequest("image", null, fileId);
    }

    private SendImMessageRequest(String messageType, String content, String fileId) {
        this.messageType = messageType;
        this.content = content;
        this.fileId = fileId;
    }
}
