package com.qingtian.app_qingoa.ui.mine;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.qingtian.app_qingoa.R;
import com.qingtian.app_qingoa.model.BadgeSummaryData;
import com.qingtian.app_qingoa.model.MenuData;

import java.util.List;

/** 我的页动态入口列表，区别于首页九宫格。 */
public class MineMenuAdapter extends RecyclerView.Adapter<MineMenuAdapter.ViewHolder> {

    public interface OnMenuClickListener {
        void onMenuClick(MenuData.MenuItem item);
    }

    private final List<MenuData.MenuItem> mItems;
    private final OnMenuClickListener mListener;
    private BadgeSummaryData mBadgeSummary;

    public MineMenuAdapter(List<MenuData.MenuItem> items, OnMenuClickListener listener) {
        this.mItems = items;
        this.mListener = listener;
    }

    public void setBadgeSummary(BadgeSummaryData badgeSummary) {
        mBadgeSummary = badgeSummary;
        notifyDataSetChanged();
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_mine_menu, parent, false);
        return new ViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        MenuData.MenuItem item = mItems.get(position);
        holder.tvName.setText(item.getName());
        holder.tvHint.setText(item.isEnabled()
                ? hintForTarget(item.getTarget())
                : item.getDisabledReason() != null ? item.getDisabledReason() : "功能开发中");
        int badgeCount = badgeCountForTarget(item.getTarget());
        holder.tvBadge.setVisibility(item.isEnabled() && badgeCount > 0 ? View.VISIBLE : View.GONE);
        holder.tvBadge.setText(formatBadgeCount(badgeCount));

        float alpha = item.isEnabled() ? 1.0f : 0.45f;
        holder.itemView.setAlpha(alpha);
        holder.ivArrow.setVisibility(item.isEnabled() ? View.VISIBLE : View.GONE);
        holder.itemView.setContentDescription(menuContentDescription(item));
        holder.itemView.setOnClickListener(v -> {
            if (mListener != null) {
                mListener.onMenuClick(item);
            }
        });
    }

    @Override
    public int getItemCount() {
        return mItems != null ? mItems.size() : 0;
    }

    private String hintForTarget(String target) {
        if ("PunchRecordListActivity".equals(target)) {
            return "查看上班、下班和更新记录";
        }
        if ("WorkflowWebActivity".equals(target)) {
            BadgeSummaryData.Workflow workflow = mBadgeSummary != null ? mBadgeSummary.getWorkflow() : null;
            if (workflow != null && workflow.getActionableTotal() > 0) {
                return "待办 " + workflow.getTodo() + " · 催办 " + workflow.getUrged() + " · 退回 " + workflow.getReturned();
            }
            return "打开待办、催办和流程详情";
        }
        if ("PunchAppealActivity".equals(target)) {
            return "提交补卡说明并进入审批";
        }
        if ("PunchAppealReviewActivity".equals(target)) {
            int count = mBadgeSummary != null ? mBadgeSummary.punchAppealReviewCount() : 0;
            if (count > 0) {
                return "待处理 " + count + " 条补卡申诉";
            }
            return "处理直属上级或 HR 待办";
        }
        return "进入功能";
    }

    private int badgeCountForTarget(String target) {
        if (mBadgeSummary == null) {
            return 0;
        }
        if ("WorkflowWebActivity".equals(target)) {
            return mBadgeSummary.workflowActionableTotal();
        }
        if ("PunchAppealReviewActivity".equals(target)) {
            return mBadgeSummary.punchAppealReviewCount();
        }
        return 0;
    }

    private String formatBadgeCount(int count) {
        return count > 99 ? "99+" : String.valueOf(count);
    }

    private String menuContentDescription(MenuData.MenuItem item) {
        String target = item.getTarget();
        if ("PunchRecordListActivity".equals(target)) {
            return "qingoa_mine_punch_records_entry";
        }
        if ("WorkflowWebActivity".equals(target)) {
            return "qingoa_mine_workflow_entry";
        }
        if ("PunchAppealActivity".equals(target)) {
            return "qingoa_mine_punch_appeal_entry";
        }
        if ("PunchAppealReviewActivity".equals(target)) {
            return "qingoa_mine_punch_appeal_review_entry";
        }
        String name = item.getName() != null ? item.getName() : "menu";
        return "qingoa_mine_menu_" + name + (item.isEnabled() ? "_enabled" : "_disabled");
    }

    static class ViewHolder extends RecyclerView.ViewHolder {
        ImageView ivArrow;
        TextView tvName;
        TextView tvHint;
        TextView tvBadge;

        ViewHolder(@NonNull View itemView) {
            super(itemView);
            tvName = itemView.findViewById(R.id.tv_name);
            tvHint = itemView.findViewById(R.id.tv_hint);
            tvBadge = itemView.findViewById(R.id.tv_badge);
            ivArrow = itemView.findViewById(R.id.iv_arrow);
        }
    }
}
