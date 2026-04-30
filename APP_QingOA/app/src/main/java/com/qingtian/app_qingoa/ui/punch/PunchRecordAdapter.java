package com.qingtian.app_qingoa.ui.punch;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.qingtian.app_qingoa.R;
import com.qingtian.app_qingoa.model.PunchRecordListData;

import java.util.List;

/** 打卡记录列表 Adapter */
public class PunchRecordAdapter extends RecyclerView.Adapter<PunchRecordAdapter.ViewHolder> {

    public interface OnItemClickListener {
        void onItemClick(PunchRecordListData.PunchRecord record);
    }

    private final List<PunchRecordListData.PunchRecord> mItems;
    private final OnItemClickListener mListener;

    public PunchRecordAdapter(List<PunchRecordListData.PunchRecord> items,
                              OnItemClickListener listener) {
        this.mItems = items;
        this.mListener = listener;
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_punch_record, parent, false);
        return new ViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        PunchRecordListData.PunchRecord record = mItems.get(position);

        holder.tvPunchType.setText(record.getPunchTypeLabel());
        holder.tvStatus.setText(record.getStatus() != null ? record.getStatus() : "");
        // 展示完整时间字符串，取空格后的时间部分作为主要展示
        String punchTime = record.getPunchTime() != null ? record.getPunchTime() : "";
        String[] parts = punchTime.split(" ");
        holder.tvPunchTime.setText(parts.length > 1 ? parts[1] : punchTime);
        holder.tvPointDistance.setText(record.getPointName() + "  ·  距离 " + record.getDistance() + "m");

        holder.itemView.setOnClickListener(v -> {
            if (mListener != null) mListener.onItemClick(record);
        });
    }

    @Override
    public int getItemCount() { return mItems != null ? mItems.size() : 0; }

    static class ViewHolder extends RecyclerView.ViewHolder {
        TextView tvPunchType, tvStatus, tvPunchTime, tvPointDistance;

        ViewHolder(@NonNull View itemView) {
            super(itemView);
            tvPunchType = itemView.findViewById(R.id.tv_punch_type);
            tvStatus = itemView.findViewById(R.id.tv_status);
            tvPunchTime = itemView.findViewById(R.id.tv_punch_time);
            tvPointDistance = itemView.findViewById(R.id.tv_point_distance);
        }
    }
}
