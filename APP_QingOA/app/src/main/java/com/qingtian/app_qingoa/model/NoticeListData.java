package com.qingtian.app_qingoa.model;

import com.google.gson.annotations.SerializedName;

import java.util.List;

/** 通知公告列表接口返回的 data 字段 */
public class NoticeListData {

    @SerializedName("total")
    private int total;

    @SerializedName("page")
    private int page;

    @SerializedName("size")
    private int size;

    @SerializedName("list")
    private List<NoticeItem> list;

    public int getTotal() { return total; }
    public List<NoticeItem> getList() { return list; }

    /** 单条公告 */
    public static class NoticeItem {

        @SerializedName("id")
        private int id;

        @SerializedName("title")
        private String title;

        @SerializedName("summary")
        private String summary;

        @SerializedName("created_at")
        private String createdAt;

        /** v1 全部返回 false，不实现已读逻辑 */
        @SerializedName("is_read")
        private boolean read;

        public int getId() { return id; }
        public String getTitle() { return title; }
        public String getSummary() { return summary; }
        public String getCreatedAt() { return createdAt; }
        public boolean isRead() { return read; }
    }
}
