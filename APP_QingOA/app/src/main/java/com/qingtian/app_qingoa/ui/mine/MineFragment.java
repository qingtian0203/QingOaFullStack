package com.qingtian.app_qingoa.ui.mine;

import android.content.Intent;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;

import com.qingtian.app_qingoa.databinding.FragmentMineBinding;
import com.qingtian.app_qingoa.model.UserInfo;
import com.qingtian.app_qingoa.net.ApiClient;
import com.qingtian.app_qingoa.net.ApiResponse;
import com.qingtian.app_qingoa.session.UserSession;
import com.qingtian.app_qingoa.ui.auth.LoginActivity;
import com.qingtian.app_qingoa.util.ToastUtils;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * 我的 Fragment。
 * 展示用户信息（优先读内存缓存，无网络也能显示）。
 * 退出登录：调 /api/auth/logout → 清除 Session → 跳登录页。
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
    }

    private void showUserInfo(UserInfo info) {
        if (info == null) return;
        mBinding.tvName.setText(info.getName() != null ? info.getName() : info.getUsername());
        mBinding.tvDept.setText(info.getDept() != null ? info.getDept() : "");
        mBinding.tvRole.setText(info.getRole() != null ? info.getRole() : "");
    }

    private void logout() {
        // 先调登出接口（忽略失败，保证客户端一定能退出）
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

    /** 清除本地 Session，跳回登录页 */
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
