package com.qingtian.app_qingoa.ui.chat;

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
import com.qingtian.app_qingoa.databinding.FragmentChatBinding;
import com.qingtian.app_qingoa.model.ImConversationListData;
import com.qingtian.app_qingoa.net.ApiClient;
import com.qingtian.app_qingoa.net.ApiResponse;
import com.qingtian.app_qingoa.util.ToastUtils;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class ChatFragment extends Fragment {
    private FragmentChatBinding mBinding;
    private ConversationAdapter mAdapter;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater,
                             @Nullable ViewGroup container,
                             @Nullable Bundle savedInstanceState) {
        mBinding = FragmentChatBinding.inflate(inflater, container, false);
        return mBinding.getRoot();
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        mAdapter = new ConversationAdapter(this::openConversation);
        mBinding.rvConversations.setLayoutManager(new LinearLayoutManager(requireContext()));
        mBinding.rvConversations.setAdapter(mAdapter);
        mBinding.fabCreateChat.setOnClickListener(v ->
                startActivity(new Intent(requireContext(), ChatCreateActivity.class)));
    }

    @Override
    public void onResume() {
        super.onResume();
        loadConversations();
    }

    private void loadConversations() {
        if (mBinding == null) return;
        mBinding.progressBar.setVisibility(View.VISIBLE);
        ApiClient.getService().getImConversations().enqueue(new Callback<ApiResponse<ImConversationListData>>() {
            @Override
            public void onResponse(Call<ApiResponse<ImConversationListData>> call,
                                   Response<ApiResponse<ImConversationListData>> response) {
                if (!isAdded() || mBinding == null) return;
                mBinding.progressBar.setVisibility(View.GONE);
                if (response.isSuccessful() && response.body() != null) {
                    ApiResponse<ImConversationListData> body = response.body();
                    if (body.isTokenExpired()) {
                        ((BaseActivity) requireActivity()).handleTokenExpired();
                        return;
                    }
                    if (body.isSuccess() && body.getData() != null) {
                        mAdapter.submit(body.getData().getList());
                        boolean empty = body.getData().getList() == null || body.getData().getList().isEmpty();
                        mBinding.emptyState.setVisibility(empty ? View.VISIBLE : View.GONE);
                        return;
                    }
                }
                ToastUtils.show(requireContext(), "聊天列表加载失败");
            }

            @Override
            public void onFailure(Call<ApiResponse<ImConversationListData>> call, Throwable t) {
                if (!isAdded() || mBinding == null) return;
                mBinding.progressBar.setVisibility(View.GONE);
                ToastUtils.show(requireContext(), "聊天列表加载失败");
            }
        });
    }

    private void openConversation(ImConversationListData.Conversation item) {
        Intent intent = new Intent(requireContext(), ChatDetailActivity.class);
        intent.putExtra(ChatDetailActivity.EXTRA_CONVERSATION_ID, item.getId());
        if (item.getPeer() != null) {
            intent.putExtra(ChatDetailActivity.EXTRA_PEER_NAME, item.getPeer().displayName());
        }
        startActivity(intent);
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        mBinding = null;
    }
}
