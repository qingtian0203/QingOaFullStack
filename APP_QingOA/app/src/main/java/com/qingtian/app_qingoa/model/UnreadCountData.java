package com.qingtian.app_qingoa.model;

import com.google.gson.annotations.SerializedName;

/** 首页未读数接口返回的 data 字段。 */
public class UnreadCountData {

    @SerializedName("notice_unread")
    private int noticeUnread;

    public int getNoticeUnread() { return noticeUnread; }
}
