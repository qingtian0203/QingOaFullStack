package com.qingtian.app_qingoa.net;

import com.google.gson.annotations.SerializedName;

/** v1.5 打卡接口请求体，新增 punch_type 区分上班/下班卡 */
public class PunchRequest {

    @SerializedName("lat")
    private final double lat;

    @SerializedName("lng")
    private final double lng;

    @SerializedName("device_id")
    private final String deviceId;

    /** "clock_in" 或 "clock_out" */
    @SerializedName("punch_type")
    private final String punchType;

    public PunchRequest(double lat, double lng, String deviceId, String punchType) {
        this.lat = lat;
        this.lng = lng;
        this.deviceId = deviceId;
        this.punchType = punchType;
    }
}
