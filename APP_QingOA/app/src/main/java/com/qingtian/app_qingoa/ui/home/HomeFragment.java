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
import com.qingtian.app_qingoa.ui.punch.PunchRecordListActivity;
import com.qingtian.app_qingoa.util.AppRouteWhitelist;
import com.qingtian.app_qingoa.util.ToastUtils;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * 首页 Fragment。
 * - 九宫格菜单：服务端配置驱动，enabled=false 弹禁用原因，target 必须在白名单内
 * - 公告列表：点击任意一条进通知详情（不依赖菜单 enabled）
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
                if (isAdded()) ToastUtils.show(requireContext(), "菜单加载失败");
            }
        });
    }

    private void setupMenuGrid(MenuData data) {
        mBinding.rvMenu.setLayoutManager(new GridLayoutManager(requireContext(), 3));
        mBinding.rvMenu.setAdapter(new MenuAdapter(data.getMenus(), item -> {
            if (!item.isEnabled()) {
                String reason = item.getDisabledReason() != null
                        ? item.getDisabledReason() : "功能暂未开放";
                ToastUtils.show(requireContext(), reason);
                return;
            }
            navigateToTarget(item.getTarget());
        }));
    }

    /**
     * 根据白名单路由到目标页面。
     * 不在白名单内的 target 弹 Toast "功能开发中"，防止任意跳转。
     */
    private void navigateToTarget(String target) {
        if (!AppRouteWhitelist.isAllowed(target)) {
            ToastUtils.show(requireContext(), "功能开发中");
            return;
        }
        switch (target) {
            case "PunchCardActivity":
                startActivity(new Intent(requireContext(), PunchCardActivity.class));
                break;
            case "PunchRecordListActivity":
                startActivity(new Intent(requireContext(), PunchRecordListActivity.class));
                break;
            default:
                // 白名单内但 App 尚未实现的页面（如 OkrListActivity 等 v1.5B 的）
                ToastUtils.show(requireContext(), "功能开发中");
                break;
        }
    }

    private void loadNotices() {
        ApiClient.getService().getNotices(1, 10)
                .enqueue(new Callback<ApiResponse<NoticeListData>>() {
                    @Override
                    public void onResponse(Call<ApiResponse<NoticeListData>> call,
                                           Response<ApiResponse<NoticeListData>> response) {
                        if (!isAdded()) return;
                        if (response.isSuccessful() && response.body() != null) {
                            ApiResponse<NoticeListData> body = response.body();
                            if (body.isSuccess() && body.getData() != null
                                    && body.getData().getList() != null) {
                                setupNoticeList(body.getData());
                            }
                        }
                    }

                    @Override
                    public void onFailure(Call<ApiResponse<NoticeListData>> call, Throwable t) {
                        // 公告加载失败静默处理，不影响主流程
                    }
                });
    }

    /**
     * 公告列表：点击跳通知详情，路径独立，不依赖菜单 enabled。
     */
    private void setupNoticeList(NoticeListData data) {
        mBinding.rvNotices.setLayoutManager(new LinearLayoutManager(requireContext()));
        mBinding.rvNotices.setAdapter(new NoticeAdapter(data.getList(), item -> {
            Intent intent = new Intent(requireContext(), NoticeDetailActivity.class);
            intent.putExtra("notice_id", item.getId());
            startActivity(intent);
        }));
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        mBinding = null;
    }
}
