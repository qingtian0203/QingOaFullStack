package com.qingtian.app_qingoa.ui.home;

import android.content.Intent;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import androidx.recyclerview.widget.GridLayoutManager;
import androidx.recyclerview.widget.LinearLayoutManager;

import com.qingtian.app_qingoa.base.BaseActivity;
import com.qingtian.app_qingoa.databinding.FragmentHomeBinding;
import com.qingtian.app_qingoa.model.MenuData;
import com.qingtian.app_qingoa.model.NoticeListData;
import com.qingtian.app_qingoa.net.ApiClient;
import com.qingtian.app_qingoa.net.ApiResponse;
import com.qingtian.app_qingoa.ui.punch.PunchCardActivity;
import com.qingtian.app_qingoa.util.ToastUtils;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * 首页 Fragment。
 * 加载九宫格菜单（服务端配置驱动灰显）和通知公告列表。
 * 菜单点击规则：enabled=true 跳转对应页面，enabled=false 弹 disabled_reason。
 */
public class HomeFragment extends Fragment {

    private FragmentHomeBinding mBinding;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater,
                             @Nullable ViewGroup container,
                             @Nullable Bundle savedInstanceState) {
        mBinding = FragmentHomeBinding.inflate(inflater, container, false);
        return mBinding.getRoot();
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        loadMenu();
        loadNotices();
    }

    private void loadMenu() {
        ApiClient.getService().getMenu().enqueue(new Callback<ApiResponse<MenuData>>() {
            @Override
            public void onResponse(Call<ApiResponse<MenuData>> call,
                                   Response<ApiResponse<MenuData>> response) {
                if (!isAdded()) return;
                if (response.isSuccessful() && response.body() != null) {
                    ApiResponse<MenuData> body = response.body();
                    if (body.isTokenExpired()) {
                        ((BaseActivity) requireActivity()).handleTokenExpired();
                        return;
                    }
                    if (body.isSuccess() && body.getData() != null) {
                        setupMenuGrid(body.getData());
                    }
                }
            }

            @Override
            public void onFailure(Call<ApiResponse<MenuData>> call, Throwable t) {
                if (isAdded()) {
                    ToastUtils.show(requireContext(), "菜单加载失败");
                }
            }
        });
    }

    private void setupMenuGrid(MenuData data) {
        // 3 列九宫格
        mBinding.rvMenu.setLayoutManager(new GridLayoutManager(requireContext(), 3));
        mBinding.rvMenu.setAdapter(new MenuAdapter(data.getMenus(), item -> {
            if (!item.isEnabled()) {
                // 灰显菜单：弹禁用原因
                String reason = item.getDisabledReason() != null
                        ? item.getDisabledReason() : "功能暂未开放";
                ToastUtils.show(requireContext(), reason);
                return;
            }
            // 根据 target 路由到对应页面
            navigateToTarget(item.getTarget());
        }));
    }

    /** 根据后台配置的 target 字符串跳转页面 */
    private void navigateToTarget(String target) {
        if ("PunchCardActivity".equals(target)) {
            startActivity(new Intent(requireContext(), PunchCardActivity.class));
        } else {
            ToastUtils.show(requireContext(), "页面未实现：" + target);
        }
    }

    private void loadNotices() {
        ApiClient.getService().getNotices(1, 10).enqueue(new Callback<ApiResponse<NoticeListData>>() {
            @Override
            public void onResponse(Call<ApiResponse<NoticeListData>> call,
                                   Response<ApiResponse<NoticeListData>> response) {
                if (!isAdded()) return;
                if (response.isSuccessful() && response.body() != null) {
                    ApiResponse<NoticeListData> body = response.body();
                    if (body.isSuccess() && body.getData() != null
                            && body.getData().getList() != null) {
                        mBinding.rvNotices.setLayoutManager(
                                new LinearLayoutManager(requireContext()));
                        mBinding.rvNotices.setAdapter(
                                new NoticeAdapter(body.getData().getList()));
                    }
                }
            }

            @Override
            public void onFailure(Call<ApiResponse<NoticeListData>> call, Throwable t) {
                // 公告加载失败静默处理，不影响主流程
            }
        });
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        mBinding = null;
    }
}
