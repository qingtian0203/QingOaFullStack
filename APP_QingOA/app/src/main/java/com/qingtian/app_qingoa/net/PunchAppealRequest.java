package com.qingtian.app_qingoa.net;

import com.google.gson.annotations.SerializedName;

/** v1.6B 补卡申诉请求。 */
public class PunchAppealRequest {
    @SerializedName("punch_date")
    private final String punchDate;

    @SerializedName("punch_type")
    private final String punchType;

    @SerializedName("reason")
    private final String reason;

    @SerializedName("expect_time")
    private final String expectTime;

    public PunchAppealRequest(String punchDate, String punchType, String reason, String expectTime) {
        this.punchDate = punchDate;
        this.punchType = punchType;
        this.reason = reason;
        this.expectTime = expectTime;
    }
}
