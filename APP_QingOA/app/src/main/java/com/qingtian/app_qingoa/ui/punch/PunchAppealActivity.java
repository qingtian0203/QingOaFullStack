package com.qingtian.app_qingoa.ui.punch;

import android.app.AlertDialog;
import android.os.Bundle;
import android.view.View;
import android.widget.EditText;

import androidx.recyclerview.widget.LinearLayoutManager;

import com.qingtian.app_qingoa.base.BaseActivity;
import com.qingtian.app_qingoa.databinding.ActivityPunchAppealBinding;
import com.qingtian.app_qingoa.model.PunchAppealListData;
import com.qingtian.app_qingoa.model.PunchAppealResultData;
import com.qingtian.app_qingoa.net.ApiClient;
import com.qingtian.app_qingoa.net.ApiResponse;
import com.qingtian.app_qingoa.net.PunchAppealRequest;
import com.qingtian.app_qingoa.net.PunchAppealReviewRequest;
import com.qingtian.app_qingoa.util.ToastUtils;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/** v1.6B Native 补卡申诉与待我审批页。 */
public class PunchAppealActivity extends BaseActivity {

    public static final String EXTRA_MODE = "mode";
    public static final String MODE_REVIEW = "review";

    private ActivityPunchAppealBinding mBinding;
    private boolean mReviewMode;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        mBinding = ActivityPunchAppealBinding.inflate(getLayoutInflater());
        setContentView(mBinding.getRoot());

        mReviewMode = MODE_REVIEW.equals(getIntent().getStringExtra(EXTRA_MODE));
        mBinding.btnBack.setOnClickListener(v -> finish());
        mBinding.tvTitle.setText(mReviewMode ? "待我审批" : "补卡申诉");
        mBinding.tvSubtitle.setText(mReviewMode
                ? "处理下属或 HR 环节的补卡申请"
                : "提交缺卡、迟到或早退的补卡说明");
        mBinding.formCard.setVisibility(mReviewMode ? View.GONE : View.VISIBLE);
        mBinding.tvListTitle.setText(mReviewMode ? "待处理申请" : "我的申诉");
        mBinding.rvAppeals.setLayoutManager(new LinearLayoutManager(this));

