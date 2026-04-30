package com.qingtian.app_qingoa.model;

import com.google.gson.annotations.SerializedName;

import java.util.List;

/** v1.5 今日打卡状态接口返回的 data 字段，区分上班/下班卡 */
public class PunchStatusData {

    /** 上班卡状态 */
    @SerializedName("clock_in")
    private PunchInfo clockIn;

    /** 下班卡状态 */
    @SerializedName("clock_out")
    private PunchInfo clockOut;

    @SerializedName("punch_points")
    private List<PunchPoint> punchPoints;

    public PunchInfo getClockIn() { return clockIn; }
    public PunchInfo getClockOut() { return clockOut; }
    public List<PunchPoint> getPunchPoints() { return punchPoints; }

    /** 单类型卡的状态（done + time） */
    public static class PunchInfo {

        @SerializedName("done")
        private boolean done;

        /** 仅时间字符串 "09:05:33"，用于 UI 展示 */
        @SerializedName("time")
        private String time;

        public boolean isDone() { return done; }
        public String getTime() { return time; }
    }

    /** 打卡点信息 */
    public static class PunchPoint {

        @SerializedName("id")
        private int id;

        @SerializedName("name")
        private String name;

        @SerializedName("lat")
        private double lat;

        @SerializedName("lng")
        private double lng;

        @SerializedName("radius")
        private int radius;

        public int getId() { return id; }
        public String getName() { return name; }
        public double getLat() { return lat; }
        public double getLng() { return lng; }
        public int getRadius() { return radius; }
    }
}
