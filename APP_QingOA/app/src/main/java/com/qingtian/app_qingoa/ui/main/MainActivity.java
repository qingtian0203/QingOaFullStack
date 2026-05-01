package com.qingtian.app_qingoa.ui.main;

import android.os.Bundle;

import androidx.fragment.app.Fragment;

import com.google.android.material.bottomnavigation.BottomNavigationView;
import com.qingtian.app_qingoa.R;
import com.qingtian.app_qingoa.base.BaseActivity;
import com.qingtian.app_qingoa.databinding.ActivityMainBinding;
import com.qingtian.app_qingoa.ui.home.HomeFragment;
import com.qingtian.app_qingoa.ui.mine.MineFragment;
import com.qingtian.app_qingoa.ui.okr.OkrFragment;

/**
 * 主页：管理底部导航和 Fragment 切换。
 * 使用 show/hide 方案复用 Fragment，避免重复请求数据。
 */
public class MainActivity extends BaseActivity {

    private ActivityMainBinding mBinding;
    private HomeFragment mHomeFragment;
    private OkrFragment mOkrFragment;
    private MineFragment mMineFragment;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        mBinding = ActivityMainBinding.inflate(getLayoutInflater());
        setContentView(mBinding.getRoot());

        initFragments();
        setupBottomNav();
    }

    private void initFragments() {
        mHomeFragment = new HomeFragment();
        mOkrFragment = new OkrFragment();
        mMineFragment = new MineFragment();

        getSupportFragmentManager().beginTransaction()
                .add(R.id.fragment_container, mHomeFragment, "home")
                .add(R.id.fragment_container, mOkrFragment, "okr")
                .add(R.id.fragment_container, mMineFragment, "mine")
                .hide(mOkrFragment)
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
            } else if (id == R.id.nav_mine) {
                showFragment(mMineFragment);
                return true;
            }
            return false;
        });
    }

    private void showFragment(Fragment show) {
        getSupportFragmentManager().beginTransaction()
                .show(show)
                .hide(show == mHomeFragment ? mOkrFragment : mHomeFragment)
                .hide(show == mMineFragment ? mOkrFragment : mMineFragment)
                .commit();
    }
}
