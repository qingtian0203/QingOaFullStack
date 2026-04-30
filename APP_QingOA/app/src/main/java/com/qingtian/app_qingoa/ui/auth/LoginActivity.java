package com.qingtian.app_qingoa.ui.auth;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.view.inputmethod.EditorInfo;

import com.qingtian.app_qingoa.base.BaseActivity;
import com.qingtian.app_qingoa.databinding.ActivityLoginBinding;
import com.qingtian.app_qingoa.model.LoginData;
import com.qingtian.app_qingoa.net.ApiClient;
import com.qingtian.app_qingoa.net.ApiResponse;
import com.qingtian.app_qingoa.net.LoginRequest;
import com.qingtian.app_qingoa.session.UserSession;
import com.qingtian.app_qingoa.ui.main.MainActivity;
import com.qingtian.app_qingoa.util.ToastUtils;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * 登录页。
 * 流程：输入账号密码 → POST /api/auth/login → 写入 Token + 用户信息 → 进主页。
 * 失败（1001）：Toast 提示错误信息，不跳转。
 */
public class LoginActivity extends BaseActivity {

    private ActivityLoginBinding mBinding;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        mBinding = ActivityLoginBinding.inflate(getLayoutInflater());
        setContentView(mBinding.getRoot());

        setupListeners();
    }

    private void setupListeners() {
        // 点击登录按钮
        mBinding.btnLogin.setOnClickListener(v -> attemptLogin());

        // 键盘"完成"键触发登录
        mBinding.etPassword.setOnEditorActionListener((v, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_DONE) {
                attemptLogin();
                return true;
            }
            return false;
        });
    }

    private void attemptLogin() {
        String username = getInputText(mBinding.etUsername);
        String password = getInputText(mBinding.etPassword);

        if (username.isEmpty()) {
            ToastUtils.show(this, "请输入账号");
            return;
        }
        if (password.isEmpty()) {
            ToastUtils.show(this, "请输入密码");
            return;
        }

        setLoading(true);

        ApiClient.getService()
                .login(new LoginRequest(username, password))
                .enqueue(new Callback<ApiResponse<LoginData>>() {
                    @Override
                    public void onResponse(Call<ApiResponse<LoginData>> call,
                                           Response<ApiResponse<LoginData>> response) {
                        setLoading(false);
                        if (response.isSuccessful() && response.body() != null) {
                            ApiResponse<LoginData> body = response.body();
                            if (body.isSuccess()) {
                                // 登录成功：保存 Token + 用户信息
                                LoginData data = body.getData();
                                UserSession.getInstance().saveSession(
                                        data.getToken(),
                                        data.toUserInfo()
                                );
                                goMain();
                            } else {
                                // 业务失败：1001 账号密码错误等
                                ToastUtils.show(LoginActivity.this, body.getMsg());
                            }
                        } else {
                            ToastUtils.show(LoginActivity.this, "服务器异常，请稍后重试");
                        }
                    }

                    @Override
                    public void onFailure(Call<ApiResponse<LoginData>> call, Throwable t) {
                        setLoading(false);
                        ToastUtils.show(LoginActivity.this, "网络连接失败，请检查网络");
                    }
                });
    }

    private void setLoading(boolean loading) {
        mBinding.btnLogin.setEnabled(!loading);
        mBinding.progressBar.setVisibility(loading ? View.VISIBLE : View.GONE);
    }

    private String getInputText(com.google.android.material.textfield.TextInputEditText et) {
        return et.getText() != null ? et.getText().toString().trim() : "";
    }

    private void goMain() {
        startActivity(new Intent(this, MainActivity.class));
        finish();
    }
}
