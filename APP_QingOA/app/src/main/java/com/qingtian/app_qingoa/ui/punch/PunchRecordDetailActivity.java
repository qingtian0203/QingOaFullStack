package com.qingtian.app_qingoa.ui.punch;

import android.os.Bundle;
import android.view.View;

import com.qingtian.app_qingoa.base.BaseActivity;
import com.qingtian.app_qingoa.databinding.ActivityPunchRecordDetailBinding;
import com.qingtian.app_qingoa.model.PunchRecordDetailData;
import com.qingtian.app_qingoa.net.ApiClient;
import com.qingtian.app_qingoa.net.ApiResponse;
import com.qingtian.app_qingoa.util.ToastUtils;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/** 单条打卡详情页（时间、地点、距离、设备ID） */
public class PunchRecordDetailActivity extends BaseActivity {

    private ActivityPunchRecordDetailBinding mBinding;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        mBinding = ActivityPunchRecordDetailBinding.inflate(getLayoutInflater());
        setContentView(mBinding.getRoot());

        mBinding.btnBack.setOnClickListener(v -> finish());

        int recordId = getIntent().getIntExtra("record_id", -1);
        if (recordId == -1) {
            ToastUtils.show(this, "参数错误");
            finish();
            return;
        }
        loadDetail(recordId);
    }

    private void loadDetail(int recordId) {
        mBinding.progressBar.setVisibility(View.VISIBLE);
        ApiClient.getService().getPunchRecordDetail(recordId)
                .enqueue(new Callback<ApiResponse<PunchRecordDetailData>>() {
                    @Override
                    public void onResponse(Call<ApiResponse<PunchRecordDetailData>> call,
                                           Response<ApiResponse<PunchRecordDetailData>> response) {
                        mBinding.progressBar.setVisibility(View.GONE);
                        if (response.isSuccessful() && response.body() != null) {
                            ApiResponse<PunchRecordDetailData> body = response.body();
                            if (body.isTokenExpired()) { handleTokenExpired(); return; }
                            if (body.isSuccess() && body.getData() != null) {
                                bindDetail(body.getData());
                            }
                        }
                    }

                    @Override
                    public void onFailure(Call<ApiResponse<PunchRecordDetailData>> call, Throwable t) {
                        mBinding.progressBar.setVisibility(View.GONE);
                        ToastUtils.show(PunchRecordDetailActivity.this, "加载失败");
                    }
                });
    }

    private void bindDetail(PunchRecordDetailData data) {
        mBinding.tvTitle.setText(data.getPunchTypeLabel());
        mBinding.tvTypeLabel.setText(data.getPunchTypeLabel());

        // 取时间部分展示大字，完整日期展示小字
        String punchTime = data.getPunchTime() != null ? data.getPunchTime() : "";
        String[] parts = punchTime.split(" ");
        mBinding.tvPunchTime.setText(parts.length > 1 ? parts[1] : punchTime);
        mBinding.tvPunchDate.setText(data.getPunchDate() != null ? data.getPunchDate() : "");

        mBinding.tvPointName.setText(data.getPointName() != null ? data.getPointName() : "-");
        mBinding.tvDistance.setText(data.getDistance() + " 米");
        mBinding.tvDeviceId.setText(data.getDeviceId() != null ? data.getDeviceId() : "-");
    }
}
