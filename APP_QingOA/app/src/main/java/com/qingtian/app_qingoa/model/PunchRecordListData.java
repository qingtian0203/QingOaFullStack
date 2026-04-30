package com.qingtian.app_qingoa.model;

import com.google.gson.annotations.SerializedName;

import java.util.List;

/** 打卡记录列表接口返回的 data 字段 */
public class PunchRecordListData {

    @SerializedName("total")
    private int total;

    @SerializedName("list")
    private List<PunchRecord> list;

    public int getTotal() { return total; }
    public List<PunchRecord> getList() { return list; }

    /** 单条打卡记录 */
    public static class PunchRecord {

        @SerializedName("id")
        private int id;

        @SerializedName("punch_time")
        private String punchTime;

        @SerializedName("point_name")
        private String pointName;

        @SerializedName("distance")
        private int distance;

        @SerializedName("status")
        private String status;

        public int getId() { return id; }
        public String getPunchTime() { return punchTime; }
        public String getPointName() { return pointName; }
        public int getDistance() { return distance; }
        public String getStatus() { return status; }
    }
}
