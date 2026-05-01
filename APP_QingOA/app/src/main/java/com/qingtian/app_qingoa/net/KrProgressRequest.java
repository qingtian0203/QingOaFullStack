package com.qingtian.app_qingoa.net;

import com.google.gson.annotations.SerializedName;

/** PUT /api/okr/{id}/key-results/{krId} 请求体。 */
public class KrProgressRequest {
    @SerializedName("current_value")
    private final double currentValue;

    public KrProgressRequest(double currentValue) {
        this.currentValue = currentValue;
    }
}
