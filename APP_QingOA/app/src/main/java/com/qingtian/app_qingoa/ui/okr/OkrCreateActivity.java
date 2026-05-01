package com.qingtian.app_qingoa.ui.okr;

import android.os.Bundle;
import android.view.View;

import com.qingtian.app_qingoa.base.BaseActivity;
import com.qingtian.app_qingoa.databinding.ActivityOkrCreateBinding;
import com.qingtian.app_qingoa.model.OkrCreateResultData;
import com.qingtian.app_qingoa.net.ApiClient;
import com.qingtian.app_qingoa.net.ApiResponse;
import com.qingtian.app_qingoa.net.OkrCreateRequest;
import com.qingtian.app_qingoa.util.ToastUtils;

import java.util.Collections;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/** v1.5B：创建 OKR。 */
public class OkrCreateActivity extends BaseActivity {

    private ActivityOkrCreateBinding mBinding;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        mBinding = ActivityOkrCreateBinding.inflate(getLayoutInflater());
        setContentView(mBinding.getRoot());

        enableKeyboardAwareScroll(mBinding.scrollContent);
        mBinding.btnBack.setOnClickListener(v -> finish());
        mBinding.btnSubmit.setOnClickListener(v -> submit());
    }

    private void submit() {
        String title = text(mBinding.etTitle);
        String period = text(mBinding.etPeriod);
        String description = text(mBinding.etDescription);
        String krTitle = text(mBinding.etKrTitle);
        String targetValueText = text(mBinding.etTargetValue);
        String unit = text(mBinding.etUnit);

        if (title.isEmpty()) { ToastUtils.show(this, "请输入 OKR 标题"); return; }
        if (period.isEmpty()) { ToastUtils.show(this, "请输入周期"); return; }
        if (krTitle.isEmpty()) { ToastUtils.show(this, "请输入 KR 标题"); return; }
        if (targetValueText.isEmpty()) { ToastUtils.show(this, "请输入 KR 目标值"); return; }
        if (unit.isEmpty()) { unit = "%"; }

        double targetValue;
        try {
            targetValue = Double.parseDouble(targetValueText);
        } catch (NumberFormatException e) {
            ToastUtils.show(this, "KR 目标值格式错误");
            return;
        }
        if (targetValue <= 0) {
            ToastUtils.show(this, "KR 目标值必须大于 0");
            return;
        }

        OkrCreateRequest body = new OkrCreateRequest(
                title,
                description,
                period,
                Collections.singletonList(new OkrCreateRequest.KeyResultPayload(krTitle, targetValue, unit))
        );
        create(body);
    }

    private void create(OkrCreateRequest body) {
        setLoading(true);
        ApiClient.getService().createOkr(body).enqueue(new Callback<ApiResponse<OkrCreateResultData>>() {
            @Override
            public void onResponse(Call<ApiResponse<OkrCreateResultData>> call,
                                   Response<ApiResponse<OkrCreateResultData>> response) {
                setLoading(false);
                if (response.isSuccessful() && response.body() != null) {
                    ApiResponse<OkrCreateResultData> result = response.body();
                    if (result.isTokenExpired()) {
                        handleTokenExpired();
                        return;
                    }
                    if (result.isSuccess()) {
                        ToastUtils.show(OkrCreateActivity.this, "OKR 已创建");
                        finish();
                        return;
                    }
                    ToastUtils.show(OkrCreateActivity.this, result.getMsg());
                }
            }

            @Override
            public void onFailure(Call<ApiResponse<OkrCreateResultData>> call, Throwable t) {
                setLoading(false);
                ToastUtils.show(OkrCreateActivity.this, "创建失败，请重试");
            }
        });
    }

    private String text(android.widget.EditText view) {
        return view.getText() != null ? view.getText().toString().trim() : "";
    }

    private void setLoading(boolean loading) {
        mBinding.progressBar.setVisibility(loading ? View.VISIBLE : View.GONE);
        mBinding.btnSubmit.setEnabled(!loading);
    }
}
