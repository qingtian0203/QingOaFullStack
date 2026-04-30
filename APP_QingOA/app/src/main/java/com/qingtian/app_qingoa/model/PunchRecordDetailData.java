package com.qingtian.app_qingoa.model;

import com.google.gson.annotations.SerializedName;

/** 打卡详情接口返回的 data 字段（GET /api/punch/records/{id}） */
public class PunchRecordDetailData {

    @SerializedName("id")
    private int id;

    @SerializedName("punch_type")
    private String punchType;

    @SerializedName("punch_date")
    private String punchDate;

    @SerializedName("punch_time")
    private String punchTime;

    @SerializedName("point_name")
    private String pointName;

    @SerializedName("lat")
    private double lat;

    @SerializedName("lng")
    private double lng;

    @SerializedName("distance")
    private int distance;

    @SerializedName("device_id")
    private String deviceId;

    public int getId() { return id; }
    public String getPunchType() { return punchType; }
    public String getPunchDate() { return punchDate; }
    public String getPunchTime() { return punchTime; }
    public String getPointName() { return pointName; }
    public double getLat() { return lat; }
    public double getLng() { return lng; }
    public int getDistance() { return distance; }
    public String getDeviceId() { return deviceId; }

    public boolean isClockIn() { return "clock_in".equals(punchType); }
    public String getPunchTypeLabel() { return isClockIn() ? "上班打卡" : "下班打卡"; }
}
