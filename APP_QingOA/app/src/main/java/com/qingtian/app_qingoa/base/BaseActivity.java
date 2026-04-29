package com.qingtian.app_qingoa.base;

import android.content.Intent;
import android.os.Bundle;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import com.qingtian.app_qingoa.session.UserSession;
import com.qingtian.app_qingoa.ui.auth.LoginActivity;

/**
 * 所有业务页面的父类。
 * 统一处理 Token 过期（code=1002）的跳登录页逻辑，
 * 子类无需单独处理鉴权失败，调用 handleTokenExpired() 即可。
 */
public abstract class BaseActivity extends AppCompatActivity {

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // 初始化 UserSession（若已初始化则无副作用）
        UserSession.getInstance().init(this);
    }

    /**
     * 网络请求收到 code=1002 时调用。
     * 清除本地 Token，跳转到登录页，清除所有任务栈。
     */
    public void handleTokenExpired() {
        UserSession.getInstance().clearSession();
        Intent intent = new Intent(this, LoginActivity.class);
        // 清除所有上层 Activity，让用户重新登录
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        startActivity(intent);
        finish();
    }
}
