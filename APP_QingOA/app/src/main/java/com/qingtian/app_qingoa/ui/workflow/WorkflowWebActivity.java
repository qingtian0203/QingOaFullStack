package com.qingtian.app_qingoa.ui.workflow;

import android.annotation.SuppressLint;
import android.text.TextUtils;
import android.os.Bundle;
import android.view.View;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import com.qingtian.app_qingoa.BuildConfig;
import com.qingtian.app_qingoa.base.BaseActivity;
import com.qingtian.app_qingoa.databinding.ActivityWorkflowWebBinding;
import com.qingtian.app_qingoa.net.ApiClient;
import com.qingtian.app_qingoa.session.UserSession;

/** v1.6C：Native 入口承载 WAP 流程中心，并给页面注入获取 Token 的 JS Bridge。 */
public class WorkflowWebActivity extends BaseActivity {

    public static final String EXTRA_PATH = "workflow_path";
    private static final String DEFAULT_PATH = "/wap/#/workflow?tab=todo";
    private static final String DEFAULT_TITLE = "流程中心";
    private static final int MAX_TITLE_CHARS = 14;

    private ActivityWorkflowWebBinding mBinding;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        mBinding = ActivityWorkflowWebBinding.inflate(getLayoutInflater());
        setContentView(mBinding.getRoot());

        updateTitle(DEFAULT_TITLE);
        mBinding.btnBack.setOnClickListener(v -> navigateBack());
        WebView.setWebContentsDebuggingEnabled(BuildConfig.DEBUG);

        WebSettings settings = mBinding.webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE);
        mBinding.webView.addJavascriptInterface(new QingOABridge(), "QingOA");
        mBinding.webView.setWebViewClient(new WebViewClient());
        mBinding.webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onProgressChanged(WebView view, int newProgress) {
                mBinding.progressBar.setVisibility(newProgress >= 100 ? View.GONE : View.VISIBLE);
                mBinding.progressBar.setProgress(newProgress);
            }

            @Override
            public void onReceivedTitle(WebView view, String title) {
                super.onReceivedTitle(view, title);
                updateTitle(title);
            }
        });

        String path = getIntent().getStringExtra(EXTRA_PATH);
        mBinding.webView.loadUrl(ApiClient.resolveResourceUrl(path == null ? DEFAULT_PATH : path));
    }

    @Override
    public void onBackPressed() {
        navigateBack();
    }

    private void navigateBack() {
        if (mBinding != null && mBinding.webView.canGoBack()) {
            mBinding.webView.goBack();
            return;
        }
        finish();
    }

    private void updateTitle(String title) {
        if (TextUtils.isEmpty(title)) {
            return;
        }
        String normalized = title.trim();
        if (normalized.startsWith("http://")
                || normalized.startsWith("https://")
                || "about:blank".equals(normalized)) {
            return;
        }
        mBinding.tvTitle.setContentDescription(normalized);
        mBinding.tvTitle.setText(truncateTitle(normalized));
    }

    private String truncateTitle(String title) {
        if (title.codePointCount(0, title.length()) <= MAX_TITLE_CHARS) {
            return title;
        }
        int endIndex = title.offsetByCodePoints(0, MAX_TITLE_CHARS);
        return title.substring(0, endIndex) + "...";
    }

    public static class QingOABridge {
        @JavascriptInterface
        public String getToken() {
            String token = UserSession.getInstance().getToken();
            return token == null ? "" : token;
        }
    }
}
