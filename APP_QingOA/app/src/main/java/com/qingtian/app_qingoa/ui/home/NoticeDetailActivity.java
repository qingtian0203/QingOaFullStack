package com.qingtian.app_qingoa.ui.home;

import android.os.Bundle;
import android.view.View;

import com.qingtian.app_qingoa.base.BaseActivity;
import com.qingtian.app_qingoa.databinding.ActivityNoticeDetailBinding;
import com.qingtian.app_qingoa.model.NoticeDetailData;
import com.qingtian.app_qingoa.net.ApiClient;
import com.qingtian.app_qingoa.net.ApiResponse;
import com.qingtian.app_qingoa.util.ToastUtils;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * 通知详情页。
 * 入口：HomeFragment 底部公告列表点击 → 传 notice_id 跳转。
 * 注意：此入口与首页菜单"通知公告"（NoticeListActivity）无关，不依赖菜单 enabled。
 */
public class NoticeDetailActivity extends BaseActivity {

    private ActivityNoticeDetailBinding mBinding;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        mBinding = ActivityNoticeDetailBinding.inflate(getLayoutInflater());
        setContentView(mBinding.getRoot());

        mBinding.btnBack.setOnClickListener(v -> finish());

        int noticeId = getIntent().getIntExtra("notice_id", -1);
        if (noticeId == -1) {
            ToastUtils.show(this, "参数错误");
            finish();
            return;
        }
        loadDetail(noticeId);
    }

    private void loadDetail(int noticeId) {
        mBinding.progressBar.setVisibility(View.VISIBLE);
        ApiClient.getService().getNoticeDetail(noticeId)
                .enqueue(new Callback<ApiResponse<NoticeDetailData>>() {
                    @Override
                    public void onResponse(Call<ApiResponse<NoticeDetailData>> call,
                                           Response<ApiResponse<NoticeDetailData>> response) {
                        mBinding.progressBar.setVisibility(View.GONE);
                        if (response.isSuccessful() && response.body() != null) {
                            ApiResponse<NoticeDetailData> body = response.body();
                            if (body.isTokenExpired()) { handleTokenExpired(); return; }
                            if (body.isSuccess() && body.getData() != null) {
                                bindDetail(body.getData());
                            }
                        }
                    }

                    @Override
                    public void onFailure(Call<ApiResponse<NoticeDetailData>> call, Throwable t) {
                        mBinding.progressBar.setVisibility(View.GONE);
                        ToastUtils.show(NoticeDetailActivity.this, "加载失败");
                    }
                });
    }

    private void bindDetail(NoticeDetailData data) {
        mBinding.detailContent.setVisibility(View.VISIBLE);
        mBinding.tvNoticeTitle.setText(data.getTitle() != null ? data.getTitle() : "");
        mBinding.tvNoticeTime.setText(data.getCreatedAt() != null ? data.getCreatedAt() : "");
        mBinding.tvNoticeContent.setText(data.getContent() != null ? data.getContent() : "");
    }
}
