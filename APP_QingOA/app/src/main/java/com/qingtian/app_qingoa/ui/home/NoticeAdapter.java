package com.qingtian.app_qingoa.ui.home;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.qingtian.app_qingoa.R;
import com.qingtian.app_qingoa.model.NoticeListData;

import java.util.List;

/** 通知公告列表 Adapter，支持点击回调 */
public class NoticeAdapter extends RecyclerView.Adapter<NoticeAdapter.ViewHolder> {

    public interface OnItemClickListener {
        void onItemClick(NoticeListData.NoticeItem item);
    }

    private final List<NoticeListData.NoticeItem> mItems;
    private final OnItemClickListener mListener;

    public NoticeAdapter(List<NoticeListData.NoticeItem> items, OnItemClickListener listener) {
        this.mItems = items;
        this.mListener = listener;
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_notice, parent, false);
        return new ViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        NoticeListData.NoticeItem item = mItems.get(position);
        holder.tvTitle.setText(item.getTitle());
        holder.tvSummary.setText(item.getSummary() != null ? item.getSummary() : "");
        holder.tvTime.setText(item.getCreatedAt() != null ? item.getCreatedAt() : "");
        holder.itemView.setOnClickListener(v -> {
            if (mListener != null) mListener.onItemClick(item);
        });
    }

    @Override
    public int getItemCount() { return mItems != null ? mItems.size() : 0; }

    static class ViewHolder extends RecyclerView.ViewHolder {
        TextView tvTitle, tvSummary, tvTime;

        ViewHolder(@NonNull View itemView) {
            super(itemView);
            tvTitle = itemView.findViewById(R.id.tv_title);
            tvSummary = itemView.findViewById(R.id.tv_summary);
            tvTime = itemView.findViewById(R.id.tv_time);
        }
    }
}
