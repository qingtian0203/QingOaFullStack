package com.qingtian.app_qingoa.model;

import com.google.gson.annotations.SerializedName;

import java.util.List;

public class ImConversationListData {
    @SerializedName("list")
    private List<Conversation> list;

    public List<Conversation> getList() { return list; }

    public static class Conversation {
        @SerializedName("id")
        private int id;
        @SerializedName("peer")
        private ImUser peer;
        @SerializedName("last_message")
        private ImMessageListData.Message lastMessage;
        @SerializedName("unread_count")
        private int unreadCount;
        @SerializedName("updated_at")
        private String updatedAt;

        public int getId() { return id; }
        public ImUser getPeer() { return peer; }
        public ImMessageListData.Message getLastMessage() { return lastMessage; }
        public int getUnreadCount() { return unreadCount; }
        public String getUpdatedAt() { return updatedAt; }
    }
}
