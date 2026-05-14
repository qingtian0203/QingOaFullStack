package com.qingtian.app_qingoa.net;

import com.google.gson.annotations.SerializedName;

/** v1.6B 补卡申诉审批请求。 */
public class PunchAppealReviewRequest {
    @SerializedName("action")
    private final String action;

    @SerializedName("note")
    private final String note;

    public PunchAppealReviewRequest(String action, String note) {
        this.action = action;
        this.note = note;
    }
}
