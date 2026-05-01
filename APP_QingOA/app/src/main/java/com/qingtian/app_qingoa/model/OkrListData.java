package com.qingtian.app_qingoa.model;

import com.google.gson.annotations.SerializedName;

import java.util.List;

/** OKR 列表接口 data 字段。 */
public class OkrListData {

    @SerializedName("list")
    private List<OkrItem> list;

    public List<OkrItem> getList() { return list; }

    public static class OkrItem {
        @SerializedName("id")
        private int id;

        @SerializedName("title")
        private String title;

        @SerializedName("description")
        private String description;

        @SerializedName("period")
        private String period;

        @SerializedName("status")
        private String status;

        @SerializedName("progress")
        private int progress;

        @SerializedName("kr_count")
        private int krCount;

        @SerializedName("updated_at")
        private String updatedAt;

        public int getId() { return id; }
        public String getTitle() { return title; }
        public String getDescription() { return description; }
        public String getPeriod() { return period; }
        public String getStatus() { return status; }
        public int getProgress() { return progress; }
        public int getKrCount() { return krCount; }
        public String getUpdatedAt() { return updatedAt; }
    }
}
