package com.qingtian.app_qingoa.ui.main;

import android.os.Bundle;

import androidx.core.content.ContextCompat;
import androidx.fragment.app.Fragment;

import com.google.android.material.badge.BadgeDrawable;
import com.qingtian.app_qingoa.R;
import com.qingtian.app_qingoa.base.BaseActivity;
import com.qingtian.app_qingoa.databinding.ActivityMainBinding;
import com.qingtian.app_qingoa.model.BadgeSummaryData;
import com.qingtian.app_qingoa.net.ApiClient;
import com.qingtian.app_qingoa.net.ApiResponse;
import com.qingtian.app_qingoa.ui.chat.ChatFragment;
import com.qingtian.app_qingoa.ui.home.HomeFragment;
import com.qingtian.app_qingoa.ui.mine.MineFragment;
import com.qingtian.app_qingoa.ui.okr.OkrFragment;

import java.util.ArrayList;
import java.util.List;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * 主页：管理底部导航和 Fragment 切换。
 * 使用 show/hide 方案复用 Fragment，避免重复请求数据。
 */
public class MainActivity extends BaseActivity {

    private ActivityMainBinding mBinding;
    private HomeFragment mHomeFragment;
    private OkrFragment mOkrFragment;
    private ChatFragment mChatFragment;
    private MineFragment mMineFragment;
    private final List<Fragment> mFragments = new ArrayList<>();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        mBinding = ActivityMainBinding.inflate(getLayoutInflater());
        setContentView(mBinding.getRoot());

        initFragments();
        setupBottomNav();
        setupAutomationLabels();
    }

    @Override
    protected void onResume() {
        super.onResume();
        loadBadgeSummary();
    }

    private void initFragments() {
        mHomeFragment = new HomeFragment();
        mOkrFragment = new OkrFragment();
        mChatFragment = new ChatFragment();
        mMineFragment = new MineFragment();
        mFragments.add(mHomeFragment);
        mFragments.add(mOkrFragment);
        mFragments.add(mChatFragment);
        mFragments.add(mMineFragment);

        getSupportFragmentManager().beginTransaction()
                .add(R.id.fragment_container, mHomeFragment, "home")
                .add(R.id.fragment_container, mOkrFragment, "okr")
                .add(R.id.fragment_container, mChatFragment, "chat")
                .add(R.id.fragment_container, mMineFragment, "mine")
                .hide(mOkrFragment)
                .hide(mChatFragment)
                .hide(mMineFragment)
                .commit();
    }

    private void setupBottomNav() {
        mBinding.bottomNav.setOnItemSelectedListener(item -> {
            int id = item.getItemId();
            if (id == R.id.nav_home) {
                showFragment(mHomeFragment);
                return true;
            } else if (id == R.id.nav_okr) {
                showFragment(mOkrFragment);
                return true;
            } else if (id == R.id.nav_chat) {
                showFragment(mChatFragment);
                return true;
            } else if (id == R.id.nav_mine) {
                showFragment(mMineFragment);
                return true;
            }
            return false;
        });
    }

    private void setupAutomationLabels() {
        mBinding.bottomNav.getMenu().findItem(R.id.nav_home).setContentDescription("qingoa_bottom_tab_home");
        mBinding.bottomNav.getMenu().findItem(R.id.nav_okr).setContentDescription("qingoa_bottom_tab_okr");
        mBinding.bottomNav.getMenu().findItem(R.id.nav_chat).setContentDescription("qingoa_bottom_tab_chat");
        mBinding.bottomNav.getMenu().findItem(R.id.nav_mine).setContentDescription("qingoa_bottom_tab_mine");
    }

    private void showFragment(Fragment show) {
        androidx.fragment.app.FragmentTransaction transaction = getSupportFragmentManager().beginTransaction();
        for (Fragment fragment : mFragments) {
            if (fragment == show) {
                transaction.show(fragment);
            } else {
                transaction.hide(fragment);
            }
        }
        transaction.commit();
    }

    private void loadBadgeSummary() {
        ApiClient.getService().getBadgeSummary().enqueue(new Callback<ApiResponse<BadgeSummaryData>>() {
            @Override
            public void onResponse(Call<ApiResponse<BadgeSummaryData>> call,
                                   Response<ApiResponse<BadgeSummaryData>> response) {
                if (response.isSuccessful() && response.body() != null) {
                    ApiResponse<BadgeSummaryData> body = response.body();
                    if (body.isTokenExpired()) {
                        handleTokenExpired();
                        return;
                    }
                    if (body.isSuccess() && body.getData() != null) {
                        updateChatBadge(body.getData().imUnreadTotal());
                    }
                }
            }

            @Override
            public void onFailure(Call<ApiResponse<BadgeSummaryData>> call, Throwable t) {
                updateChatBadge(0);
            }
        });
    }

    private void updateChatBadge(int count) {
        BadgeDrawable badge = mBinding.bottomNav.getOrCreateBadge(R.id.nav_chat);
        badge.setBadgeGravity(BadgeDrawable.TOP_END);
        badge.setBackgroundColor(ContextCompat.getColor(this, R.color.oa_primary));
        badge.setBadgeTextColor(ContextCompat.getColor(this, R.color.white));
        badge.setMaxCharacterCount(3);
        badge.setHorizontalOffset(-dp(6));
        badge.setVerticalOffset(dp(8));
        if (count <= 0) {
            badge.setVisible(false);
            badge.clearNumber();
            return;
        }
        badge.setVisible(true);
        badge.setNumber(count);
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
