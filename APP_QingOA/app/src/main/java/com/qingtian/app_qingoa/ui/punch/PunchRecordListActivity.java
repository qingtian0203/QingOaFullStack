package com.qingtian.app_qingoa.ui.punch;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;

import androidx.recyclerview.widget.LinearLayoutManager;

import com.qingtian.app_qingoa.base.BaseActivity;
import com.qingtian.app_qingoa.databinding.ActivityPunchRecordListBinding;
import com.qingtian.app_qingoa.model.PunchRecordListData;
import com.qingtian.app_qingoa.net.ApiClient;
import com.qingtian.app_qingoa.net.ApiResponse;
import com.qingtian.app_qingoa.util.ToastUtils;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/** 打卡记录列表页，展示历史上班/下班打卡 */
public class PunchRecordListActivity extends BaseActivity {

    private ActivityPunchRecordListBinding mBinding;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        mBinding = ActivityPunchRecordListBinding.inflate(getLayoutInflater());
        setContentView(mBinding.getRoot());

        mBinding.btnBack.setOnClickListener(v -> finish());
        loadRecords();
    }

    private void loadRecords() {
        mBinding.progressBar.setVisibility(View.VISIBLE);
        ApiClient.getService().getPunchRecords(1, 50)
                .enqueue(new Callback<ApiResponse<PunchRecordListData>>() {
                    @Override
                    public void onResponse(Call<ApiResponse<PunchRecordListData>> call,
                                           Response<ApiResponse<PunchRecordListData>> response) {
                        mBinding.progressBar.setVisibility(View.GONE);
                        if (response.isSuccessful() && response.body() != null) {
                            ApiResponse<PunchRecordListData> body = response.body();
                            if (body.isTokenExpired()) {
                                handleTokenExpired();
                                return;
                            }
                            if (body.isSuccess() && body.getData() != null
                                    && body.getData().getList() != null) {
                                setupList(body.getData());
                            }
                        }
                    }

                    @Override
                    public void onFailure(Call<ApiResponse<PunchRecordListData>> call, Throwable t) {
                        mBinding.progressBar.setVisibility(View.GONE);
                        ToastUtils.show(PunchRecordListActivity.this, "加载失败，请重试");
                    }
                });
    }

    private void setupList(PunchRecordListData data) {
        mBinding.rvRecords.setLayoutManager(new LinearLayoutManager(this));
        mBinding.rvRecords.setAdapter(new PunchRecordAdapter(groupByDay(data.getList()), record -> {
            int recordId = record.getPrimaryRecordId();
            if (recordId <= 0) {
                ToastUtils.show(this, "暂无可查看的打卡明细");
                return;
            }
            Intent intent = new Intent(this, PunchRecordDetailActivity.class);
            intent.putExtra("record_id", recordId);
            startActivity(intent);
        }));
    }

    private List<PunchRecordAdapter.DailyRecord> groupByDay(
            List<PunchRecordListData.PunchRecord> records
    ) {
        Map<String, PunchRecordAdapter.DailyRecord> grouped = new LinkedHashMap<>();
        for (PunchRecordListData.PunchRecord record : records) {
            String date = record.getPunchDate();
            if (date == null || date.isEmpty()) {
                date = "未知日期";
            }
            PunchRecordAdapter.DailyRecord day = grouped.get(date);
            if (day == null) {
                day = new PunchRecordAdapter.DailyRecord(date);
                grouped.put(date, day);
            }
            day.accept(record);
        }
        return new ArrayList<>(grouped.values());
    }
}
