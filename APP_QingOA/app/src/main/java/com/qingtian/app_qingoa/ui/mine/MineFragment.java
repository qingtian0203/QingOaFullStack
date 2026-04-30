package com.qingtian.app_qingoa.ui.mine;

import android.content.Intent;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import androidx.recyclerview.widget.LinearLayoutManager;

import com.qingtian.app_qingoa.base.BaseActivity;
import com.qingtian.app_qingoa.databinding.FragmentMineBinding;
import com.qingtian.app_qingoa.model.MenuData;
import com.qingtian.app_qingoa.model.UserInfo;
import com.qingtian.app_qingoa.net.ApiClient;
import com.qingtian.app_qingoa.net.ApiResponse;
import com.qingtian.app_qingoa.session.UserSession;
import com.qingtian.app_qingoa.ui.auth.LoginActivity;
import com.qingtian.app_qingoa.ui.punch.PunchCardActivity;
import com.qingtian.app_qingoa.ui.punch.PunchRecordListActivity;
import com.qingtian.app_qingoa.util.AppRouteWhitelist;
import com.qingtian.app_qingoa.util.ToastUtils;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * 我的 Fragment。
 * v1.5A 新增：动态功能入口区（调 /api/mine/menu），复用 MenuData 和白名单路由逻辑。
 */
public class MineFragment extends Fragment {

    private FragmentMineBinding mBinding;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater,
                             @Nullable ViewGroup container,
                             @Nullable Bundle savedInstanceState) {
        mBinding = FragmentMineBinding.inflate(inflater, container, false);
        return mBinding.getRoot();
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);

        // 优先用本地缓存展示，不等网络
        showUserInfo(UserSession.getInstance().getUserInfo());

        mBinding.btnLogout.setOnClickListener(v -> logout());

        // 加载"我的"动态功能入口
        loadMineMenu();
    }

    private void showUserInfo(UserInfo info) {
        if (info == null) return;
        mBinding.tvName.setText(info.getName() != null ? info.getName() : info.getUsername());
        mBinding.tvDept.setText(info.getDept() != null ? info.getDept() : "");
        mBinding.tvRole.setText(info.getRole() != null ? info.getRole() : "");
    }

    /** 调 /api/mine/menu，字段结构与 home/menu 完全一致，复用 MenuData + MenuAdapter */
    private void loadMineMenu() {
        ApiClient.getService().getMineMenu().enqueue(new Callback<ApiResponse<MenuData>>() {
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
                    if (body.isSuccess() && body.getData() != null
                            && body.getData().getMenus() != null) {
                        setupMineMenuList(body.getData());
                    }
                }
                mBinding.loadingMineMenu.setVisibility(View.GONE);
            }

            @Override
            public void onFailure(Call<ApiResponse<MenuData>> call, Throwable t) {
                if (isAdded()) mBinding.loadingMineMenu.setVisibility(View.GONE);
                // 我的菜单加载失败静默处理
            }
        });
    }

    private void setupMineMenuList(MenuData data) {
        mBinding.loadingMineMenu.setVisibility(View.GONE);
        mBinding.rvMineMenu.setVisibility(View.VISIBLE);
        // 纵向列表展示（与首页九宫格区分）
        mBinding.rvMineMenu.setLayoutManager(new LinearLayoutManager(requireContext()));
        mBinding.rvMineMenu.setAdapter(new MineMenuAdapter(data.getMenus(), item -> {
            if (!item.isEnabled()) {
                String reason = item.getDisabledReason() != null
                        ? item.getDisabledReason() : "功能暂未开放";
                ToastUtils.show(requireContext(), reason);
                return;
            }
            navigateMineTarget(item.getTarget());
        }));
    }

    /** 我的页路由，同样走白名单校验 */
    private void navigateMineTarget(String target) {
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
                ToastUtils.show(requireContext(), "功能开发中");
                break;
        }
    }

    private void logout() {
        ApiClient.getService().logout().enqueue(new Callback<ApiResponse<Void>>() {
            @Override
            public void onResponse(Call<ApiResponse<Void>> call,
                                   Response<ApiResponse<Void>> response) {
                doLocalLogout();
            }

            @Override
            public void onFailure(Call<ApiResponse<Void>> call, Throwable t) {
                // 网络失败也允许退出，客户端清除即可
                doLocalLogout();
            }
        });
    }

    private void doLocalLogout() {
        if (!isAdded()) return;
        UserSession.getInstance().clearSession();
        Intent intent = new Intent(requireContext(), LoginActivity.class);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        startActivity(intent);
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        mBinding = null;
    }
}
