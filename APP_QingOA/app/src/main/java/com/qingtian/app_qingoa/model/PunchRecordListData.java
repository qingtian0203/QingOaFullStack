package com.qingtian.app_qingoa.model;

import com.google.gson.annotations.SerializedName;

import java.util.List;

/** v1.5 打卡记录列表接口返回的 data 字段，新增 punch_type / punch_date 字段 */
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

        /** "clock_in" 或 "clock_out" */
        @SerializedName("punch_type")
        private String punchType;

        /** 自然日 "2026-04-30" */
        @SerializedName("punch_date")
        private String punchDate;

        /** 完整时间 "2026-04-30 09:05:33"，用于列表展示和详情跳转 */
        @SerializedName("punch_time")
        private String punchTime;

        @SerializedName("point_name")
        private String pointName;

        @SerializedName("distance")
        private int distance;

        @SerializedName("status")
        private String status;

        public int getId() { return id; }
        public String getPunchType() { return punchType; }
        public String getPunchDate() { return punchDate; }
        public String getPunchTime() { return punchTime; }
        public String getPointName() { return pointName; }
        public int getDistance() { return distance; }
        public String getStatus() { return status; }

        /** 是否为上班卡 */
        public boolean isClockIn() { return "clock_in".equals(punchType); }

        /** 获取类型中文展示名 */
        public String getPunchTypeLabel() {
            return isClockIn() ? "上班打卡" : "下班打卡";
        }
    }
}
