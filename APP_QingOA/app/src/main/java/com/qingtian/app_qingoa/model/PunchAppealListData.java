package com.qingtian.app_qingoa.model;

import com.google.gson.annotations.SerializedName;

import java.util.List;

/** v1.6B 补卡申诉列表/待审批列表返回数据。 */
public class PunchAppealListData {

    @SerializedName("list")
    private List<PunchAppeal> list;

    public List<PunchAppeal> getList() { return list; }

    public static class PunchAppeal {
        @SerializedName("id")
        private int id;

        @SerializedName("applicant_name")
        private String applicantName;

        @SerializedName("punch_date")
        private String punchDate;

        @SerializedName("punch_type")
        private String punchType;

        @SerializedName("punch_type_label")
        private String punchTypeLabel;

        @SerializedName("reason")
        private String reason;

        @SerializedName("expect_time")
        private String expectTime;

        @SerializedName("status")
        private String status;

        @SerializedName("status_label")
        private String statusLabel;

        @SerializedName("manager_note")
        private String managerNote;

        @SerializedName("hr_note")
        private String hrNote;

        @SerializedName("process_instance_id")
        private int processInstanceId;

        @SerializedName("node_key")
        private String nodeKey;

        @SerializedName("urged")
        private boolean urged;

        @SerializedName("created_at")
        private String createdAt;

        public int getId() { return id; }
        public String getApplicantName() { return applicantName; }
        public String getPunchDate() { return punchDate; }
        public String getPunchType() { return punchType; }
        public String getPunchTypeLabel() {
            if (punchTypeLabel != null && !punchTypeLabel.isEmpty()) return punchTypeLabel;
            return "clock_in".equals(punchType) ? "上班卡" : "下班卡";
        }
        public String getReason() { return reason; }
        public String getExpectTime() { return expectTime; }
        public String getStatus() { return status; }
        public String getStatusLabel() {
            return statusLabel != null && !statusLabel.isEmpty() ? statusLabel : status;
        }
        public String getManagerNote() { return managerNote; }
        public String getHrNote() { return hrNote; }
        public int getProcessInstanceId() { return processInstanceId; }
        public String getNodeKey() { return nodeKey; }
        public boolean isUrged() { return urged; }
        public String getCreatedAt() { return createdAt; }
    }
}
