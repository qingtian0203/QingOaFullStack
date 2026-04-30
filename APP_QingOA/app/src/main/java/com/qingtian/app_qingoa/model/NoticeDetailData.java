package com.qingtian.app_qingoa.model;

import com.google.gson.annotations.SerializedName;

/** 通知详情接口返回的 data 字段（GET /api/notices/{id}） */
public class NoticeDetailData {

    @SerializedName("id")
    private int id;

    @SerializedName("title")
    private String title;

    /** 通知全文 */
    @SerializedName("content")
    private String content;

    @SerializedName("created_at")
    private String createdAt;

    public int getId() { return id; }
    public String getTitle() { return title; }
    public String getContent() { return content; }
    public String getCreatedAt() { return createdAt; }
}
