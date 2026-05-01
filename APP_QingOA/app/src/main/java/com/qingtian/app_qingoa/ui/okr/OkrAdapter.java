package com.qingtian.app_qingoa.ui.okr;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ProgressBar;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.qingtian.app_qingoa.R;
import com.qingtian.app_qingoa.model.OkrListData;

import java.util.List;

/** OKR 列表 Adapter。 */
public class OkrAdapter extends RecyclerView.Adapter<OkrAdapter.ViewHolder> {

    public interface OnOkrClickListener {
        void onOkrClick(OkrListData.OkrItem item);
    }

    private final List<OkrListData.OkrItem> mItems;
    private final OnOkrClickListener mListener;

    public OkrAdapter(List<OkrListData.OkrItem> items, OnOkrClickListener listener) {
        this.mItems = items;
        this.mListener = listener;
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_okr, parent, false);
        return new ViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        OkrListData.OkrItem item = mItems.get(position);
        holder.tvTitle.setText(item.getTitle());
        holder.tvDescription.setText(emptyToDefault(item.getDescription(), "暂无说明"));
        holder.tvPeriod.setText(item.getPeriod());
        holder.tvKrCount.setText(item.getKrCount() + " 个 KR");
        holder.tvProgress.setText(item.getProgress() + "%");
        holder.progressOkr.setProgress(item.getProgress());
        holder.itemView.setOnClickListener(v -> {
            if (mListener != null) {
                mListener.onOkrClick(item);
            }
        });
    }

    @Override
    public int getItemCount() {
        return mItems != null ? mItems.size() : 0;
    }

    private String emptyToDefault(String value, String fallback) {
        return value == null || value.trim().isEmpty() ? fallback : value;
    }

    static class ViewHolder extends RecyclerView.ViewHolder {
        TextView tvTitle;
        TextView tvDescription;
        TextView tvPeriod;
        TextView tvKrCount;
        TextView tvProgress;
        ProgressBar progressOkr;

        ViewHolder(@NonNull View itemView) {
            super(itemView);
            tvTitle = itemView.findViewById(R.id.tv_title);
            tvDescription = itemView.findViewById(R.id.tv_description);
            tvPeriod = itemView.findViewById(R.id.tv_period);
            tvKrCount = itemView.findViewById(R.id.tv_kr_count);
            tvProgress = itemView.findViewById(R.id.tv_progress);
            progressOkr = itemView.findViewById(R.id.progress_okr);
        }
    }
}
