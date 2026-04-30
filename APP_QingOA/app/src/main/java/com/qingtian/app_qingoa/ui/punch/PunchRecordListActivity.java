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
        mBinding.rvRecords.setAdapter(new PunchRecordAdapter(data.getList(), record -> {
            // 点击跳详情
            Intent intent = new Intent(this, PunchRecordDetailActivity.class);
            intent.putExtra("record_id", record.getId());
            startActivity(intent);
        }));
    }
}
