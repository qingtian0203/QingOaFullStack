package com.qingtian.app_qingoa.ui.auth;

import android.content.Intent;
import android.os.Bundle;

import com.qingtian.app_qingoa.base.BaseActivity;
import com.qingtian.app_qingoa.net.ApiClient;
import com.qingtian.app_qingoa.net.ApiResponse;
import com.qingtian.app_qingoa.model.UserInfo;
import com.qingtian.app_qingoa.session.UserSession;
import com.qingtian.app_qingoa.ui.main.MainActivity;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * 启动页。
 * 职责：检查本地 Token 是否有效。
 * - 有 Token → 调 /api/auth/user-info 验证
 *   - code=0   → 进主页
 *   - code=1002 → 跳登录页（Token 过期）
 *   - 其他失败  → 跳登录页（保守处理）
 * - 无 Token  → 直接跳登录页
 *
 * 不需要布局文件（windowBackground 主题充当闪屏），跳转后立即 finish。
 */
public class SplashActivity extends BaseActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // 无需 setContentView，主题背景即为闪屏画面

        UserSession session = UserSession.getInstance();
        if (!session.isLoggedIn()) {
            // 本地无 Token，直接去登录
            goLogin();
            return;
        }

        // 有 Token，向服务端验证有效性
        ApiClient.getService().getUserInfo().enqueue(new Callback<ApiResponse<UserInfo>>() {
            @Override
            public void onResponse(Call<ApiResponse<UserInfo>> call,
                                   Response<ApiResponse<UserInfo>> response) {
                if (response.isSuccessful() && response.body() != null) {
                    ApiResponse<UserInfo> body = response.body();
                    if (body.isSuccess()) {
                        // Token 有效，刷新内存中的用户信息后进主页
                        session.saveSession(session.getToken(), body.getData());
                        goMain();
                    } else {
                        // 1002 或其他错误，清除并跳登录
                        session.clearSession();
                        goLogin();
                    }
                } else {
                    // HTTP 非 2xx，保守跳登录
                    goLogin();
                }
            }

            @Override
            public void onFailure(Call<ApiResponse<UserInfo>> call, Throwable t) {
                // 网络不通，跳登录（保守策略）
                goLogin();
            }
        });
    }

    private void goMain() {
        startActivity(new Intent(this, MainActivity.class));
        finish();
    }

    private void goLogin() {
        startActivity(new Intent(this, LoginActivity.class));
        finish();
    }
}
