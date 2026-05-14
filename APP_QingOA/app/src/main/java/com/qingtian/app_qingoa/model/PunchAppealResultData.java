package com.qingtian.app_qingoa.model;

import com.google.gson.annotations.SerializedName;

/** v1.6B 提交补卡申诉返回数据。 */
public class PunchAppealResultData {
    @SerializedName("appeal_id")
    private int appealId;

    @SerializedName("status")
    private String status;

    public int getAppealId() { return appealId; }
    public String getStatus() { return status; }
}
