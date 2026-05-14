package com.qingtian.app_qingoa.ui.punch;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.google.android.material.button.MaterialButton;
import com.qingtian.app_qingoa.R;
import com.qingtian.app_qingoa.model.PunchAppealListData;

import java.util.List;

/** v1.6B 补卡申诉 / 待审批列表 Adapter。 */
public class PunchAppealAdapter extends RecyclerView.Adapter<PunchAppealAdapter.ViewHolder> {

    public interface OnReviewClickListener {
        void onReview(PunchAppealListData.PunchAppeal item, String action);
    }

    private final List<PunchAppealListData.PunchAppeal> mItems;
    private final boolean mReviewMode;
    private final OnReviewClickListener mListener;

    public PunchAppealAdapter(
            List<PunchAppealListData.PunchAppeal> items,
            boolean reviewMode,
            OnReviewClickListener listener
    ) {
        this.mItems = items;
        this.mReviewMode = reviewMode;
        this.mListener = listener;
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_punch_appeal, parent, false);
        return new ViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        PunchAppealListData.PunchAppeal item = mItems.get(position);
        holder.tvTitle.setText(item.getPunchDate() + " · " + item.getPunchTypeLabel());
        holder.tvStatus.setText(item.getStatusLabel());
        holder.tvApplicant.setText("申请人：" + safe(item.getApplicantName(), "我"));
        holder.tvReason.setText("原因：" + safe(item.getReason(), "未填写"));
        holder.tvExpectTime.setText("期望补卡：" + safe(item.getExpectTime(), "--:--:--"));
        String note = "";
        if (notEmpty(item.getManagerNote())) {
            note += "上级意见：" + item.getManagerNote();
        }
        if (notEmpty(item.getHrNote())) {
            note += (note.isEmpty() ? "" : "\n") + "HR 意见：" + item.getHrNote();
        }
        holder.tvNote.setVisibility(note.isEmpty() ? View.GONE : View.VISIBLE);
        holder.tvNote.setText(note);
        holder.tvUrged.setVisibility(item.isUrged() ? View.VISIBLE : View.GONE);

        boolean canReview = mReviewMode;
        holder.actionGroup.setVisibility(canReview ? View.VISIBLE : View.GONE);
        holder.btnApprove.setOnClickListener(v -> {
            if (mListener != null) mListener.onReview(item, "approve");
        });
        holder.btnReject.setOnClickListener(v -> {
            if (mListener != null) mListener.onReview(item, "reject");
        });
    }

    @Override
    public int getItemCount() {
        return mItems != null ? mItems.size() : 0;
    }

    static class ViewHolder extends RecyclerView.ViewHolder {
        TextView tvTitle;
        TextView tvStatus;
        TextView tvApplicant;
        TextView tvReason;
        TextView tvExpectTime;
        TextView tvNote;
        TextView tvUrged;
        View actionGroup;
        MaterialButton btnApprove;
        MaterialButton btnReject;

        ViewHolder(@NonNull View itemView) {
            super(itemView);
            tvTitle = itemView.findViewById(R.id.tv_title);
            tvStatus = itemView.findViewById(R.id.tv_status);
            tvApplicant = itemView.findViewById(R.id.tv_applicant);
            tvReason = itemView.findViewById(R.id.tv_reason);
            tvExpectTime = itemView.findViewById(R.id.tv_expect_time);
            tvNote = itemView.findViewById(R.id.tv_note);
            tvUrged = itemView.findViewById(R.id.tv_urged);
            actionGroup = itemView.findViewById(R.id.action_group);
            btnApprove = itemView.findViewById(R.id.btn_approve);
            btnReject = itemView.findViewById(R.id.btn_reject);
        }
    }

    private static String safe(String value, String fallback) {
        return notEmpty(value) ? value : fallback;
    }

    private static boolean notEmpty(String value) {
        return value != null && !value.trim().isEmpty();
    }
}
