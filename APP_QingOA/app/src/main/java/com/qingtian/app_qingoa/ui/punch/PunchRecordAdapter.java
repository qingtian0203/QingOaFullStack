package com.qingtian.app_qingoa.ui.punch;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.qingtian.app_qingoa.R;
import com.qingtian.app_qingoa.model.PunchRecordListData;

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import java.util.Locale;

/** 每日打卡记录 Adapter：底层仍是 punch_records 明细，列表按自然日聚合展示。 */
public class PunchRecordAdapter extends RecyclerView.Adapter<PunchRecordAdapter.ViewHolder> {

    public interface OnDayClickListener {
        void onDayClick(DailyRecord record);
    }

    private final List<DailyRecord> mItems;
    private final OnDayClickListener mListener;

    public PunchRecordAdapter(List<DailyRecord> items, OnDayClickListener listener) {
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
        DailyRecord record = mItems.get(position);
        holder.tvPunchDate.setText(record.getPunchDate());
        holder.tvWeekday.setText(record.getWeekday());
        holder.tvDayStatus.setText(record.getDayStatusLabel());
        holder.tvClockInTime.setText(record.getClockInTimeLabel());
        holder.tvClockOutTime.setText(record.getClockOutTimeLabel());
        holder.tvPointDistance.setText(record.getPointDistanceLabel());
        holder.itemView.setOnClickListener(v -> {
            if (mListener != null) {
                mListener.onDayClick(record);
            }
        });
    }

    @Override
    public int getItemCount() {
        return mItems != null ? mItems.size() : 0;
    }

    static class ViewHolder extends RecyclerView.ViewHolder {
        TextView tvPunchDate;
        TextView tvWeekday;
        TextView tvDayStatus;
        TextView tvClockInTime;
        TextView tvClockOutTime;
        TextView tvPointDistance;

        ViewHolder(@NonNull View itemView) {
            super(itemView);
            tvPunchDate = itemView.findViewById(R.id.tv_punch_date);
            tvWeekday = itemView.findViewById(R.id.tv_weekday);
            tvDayStatus = itemView.findViewById(R.id.tv_day_status);
            tvClockInTime = itemView.findViewById(R.id.tv_clock_in_time);
            tvClockOutTime = itemView.findViewById(R.id.tv_clock_out_time);
            tvPointDistance = itemView.findViewById(R.id.tv_point_distance);
        }
    }

    public static class DailyRecord {
        private final String punchDate;
        private PunchRecordListData.PunchRecord clockIn;
        private PunchRecordListData.PunchRecord clockOut;

        public DailyRecord(String punchDate) {
            this.punchDate = punchDate;
        }

        public void accept(PunchRecordListData.PunchRecord record) {
            if (record == null) return;
            if (record.isClockIn()) {
                if (clockIn == null || isAfter(record.getPunchTime(), clockIn.getPunchTime())) {
                    clockIn = record;
                }
            } else {
                if (clockOut == null || isAfter(record.getPunchTime(), clockOut.getPunchTime())) {
                    clockOut = record;
                }
            }
        }

        public String getPunchDate() {
            return punchDate != null && !punchDate.isEmpty() ? punchDate : "未知日期";
        }

        public String getWeekday() {
            if (punchDate == null || punchDate.isEmpty()) {
                return "每日考勤";
            }
            try {
                Date date = new SimpleDateFormat("yyyy-MM-dd", Locale.CHINA).parse(punchDate);
                return date != null ? new SimpleDateFormat("EEEE", Locale.CHINA).format(date) : "每日考勤";
            } catch (ParseException e) {
                return "每日考勤";
            }
        }

        public String getDayStatusLabel() {
            if (clockIn != null && clockOut != null) return "已完成";
            if (clockIn != null) return "缺下班卡";
            if (clockOut != null) return "缺上班卡";
            return "无记录";
        }

        public String getClockInTimeLabel() {
            return clockIn != null ? timeOnly(clockIn.getPunchTime()) : "未打卡";
        }

        public String getClockOutTimeLabel() {
            return clockOut != null ? timeOnly(clockOut.getPunchTime()) : "未打卡";
        }

        public String getPointDistanceLabel() {
            PunchRecordListData.PunchRecord record = clockOut != null ? clockOut : clockIn;
            if (record == null) return "暂无打卡地点";
            String point = record.getPointName() != null ? record.getPointName() : "未知打卡点";
            return "打卡点：" + point + "  ·  最近距离 " + record.getDistance() + "m";
        }

        private static String timeOnly(String value) {
            if (value == null || value.isEmpty()) return "--:--:--";
            String[] parts = value.split(" ");
            return parts.length > 1 ? parts[1] : value;
        }

        private static boolean isAfter(String left, String right) {
            if (left == null) return false;
            if (right == null) return true;
            return left.compareTo(right) > 0;
        }
    }
}
