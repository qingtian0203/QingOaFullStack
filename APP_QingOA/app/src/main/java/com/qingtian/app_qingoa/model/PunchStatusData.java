package com.qingtian.app_qingoa.model;

import com.google.gson.annotations.SerializedName;

import java.util.List;

/** 今日打卡状态接口返回的 data 字段 */
public class PunchStatusData {

    @SerializedName("has_punched")
    private boolean hasPunched;

    @SerializedName("punch_time")
    private String punchTime;

    @SerializedName("punch_points")
    private List<PunchPoint> punchPoints;

    public boolean hasPunched() { return hasPunched; }
    public String getPunchTime() { return punchTime; }
    public List<PunchPoint> getPunchPoints() { return punchPoints; }

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
