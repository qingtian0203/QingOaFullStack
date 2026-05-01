package com.qingtian.app_qingoa.model;

import com.google.gson.annotations.SerializedName;

/** 创建 OKR 成功后的 data 字段。 */
public class OkrCreateResultData {
    @SerializedName("id")
    private int id;

    public int getId() { return id; }
}
