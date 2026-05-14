package com.qingtian.app_qingoa.model;

import com.google.gson.annotations.SerializedName;

public class BadgeSummaryData {
    @SerializedName("im")
    private Im im;
    @SerializedName("workflow")
    private Workflow workflow;
    @SerializedName("mine")
    private Mine mine;

    public Im getIm() { return im; }
    public Workflow getWorkflow() { return workflow; }
    public Mine getMine() { return mine; }

    public int imUnreadTotal() {
        return im != null ? im.getUnreadTotal() : 0;
    }

    public int workflowActionableTotal() {
        return workflow != null ? workflow.getActionableTotal() : 0;
    }

    public int punchAppealReviewCount() {
        return mine != null ? mine.getPunchAppealReview() : 0;
    }

    public static class Im {
        @SerializedName("unread_total")
        private int unreadTotal;

        public int getUnreadTotal() { return unreadTotal; }
    }

    public static class Workflow {
        @SerializedName("todo")
        private int todo;
        @SerializedName("urged")
        private int urged;
        @SerializedName("processing")
        private int processing;
        @SerializedName("returned")
        private int returned;
        @SerializedName("actionable_total")
        private int actionableTotal;

        public int getTodo() { return todo; }
        public int getUrged() { return urged; }
        public int getProcessing() { return processing; }
        public int getReturned() { return returned; }
        public int getActionableTotal() { return actionableTotal; }
    }

    public static class Mine {
        @SerializedName("punch_appeal_review")
        private int punchAppealReview;

        public int getPunchAppealReview() { return punchAppealReview; }
    }
}
