package com.qingtian.app_qingoa.ui.okr;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ProgressBar;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.qingtian.app_qingoa.R;
import com.qingtian.app_qingoa.model.OkrDetailData;

import java.text.DecimalFormat;
import java.util.List;

/** OKR 详情页 KR Adapter。 */
public class KeyResultAdapter extends RecyclerView.Adapter<KeyResultAdapter.ViewHolder> {

    public interface OnUpdateClickListener {
        void onUpdateClick(OkrDetailData.KeyResult item);
    }

    private final List<OkrDetailData.KeyResult> mItems;
    private final OnUpdateClickListener mListener;
    private final DecimalFormat mFormat = new DecimalFormat("0.##");

    public KeyResultAdapter(List<OkrDetailData.KeyResult> items, OnUpdateClickListener listener) {
        this.mItems = items;
        this.mListener = listener;
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_key_result, parent, false);
        return new ViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        OkrDetailData.KeyResult item = mItems.get(position);
        String unit = item.getUnit() != null ? item.getUnit() : "";
        holder.tvTitle.setText(item.getTitle());
        holder.tvValue.setText(mFormat.format(item.getCurrentValue()) + " / "
                + mFormat.format(item.getTargetValue()) + " " + unit);
        holder.tvProgress.setText(item.getProgress() + "%");
        holder.progressKr.setProgress(item.getProgress());
        holder.btnUpdate.setOnClickListener(v -> {
            if (mListener != null) {
                mListener.onUpdateClick(item);
            }
        });
    }

    @Override
    public int getItemCount() {
        return mItems != null ? mItems.size() : 0;
    }

    static class ViewHolder extends RecyclerView.ViewHolder {
        TextView tvTitle;
        TextView tvValue;
        TextView tvProgress;
        TextView btnUpdate;
        ProgressBar progressKr;

        ViewHolder(@NonNull View itemView) {
            super(itemView);
            tvTitle = itemView.findViewById(R.id.tv_title);
            tvValue = itemView.findViewById(R.id.tv_value);
            tvProgress = itemView.findViewById(R.id.tv_progress);
            btnUpdate = itemView.findViewById(R.id.btn_update);
            progressKr = itemView.findViewById(R.id.progress_kr);
        }
    }
}
