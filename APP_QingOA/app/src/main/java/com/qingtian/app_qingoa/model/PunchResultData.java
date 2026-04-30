package com.qingtian.app_qingoa.model;

import com.google.gson.annotations.SerializedName;

/** v1.5 打卡接口返回的 data 字段，支持上班/下班卡 */
public class PunchResultData {

    @SerializedName("punch_id")
    private int punchId;

    /** 完整日期时间，如 "2026-04-30 09:05:33"，用于记录/详情/调试 */
    @SerializedName("punch_time")
    private String punchTime;

    @SerializedName("distance")
    private int distance;

    @SerializedName("point_name")
    private String pointName;

    /** true 表示下班卡刷新（加班场景），false 表示首次打卡 */
    @SerializedName("updated")
    private boolean updated;

    public int getPunchId() { return punchId; }
    public String getPunchTime() { return punchTime; }
    public int getDistance() { return distance; }
    public String getPointName() { return pointName; }
    public boolean isUpdated() { return updated; }
}
