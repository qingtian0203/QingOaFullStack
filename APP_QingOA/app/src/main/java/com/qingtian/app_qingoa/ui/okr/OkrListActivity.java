package com.qingtian.app_qingoa.ui.okr;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;

import androidx.recyclerview.widget.LinearLayoutManager;

import com.qingtian.app_qingoa.base.BaseActivity;
import com.qingtian.app_qingoa.databinding.ActivityOkrListBinding;
import com.qingtian.app_qingoa.model.OkrListData;
import com.qingtian.app_qingoa.net.ApiClient;
import com.qingtian.app_qingoa.net.ApiResponse;
import com.qingtian.app_qingoa.util.ToastUtils;

import java.util.List;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/** v1.5B：OKR 列表页，当前主入口已迁移到底部 Tab。 */
public class OkrListActivity extends BaseActivity {

    private ActivityOkrListBinding mBinding;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        mBinding = ActivityOkrListBinding.inflate(getLayoutInflater());
        setContentView(mBinding.getRoot());

        mBinding.btnBack.setOnClickListener(v -> finish());
        mBinding.btnCreate.setOnClickListener(v -> startActivity(new Intent(this, OkrCreateActivity.class)));
        mBinding.rvOkrs.setLayoutManager(new LinearLayoutManager(this));
    }

    @Override
    protected void onResume() {
        super.onResume();
        loadOkrs();
    }

    private void loadOkrs() {
        showLoading(true);
        ApiClient.getService().getOkrList(null).enqueue(new Callback<ApiResponse<OkrListData>>() {
            @Override
            public void onResponse(Call<ApiResponse<OkrListData>> call,
                                   Response<ApiResponse<OkrListData>> response) {
                showLoading(false);
                if (response.isSuccessful() && response.body() != null) {
                    ApiResponse<OkrListData> body = response.body();
                    if (body.isTokenExpired()) {
                        handleTokenExpired();
                        return;
                    }
                    if (body.isSuccess() && body.getData() != null) {
                        setupList(body.getData().getList());
                        return;
                    }
                    ToastUtils.show(OkrListActivity.this, body.getMsg());
                }
            }

            @Override
            public void onFailure(Call<ApiResponse<OkrListData>> call, Throwable t) {
                showLoading(false);
                ToastUtils.show(OkrListActivity.this, "加载 OKR 失败");
            }
        });
    }

    private void setupList(List<OkrListData.OkrItem> list) {
        boolean empty = list == null || list.isEmpty();
        mBinding.emptyState.setVisibility(empty ? View.VISIBLE : View.GONE);
        mBinding.rvOkrs.setVisibility(empty ? View.GONE : View.VISIBLE);
        if (!empty) {
            mBinding.rvOkrs.setAdapter(new OkrAdapter(list, item -> {
                Intent intent = new Intent(this, OkrDetailActivity.class);
                intent.putExtra(OkrDetailActivity.EXTRA_OKR_ID, item.getId());
                startActivity(intent);
            }));
        }
    }

    private void showLoading(boolean loading) {
        mBinding.progressBar.setVisibility(loading ? View.VISIBLE : View.GONE);
    }
}
