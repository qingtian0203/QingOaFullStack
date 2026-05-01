package com.qingtian.app_qingoa.model;

import com.google.gson.annotations.SerializedName;

import java.util.List;

/** OKR 详情接口 data 字段。 */
public class OkrDetailData {

    @SerializedName("id")
    private int id;

    @SerializedName("title")
    private String title;

    @SerializedName("description")
    private String description;

    @SerializedName("period")
    private String period;

    @SerializedName("status")
    private String status;

    @SerializedName("progress")
    private int progress;

    @SerializedName("key_results")
    private List<KeyResult> keyResults;

    public int getId() { return id; }
    public String getTitle() { return title; }
    public String getDescription() { return description; }
    public String getPeriod() { return period; }
    public String getStatus() { return status; }
    public int getProgress() { return progress; }
    public List<KeyResult> getKeyResults() { return keyResults; }

    public static class KeyResult {
        @SerializedName("id")
        private int id;

        @SerializedName("title")
        private String title;

        @SerializedName("target_value")
        private double targetValue;

        @SerializedName("current_value")
        private double currentValue;

        @SerializedName("unit")
        private String unit;

        @SerializedName("progress")
        private int progress;

        public int getId() { return id; }
        public String getTitle() { return title; }
        public double getTargetValue() { return targetValue; }
        public double getCurrentValue() { return currentValue; }
        public String getUnit() { return unit; }
        public int getProgress() { return progress; }
    }
}
