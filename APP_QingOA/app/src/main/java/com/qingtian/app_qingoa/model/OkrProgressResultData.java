package com.qingtian.app_qingoa.model;

import com.google.gson.annotations.SerializedName;

/** 更新 KR 进度成功后的 data 字段。 */
public class OkrProgressResultData {
    @SerializedName("kr_progress")
    private int krProgress;

    @SerializedName("okr_progress")
    private int okrProgress;

    public int getKrProgress() { return krProgress; }
    public int getOkrProgress() { return okrProgress; }
}