        if (!mReviewMode) {
            mBinding.etPunchDate.setText(new SimpleDateFormat("yyyy-MM-dd", Locale.CHINA).format(new Date()));
            mBinding.etExpectTime.setText("09:00:00");
            mBinding.radioClockIn.setOnClickListener(v -> mBinding.etExpectTime.setText("09:00:00"));
            mBinding.radioClockOut.setOnClickListener(v -> mBinding.etExpectTime.setText("18:00:00"));
            mBinding.btnSubmitAppeal.setOnClickListener(v -> submitAppeal());
        }
        loadList();
    }

    private void submitAppeal() {
        String punchDate = text(mBinding.etPunchDate);
        String expectTime = text(mBinding.etExpectTime);
        String reason = text(mBinding.etReason);
        String punchType = mBinding.radioClockIn.isChecked() ? "clock_in" : "clock_out";
        if (punchDate.isEmpty() || expectTime.isEmpty() || reason.length() < 2) {
            ToastUtils.show(this, "请填写日期、时间和不少于 2 个字的原因");
            return;
        }
        setLoading(true);
        ApiClient.getService()
                .createPunchAppeal(new PunchAppealRequest(punchDate, punchType, reason, expectTime))
                .enqueue(new Callback<ApiResponse<PunchAppealResultData>>() {
                    @Override
                    public void onResponse(Call<ApiResponse<PunchAppealResultData>> call,
                                           Response<ApiResponse<PunchAppealResultData>> response) {
                        setLoading(false);
                        if (response.isSuccessful() && response.body() != null) {
                            ApiResponse<PunchAppealResultData> body = response.body();
                            if (body.isTokenExpired()) { handleTokenExpired(); return; }
                            ToastUtils.show(PunchAppealActivity.this, body.getMsg());
                            if (body.isSuccess()) {
                                mBinding.etReason.setText("");
                                loadList();
                            }
                        }
                    }

                    @Override
                    public void onFailure(Call<ApiResponse<PunchAppealResultData>> call, Throwable t) {
                        setLoading(false);
                        ToastUtils.show(PunchAppealActivity.this, "提交失败，请检查网络");
                    }
                });
    }

    private void loadList() {
        mBinding.progressBar.setVisibility(View.VISIBLE);
        Call<ApiResponse<PunchAppealListData>> call = mReviewMode
                ? ApiClient.getService().getPendingPunchAppeals()
                : ApiClient.getService().getPunchAppeals();
        call.enqueue(new Callback<ApiResponse<PunchAppealListData>>() {
            @Override
            public void onResponse(Call<ApiResponse<PunchAppealListData>> call,
                                   Response<ApiResponse<PunchAppealListData>> response) {
                mBinding.progressBar.setVisibility(View.GONE);
                if (response.isSuccessful() && response.body() != null) {
                    ApiResponse<PunchAppealListData> body = response.body();
                    if (body.isTokenExpired()) { handleTokenExpired(); return; }
                    if (body.isSuccess() && body.getData() != null) {
                        setupList(body.getData());
                    }
                }
            }

            @Override
            public void onFailure(Call<ApiResponse<PunchAppealListData>> call, Throwable t) {
                mBinding.progressBar.setVisibility(View.GONE);
                ToastUtils.show(PunchAppealActivity.this, "加载失败");
            }
        });
    }

    private void setupList(PunchAppealListData data) {
        boolean empty = data.getList() == null || data.getList().isEmpty();
        mBinding.tvEmpty.setVisibility(empty ? View.VISIBLE : View.GONE);
        mBinding.rvAppeals.setVisibility(empty ? View.GONE : View.VISIBLE);
        mBinding.rvAppeals.setAdapter(new PunchAppealAdapter(data.getList(), mReviewMode, this::confirmReview));
    }

    private void confirmReview(PunchAppealListData.PunchAppeal item, String action) {
        EditText input = new EditText(this);
        input.setHint("审批意见");
        input.setMinLines(2);
        input.setPadding(32, 20, 32, 20);
        String title = "approve".equals(action) ? "通过补卡申诉" : "驳回补卡申诉";
        new AlertDialog.Builder(this)
                .setTitle(title)
                .setMessage(item.getPunchDate() + " · " + item.getPunchTypeLabel())
                .setView(input)
                .setNegativeButton("取消", null)
                .setPositiveButton("确认", (dialog, which) ->
                        reviewAppeal(item.getId(), action, text(input)))
                .show();
    }

    private void reviewAppeal(int appealId, String action, String note) {
        setLoading(true);
        ApiClient.getService()
                .reviewPunchAppeal(appealId, new PunchAppealReviewRequest(action, note))
                .enqueue(new Callback<ApiResponse<PunchAppealListData.PunchAppeal>>() {
                    @Override
                    public void onResponse(Call<ApiResponse<PunchAppealListData.PunchAppeal>> call,
                                           Response<ApiResponse<PunchAppealListData.PunchAppeal>> response) {
                        setLoading(false);
                        if (response.isSuccessful() && response.body() != null) {
                            ApiResponse<PunchAppealListData.PunchAppeal> body = response.body();
                            if (body.isTokenExpired()) { handleTokenExpired(); return; }
                            ToastUtils.show(PunchAppealActivity.this, body.getMsg());
                            if (body.isSuccess()) {
                                loadList();
                            }
                        }
                    }

                    @Override
                    public void onFailure(Call<ApiResponse<PunchAppealListData.PunchAppeal>> call, Throwable t) {
                        setLoading(false);
                        ToastUtils.show(PunchAppealActivity.this, "审批失败");
                    }
                });
    }

    private void setLoading(boolean loading) {
        mBinding.btnSubmitAppeal.setEnabled(!loading);
        if (loading) {
            mBinding.progressBar.setVisibility(View.VISIBLE);
        }
    }

    private String text(EditText editText) {
        return editText.getText() != null ? editText.getText().toString().trim() : "";
    }
}
