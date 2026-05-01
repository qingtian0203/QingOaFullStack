package com.qingtian.app_qingoa.ui.mine;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.qingtian.app_qingoa.R;
import com.qingtian.app_qingoa.model.MenuData;

import java.util.List;

/** 我的页动态入口列表，区别于首页九宫格。 */
public class MineMenuAdapter extends RecyclerView.Adapter<MineMenuAdapter.ViewHolder> {

    public interface OnMenuClickListener {
        void onMenuClick(MenuData.MenuItem item);
    }

    private final List<MenuData.MenuItem> mItems;
    private final OnMenuClickListener mListener;

    public MineMenuAdapter(List<MenuData.MenuItem> items, OnMenuClickListener listener) {
        this.mItems = items;
        this.mListener = listener;
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

        float alpha = item.isEnabled() ? 1.0f : 0.45f;
        holder.itemView.setAlpha(alpha);
        holder.ivArrow.setVisibility(item.isEnabled() ? View.VISIBLE : View.GONE);
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
        return "进入功能";
    }

    static class ViewHolder extends RecyclerView.ViewHolder {
        ImageView ivArrow;
        TextView tvName;
        TextView tvHint;

        ViewHolder(@NonNull View itemView) {
            super(itemView);
            tvName = itemView.findViewById(R.id.tv_name);
            tvHint = itemView.findViewById(R.id.tv_hint);
            ivArrow = itemView.findViewById(R.id.iv_arrow);
        }
    }
}
