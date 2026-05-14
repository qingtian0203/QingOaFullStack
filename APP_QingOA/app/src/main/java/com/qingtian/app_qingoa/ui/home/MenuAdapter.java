package com.qingtian.app_qingoa.ui.home;

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

/**
 * 九宫格菜单 Adapter。
 * enabled=false 的菜单项灰显，点击弹 disabled_reason Toast。
 */
public class MenuAdapter extends RecyclerView.Adapter<MenuAdapter.ViewHolder> {

    public interface OnMenuClickListener {
        void onMenuClick(MenuData.MenuItem item);
    }

    private final List<MenuData.MenuItem> mItems;
    private final OnMenuClickListener mListener;

    public MenuAdapter(List<MenuData.MenuItem> items, OnMenuClickListener listener) {
        this.mItems = items;
        this.mListener = listener;
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_menu, parent, false);
        return new ViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        MenuData.MenuItem item = mItems.get(position);
        holder.tvName.setText(item.getName());

        // 未启用的菜单灰显
        float alpha = item.isEnabled() ? 1.0f : 0.4f;
        holder.ivIcon.setAlpha(alpha);
        holder.tvName.setAlpha(alpha);
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

    private String menuContentDescription(MenuData.MenuItem item) {
        String target = item.getTarget();
        if ("PunchCardActivity".equals(target)) {
            return "qingoa_home_punch_entry";
        }
        if ("WorkflowWebActivity".equals(target)) {
            return "qingoa_home_workflow_entry";
        }
        String name = item.getName() != null ? item.getName() : "menu";
        return "qingoa_home_menu_" + name + (item.isEnabled() ? "_enabled" : "_disabled");
    }

    static class ViewHolder extends RecyclerView.ViewHolder {
        ImageView ivIcon;
        TextView tvName;

        ViewHolder(@NonNull View itemView) {
            super(itemView);
            ivIcon = itemView.findViewById(R.id.iv_icon);
            tvName = itemView.findViewById(R.id.tv_name);
        }
    }
}
