package com.qingtian.app_qingoa.model;

import com.google.gson.annotations.SerializedName;

/** 打卡成功接口返回的 data 字段 */
public class PunchResultData {

    @SerializedName("punch_id")
    private int punchId;

    @SerializedName("punch_time")
    private String punchTime;

    @SerializedName("distance")
    private int distance;

    @SerializedName("point_name")
    private String pointName;

    public int getPunchId() { return punchId; }
    public String getPunchTime() { return punchTime; }
    public int getDistance() { return distance; }
    public String getPointName() { return pointName; }
}
