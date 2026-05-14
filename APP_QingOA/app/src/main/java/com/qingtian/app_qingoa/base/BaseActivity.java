package com.qingtian.app_qingoa.base;

import android.content.Intent;
import android.graphics.Insets;
import android.graphics.Rect;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.view.WindowInsets;
import android.widget.ScrollView;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import com.qingtian.app_qingoa.net.ApiClient;
import com.qingtian.app_qingoa.session.UserSession;
import com.qingtian.app_qingoa.ui.auth.LoginActivity;

/**
 * 所有业务页面的父类。
 * 统一处理 Token 过期（code=1002）的跳登录页逻辑，
 * 子类无需单独处理鉴权失败，调用 handleTokenExpired() 即可。
 */
public abstract class BaseActivity extends AppCompatActivity {

    private static final float KEYBOARD_VISIBLE_THRESHOLD = 0.15f;

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // 初始化 UserSession（若已初始化则无副作用）
        UserSession.getInstance().init(this);
        ApiClient.init(this);
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

    /**
     * 让表单页在软键盘弹出时主动给 ScrollView 留出键盘高度，并把当前输入框滚到键盘上方。
     * 部分全面屏/三方输入法环境下 windowSoftInputMode=adjustResize 不稳定，所以这里做一层页面内兜底。
     */
    protected void enableKeyboardAwareScroll(ScrollView scrollView) {
        int originalBottomPadding = scrollView.getPaddingBottom();
        int extraBottomPadding = dp(24);
        scrollView.setClipToPadding(false);
        View root = scrollView.getRootView();
        root.getViewTreeObserver().addOnGlobalLayoutListener(() -> {
            int keyboardHeight = resolveKeyboardHeight(root);
            boolean keyboardVisible = keyboardHeight > root.getHeight() * KEYBOARD_VISIBLE_THRESHOLD;
            int bottomPadding = keyboardVisible
                    ? keyboardHeight + extraBottomPadding
                    : originalBottomPadding;
            if (scrollView.getPaddingBottom() != bottomPadding) {
                scrollView.setPadding(
                        scrollView.getPaddingLeft(),
                        scrollView.getPaddingTop(),
                        scrollView.getPaddingRight(),
                        bottomPadding
                );
            }
            if (keyboardVisible) {
                scrollFocusedViewWhenKeyboardVisible(scrollView, root, extraBottomPadding);
            }
        });
        root.getViewTreeObserver().addOnGlobalFocusChangeListener((oldFocus, newFocus) -> {
            if (newFocus != null && isDescendant(scrollView, newFocus)) {
                scrollFocusedViewWhenKeyboardVisible(scrollView, root, extraBottomPadding);
            }
        });
    }

    private int resolveKeyboardHeight(View root) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            WindowInsets insets = root.getRootWindowInsets();
            if (insets != null) {
                Insets imeInsets = insets.getInsets(WindowInsets.Type.ime());
                if (imeInsets.bottom > 0) {
                    return imeInsets.bottom;
                }
            }
        }
        Rect visibleFrame = new Rect();
        root.getWindowVisibleDisplayFrame(visibleFrame);
        return Math.max(0, root.getHeight() - visibleFrame.bottom);
    }

    private void scrollFocusedViewWhenKeyboardVisible(
            ScrollView scrollView,
            View root,
            int extraBottomPadding
    ) {
        int keyboardHeight = resolveKeyboardHeight(root);
        boolean keyboardVisible = keyboardHeight > root.getHeight() * KEYBOARD_VISIBLE_THRESHOLD;
        if (!keyboardVisible) {
            return;
        }
        scrollView.postDelayed(
                () -> scrollFocusedViewAboveKeyboard(scrollView, root, keyboardHeight, extraBottomPadding),
                80
        );
    }

    private void scrollFocusedViewAboveKeyboard(
            ScrollView scrollView,
            View root,
            int keyboardHeight,
            int extraBottomPadding
    ) {
        View focused = getCurrentFocus();
        if (focused == null || !isDescendant(scrollView, focused)) {
            return;
        }
        int[] rootLocation = new int[2];
        root.getLocationOnScreen(rootLocation);
        int[] focusedLocation = new int[2];
        focused.getLocationOnScreen(focusedLocation);
        int focusedBottom = focusedLocation[1] + focused.getHeight();
        int visibleBottom = rootLocation[1] + root.getHeight() - keyboardHeight - extraBottomPadding;
        if (focusedBottom > visibleBottom) {
            scrollView.smoothScrollBy(0, focusedBottom - visibleBottom);
        }
    }

    private boolean isDescendant(View parent, View child) {
        View current = child;
        while (current != null) {
            if (current == parent) {
                return true;
            }
            if (!(current.getParent() instanceof View)) {
                return false;
            }
            current = (View) current.getParent();
        }
        return false;
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
