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

import com.google.android.material.bottomsheet.BottomSheetDialog;
import com.qingtian.app_qingoa.databinding.DialogAvatarUrlBinding;
import com.qingtian.app_qingoa.databinding.DialogProfileEditBinding;
import com.qingtian.app_qingoa.base.BaseActivity;
import com.qingtian.app_qingoa.databinding.FragmentMineBinding;
import com.qingtian.app_qingoa.model.MenuData;
import com.qingtian.app_qingoa.model.UserInfo;
import com.qingtian.app_qingoa.net.AvatarUpdateRequest;
import com.qingtian.app_qingoa.net.ApiClient;
import com.qingtian.app_qingoa.net.ApiResponse;
import com.qingtian.app_qingoa.net.ProfileUpdateRequest;
import com.qingtian.app_qingoa.session.UserSession;
import com.qingtian.app_qingoa.ui.auth.LoginActivity;
import com.qingtian.app_qingoa.ui.punch.PunchCardActivity;
import com.qingtian.app_qingoa.ui.punch.PunchRecordListActivity;
import com.qingtian.app_qingoa.util.AppRouteWhitelist;
import com.qingtian.app_qingoa.util.AvatarLoader;
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
        mBinding.avatarContainer.setOnClickListener(v -> showAvatarDialog());
        mBinding.btnAvatar.setOnClickListener(v -> showAvatarDialog());
        mBinding.btnEditProfile.setOnClickListener(v -> showProfileDialog());

        // 加载"我的"动态功能入口
        loadMineMenu();
    }

    @Override
    public void onResume() {
        super.onResume();
        loadProfile();
    }

    private void showUserInfo(UserInfo info) {
        if (info == null) return;
        mBinding.tvName.setText(info.getName() != null ? info.getName() : info.getUsername());
        mBinding.tvDept.setText(info.getDept() != null ? info.getDept() : "");
        mBinding.tvRole.setText(info.getRole() != null ? info.getRole() : "");
        mBinding.tvAvatarInitial.setText(info.getInitial());
        mBinding.tvOfficeLocation.setText(prefix("办公地点", info.getOfficeLocation()));
        mBinding.tvPhone.setText(prefix("手机", info.getPhone()));
        mBinding.tvEmail.setText(prefix("邮箱", info.getEmail()));
        AvatarLoader.load(info.getAvatarUrl(), mBinding.ivAvatar, mBinding.tvAvatarInitial);
    }

    private void loadProfile() {
        ApiClient.getService().getUserProfile().enqueue(new Callback<ApiResponse<UserInfo>>() {
            @Override
            public void onResponse(Call<ApiResponse<UserInfo>> call,
                                   Response<ApiResponse<UserInfo>> response) {
                if (!isAdded()) return;
                if (response.isSuccessful() && response.body() != null) {
                    ApiResponse<UserInfo> body = response.body();
                    if (body.isTokenExpired()) {
                        ((BaseActivity) requireActivity()).handleTokenExpired();
                        return;
                    }
                    if (body.isSuccess() && body.getData() != null) {
                        UserSession.getInstance().updateUserInfo(body.getData());
                        showUserInfo(body.getData());
                    }
                }
            }

            @Override
            public void onFailure(Call<ApiResponse<UserInfo>> call, Throwable t) {
                // cache-then-network：失败时保留本地缓存，不打扰主流程
            }
        });
    }

    private void showProfileDialog() {
        UserInfo current = UserSession.getInstance().getUserInfo();
        DialogProfileEditBinding binding = DialogProfileEditBinding.inflate(getLayoutInflater());
        binding.etPhone.setText(current != null ? current.getPhone() : "");
        binding.etEmail.setText(current != null ? current.getEmail() : "");
        binding.etOfficeLocation.setText(current != null ? current.getOfficeLocation() : "");
        BottomSheetDialog dialog = new BottomSheetDialog(requireContext());
        dialog.setContentView(binding.getRoot());
        binding.btnSave.setOnClickListener(v -> updateProfile(
                text(binding.etPhone),
                text(binding.etEmail),
                text(binding.etOfficeLocation),
                dialog
        ));
        dialog.show();
    }

    private void updateProfile(String phone, String email, String officeLocation, BottomSheetDialog dialog) {
        ApiClient.getService()
                .updateUserProfile(new ProfileUpdateRequest(phone, email, officeLocation))
                .enqueue(new Callback<ApiResponse<UserInfo>>() {
                    @Override
                    public void onResponse(Call<ApiResponse<UserInfo>> call,
                                           Response<ApiResponse<UserInfo>> response) {
                        if (!isAdded()) return;
                        if (response.isSuccessful() && response.body() != null) {
                            ApiResponse<UserInfo> body = response.body();
                            if (body.isTokenExpired()) {
                                ((BaseActivity) requireActivity()).handleTokenExpired();
                                return;
                            }
                            if (body.isSuccess() && body.getData() != null) {
                                UserSession.getInstance().updateUserInfo(body.getData());
                                showUserInfo(body.getData());
                                dialog.dismiss();
                                ToastUtils.show(requireContext(), "资料已更新");
                                return;
                            }
                            ToastUtils.show(requireContext(), body.getMsg());
                        }
                    }

                    @Override
                    public void onFailure(Call<ApiResponse<UserInfo>> call, Throwable t) {
                        if (isAdded()) ToastUtils.show(requireContext(), "资料更新失败");
                    }
                });
    }

    private void showAvatarDialog() {
        UserInfo current = UserSession.getInstance().getUserInfo();
        DialogAvatarUrlBinding binding = DialogAvatarUrlBinding.inflate(getLayoutInflater());
        binding.etAvatarUrl.setText(current != null ? current.getAvatarUrl() : "");
        BottomSheetDialog dialog = new BottomSheetDialog(requireContext());
        dialog.setContentView(binding.getRoot());
        binding.btnSaveAvatar.setOnClickListener(v -> updateAvatar(text(binding.etAvatarUrl), dialog));
        dialog.show();
    }

    private void updateAvatar(String avatarUrl, BottomSheetDialog dialog) {
        if (avatarUrl.isEmpty()) {
            ToastUtils.show(requireContext(), "请输入头像图片地址");
            return;
        }
        ApiClient.getService()
                .updateAvatar(new AvatarUpdateRequest(avatarUrl))
                .enqueue(new Callback<ApiResponse<UserInfo>>() {
                    @Override
                    public void onResponse(Call<ApiResponse<UserInfo>> call,
                                           Response<ApiResponse<UserInfo>> response) {
                        if (!isAdded()) return;
                        if (response.isSuccessful() && response.body() != null) {
                            ApiResponse<UserInfo> body = response.body();
                            if (body.isTokenExpired()) {
                                ((BaseActivity) requireActivity()).handleTokenExpired();
                                return;
                            }
                            if (body.isSuccess() && body.getData() != null) {
                                UserSession.getInstance().updateUserInfo(body.getData());
                                showUserInfo(body.getData());
                                dialog.dismiss();
                                ToastUtils.show(requireContext(), "头像已更新");
                                return;
                            }
                            ToastUtils.show(requireContext(), body.getMsg());
                        }
                    }

                    @Override
                    public void onFailure(Call<ApiResponse<UserInfo>> call, Throwable t) {
                        if (isAdded()) ToastUtils.show(requireContext(), "头像更新失败");
                    }
                });
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

    private String prefix(String label, String value) {
        return label + "：" + (value != null && !value.isEmpty() ? value : "未填写");
    }

    private String text(android.widget.EditText editText) {
        return editText.getText() != null ? editText.getText().toString().trim() : "";
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        mBinding = null;
    }
}
