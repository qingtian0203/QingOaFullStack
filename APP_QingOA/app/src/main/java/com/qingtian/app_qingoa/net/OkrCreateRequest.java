package com.qingtian.app_qingoa.net;

import com.google.gson.annotations.SerializedName;

import java.util.List;

/** POST /api/okr/create 请求体。 */
public class OkrCreateRequest {
    private final String title;
    private final String description;
    private final String period;

    @SerializedName("key_results")
    private final List<KeyResultPayload> keyResults;

    public OkrCreateRequest(
            String title,
            String description,
            String period,
            List<KeyResultPayload> keyResults
    ) {
        this.title = title;
        this.description = description;
        this.period = period;
        this.keyResults = keyResults;
    }

    public static class KeyResultPayload {
        private final String title;

        @SerializedName("target_value")
        private final double targetValue;

        private final String unit;

        public KeyResultPayload(String title, double targetValue, String unit) {
            this.title = title;
            this.targetValue = targetValue;
            this.unit = unit;
        }
    }
}
