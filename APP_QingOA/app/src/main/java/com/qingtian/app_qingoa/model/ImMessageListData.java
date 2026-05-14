package com.qingtian.app_qingoa.model;

import com.google.gson.annotations.SerializedName;

import java.util.List;

public class ImMessageListData {
    @SerializedName("list")
    private List<Message> list;

    public List<Message> getList() { return list; }

    public static class Message {
        @SerializedName("id")
        private int id;
        @SerializedName("sender_id")
        private int senderId;
        @SerializedName("message_type")
        private String messageType;
        @SerializedName("content")
        private String content;
        @SerializedName("file_id")
        private String fileId;
        @SerializedName("file")
        private FileUploadData file;
        @SerializedName("summary")
        private String summary;
        @SerializedName("created_at")
        private String createdAt;

        public int getId() { return id; }
        public int getSenderId() { return senderId; }
        public String getMessageType() { return messageType; }
        public String getContent() { return content; }
        public String getFileId() { return fileId; }
        public FileUploadData getFile() { return file; }
        public String getSummary() { return summary; }
        public String getCreatedAt() { return createdAt; }
        public boolean isImage() { return "image".equals(messageType); }
    }
}
