package com.qingtian.app_qingoa.ui.okr;

import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;

import androidx.recyclerview.widget.LinearLayoutManager;

import com.google.android.material.bottomsheet.BottomSheetDialog;
import com.qingtian.app_qingoa.base.BaseActivity;
import com.qingtian.app_qingoa.databinding.ActivityOkrDetailBinding;
import com.qingtian.app_qingoa.databinding.DialogUpdateKrProgressBinding;
import com.qingtian.app_qingoa.model.OkrDetailData;
import com.qingtian.app_qingoa.model.OkrProgressResultData;
import com.qingtian.app_qingoa.net.ApiClient;
import com.qingtian.app_qingoa.net.ApiResponse;
import com.qingtian.app_qingoa.net.KrProgressRequest;
import com.qingtian.app_qingoa.util.ToastUtils;

import java.text.DecimalFormat;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/** v1.5B：OKR 详情与 KR 进度更新。 */
public class OkrDetailActivity extends BaseActivity {

    public static final String EXTRA_OKR_ID = "okr_id";

    private final DecimalFormat mFormat = new DecimalFormat("0.##");
    private ActivityOkrDetailBinding mBinding;
    private int mOkrId;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        mBinding = ActivityOkrDetailBinding.inflate(getLayoutInflater());
        setContentView(mBinding.getRoot());

        mOkrId = getIntent().getIntExtra(EXTRA_OKR_ID, 0);
        mBinding.btnBack.setOnClickListener(v -> finish());
        mBinding.rvKeyResults.setLayoutManager(new LinearLayoutManager(this));
        if (mOkrId <= 0) {
            ToastUtils.show(this, "OKR 不存在");
            finish();
            return;
        }
        loadDetail();
    }

    private void loadDetail() {
        showLoading(true);
        ApiClient.getService().getOkrDetail(mOkrId).enqueue(new Callback<ApiResponse<OkrDetailData>>() {
            @Override
            public void onResponse(Call<ApiResponse<OkrDetailData>> call,
                                   Response<ApiResponse<OkrDetailData>> response) {
                showLoading(false);
                if (response.isSuccessful() && response.body() != null) {
                    ApiResponse<OkrDetailData> body = response.body();
                    if (body.isTokenExpired()) {
                        handleTokenExpired();
                        return;
                    }
                    if (body.isSuccess() && body.getData() != null) {
                        render(body.getData());
                        return;
                    }
                    ToastUtils.show(OkrDetailActivity.this, body.getMsg());
                }
            }

            @Override
            public void onFailure(Call<ApiResponse<OkrDetailData>> call, Throwable t) {
                showLoading(false);
                ToastUtils.show(OkrDetailActivity.this, "加载 OKR 详情失败");
            }
        });
    }

    private void render(OkrDetailData data) {
        mBinding.detailContent.setVisibility(View.VISIBLE);
        mBinding.tvPeriod.setText(data.getPeriod());
        mBinding.tvTitle.setText(data.getTitle());
        mBinding.tvDescription.setText(emptyToDefault(data.getDescription(), "暂无说明"));
        mBinding.tvProgress.setText(data.getProgress() + "%");
        mBinding.progressOkr.setProgress(data.getProgress());
        mBinding.rvKeyResults.setAdapter(new KeyResultAdapter(data.getKeyResults(), this::showUpdateDialog));
    }

    private void showUpdateDialog(OkrDetailData.KeyResult item) {
        BottomSheetDialog dialog = new BottomSheetDialog(this);
        DialogUpdateKrProgressBinding binding = DialogUpdateKrProgressBinding.inflate(LayoutInflater.from(this));
        dialog.setContentView(binding.getRoot());

        String unit = item.getUnit() != null ? item.getUnit() : "";
        binding.tvHint.setText("当前 " + mFormat.format(item.getCurrentValue())
                + " / 目标 " + mFormat.format(item.getTargetValue()) + " " + unit);
        binding.etCurrentValue.setText(mFormat.format(item.getCurrentValue()));
        binding.etCurrentValue.setSelection(binding.etCurrentValue.getText().length());
        binding.btnSubmit.setOnClickListener(v -> {
            String value = binding.etCurrentValue.getText() != null
                    ? binding.etCurrentValue.getText().toString().trim() : "";
            if (value.isEmpty()) {
                ToastUtils.show(this, "请输入当前值");
                return;
            }
            try {
                updateProgress(item.getId(), Double.parseDouble(value), dialog);
            } catch (NumberFormatException e) {
                ToastUtils.show(this, "当前值格式错误");
            }
        });
        dialog.show();
    }

    private void updateProgress(int krId, double currentValue, BottomSheetDialog dialog) {
        ApiClient.getService().updateKeyResultProgress(mOkrId, krId, new KrProgressRequest(currentValue))
                .enqueue(new Callback<ApiResponse<OkrProgressResultData>>() {
                    @Override
                    public void onResponse(Call<ApiResponse<OkrProgressResultData>> call,
                                           Response<ApiResponse<OkrProgressResultData>> response) {
                        if (response.isSuccessful() && response.body() != null) {
                            ApiResponse<OkrProgressResultData> body = response.body();
                            if (body.isTokenExpired()) {
                                handleTokenExpired();
                                return;
                            }
                            if (body.isSuccess()) {
                                dialog.dismiss();
                                ToastUtils.show(OkrDetailActivity.this, "进度已更新");
                                loadDetail();
                                return;
                            }
                            ToastUtils.show(OkrDetailActivity.this, body.getMsg());
                        }
                    }

                    @Override
                    public void onFailure(Call<ApiResponse<OkrProgressResultData>> call, Throwable t) {
                        ToastUtils.show(OkrDetailActivity.this, "更新失败，请重试");
                    }
                });
    }

    private void showLoading(boolean loading) {
        mBinding.progressBar.setVisibility(loading ? View.VISIBLE : View.GONE);
        if (loading) {
            mBinding.detailContent.setVisibility(View.GONE);
        }
    }

    private String emptyToDefault(String value, String fallback) {
        return value == null || value.trim().isEmpty() ? fallback : value;
    }
}
