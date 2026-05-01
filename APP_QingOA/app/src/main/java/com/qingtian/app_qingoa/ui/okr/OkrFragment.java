package com.qingtian.app_qingoa.ui.okr;

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
import com.qingtian.app_qingoa.databinding.FragmentOkrBinding;
import com.qingtian.app_qingoa.model.OkrListData;
import com.qingtian.app_qingoa.net.ApiClient;
import com.qingtian.app_qingoa.net.ApiResponse;
import com.qingtian.app_qingoa.util.ToastUtils;

import java.util.List;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/** 底部 Tab 中的 OKR 工作台。 */
public class OkrFragment extends Fragment {

    private FragmentOkrBinding mBinding;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater,
                             @Nullable ViewGroup container,
                             @Nullable Bundle savedInstanceState) {
        mBinding = FragmentOkrBinding.inflate(inflater, container, false);
        return mBinding.getRoot();
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        mBinding.rvOkrs.setLayoutManager(new LinearLayoutManager(requireContext()));
        mBinding.fabCreate.setOnClickListener(v ->
                startActivity(new Intent(requireContext(), OkrCreateActivity.class)));
    }

    @Override
    public void onResume() {
        super.onResume();
        if (mBinding != null) {
            loadOkrs();
        }
    }

    private void loadOkrs() {
        showLoading(true);
        ApiClient.getService().getOkrList(null).enqueue(new Callback<ApiResponse<OkrListData>>() {
            @Override
            public void onResponse(Call<ApiResponse<OkrListData>> call,
                                   Response<ApiResponse<OkrListData>> response) {
                if (!isAdded() || mBinding == null) return;
                showLoading(false);
                if (response.isSuccessful() && response.body() != null) {
                    ApiResponse<OkrListData> body = response.body();
                    if (body.isTokenExpired()) {
                        ((BaseActivity) requireActivity()).handleTokenExpired();
                        return;
                    }
                    if (body.isSuccess() && body.getData() != null) {
                        setupList(body.getData().getList());
                        return;
                    }
                    ToastUtils.show(requireContext(), body.getMsg());
                }
            }

            @Override
            public void onFailure(Call<ApiResponse<OkrListData>> call, Throwable t) {
                if (!isAdded() || mBinding == null) return;
                showLoading(false);
                ToastUtils.show(requireContext(), "加载 OKR 失败");
            }
        });
    }

    private void setupList(List<OkrListData.OkrItem> list) {
        boolean empty = list == null || list.isEmpty();
        mBinding.emptyState.setVisibility(empty ? View.VISIBLE : View.GONE);
        mBinding.rvOkrs.setVisibility(empty ? View.GONE : View.VISIBLE);
        if (!empty) {
            mBinding.rvOkrs.setAdapter(new OkrAdapter(list, item -> {
                Intent intent = new Intent(requireContext(), OkrDetailActivity.class);
                intent.putExtra(OkrDetailActivity.EXTRA_OKR_ID, item.getId());
                startActivity(intent);
            }));
        }
    }

    private void showLoading(boolean loading) {
        mBinding.progressBar.setVisibility(loading ? View.VISIBLE : View.GONE);
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        mBinding = null;
    }
}
