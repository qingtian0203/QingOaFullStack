package com.qingtian.app_qingoa.net;

import com.google.gson.annotations.SerializedName;

/** 打卡接口请求体 */
public class PunchRequest {

    @SerializedName("lat")
    private final double lat;

    @SerializedName("lng")
    private final double lng;

    @SerializedName("device_id")
    private final String deviceId;

    public PunchRequest(double lat, double lng, String deviceId) {
        this.lat = lat;
        this.lng = lng;
        this.deviceId = deviceId;
    }
}
