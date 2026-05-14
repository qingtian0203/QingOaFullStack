package com.qingtian.app_qingoa.ui.chat;

import android.content.Intent;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.inputmethod.EditorInfo;
import android.view.View;

import androidx.recyclerview.widget.LinearLayoutManager;

import com.qingtian.app_qingoa.base.BaseActivity;
import com.qingtian.app_qingoa.databinding.ActivityChatCreateBinding;
import com.qingtian.app_qingoa.model.ImConversationListData;
import com.qingtian.app_qingoa.model.ImUser;
import com.qingtian.app_qingoa.model.ImUserListData;
import com.qingtian.app_qingoa.net.AddFriendRequest;
import com.qingtian.app_qingoa.net.ApiClient;
import com.qingtian.app_qingoa.net.ApiResponse;
import com.qingtian.app_qingoa.net.SingleConversationRequest;
import com.qingtian.app_qingoa.util.ToastUtils;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class ChatCreateActivity extends BaseActivity {
    private ActivityChatCreateBinding mBinding;
    private UserSearchAdapter mAdapter;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        mBinding = ActivityChatCreateBinding.inflate(getLayoutInflater());
        setContentView(mBinding.getRoot());
        mBinding.btnBack.setOnClickListener(v -> finish());
        mAdapter = new UserSearchAdapter(this::handleUserAction);
        mBinding.rvUsers.setLayoutManager(new LinearLayoutManager(this));
        mBinding.rvUsers.setAdapter(mAdapter);
        mBinding.etKeyword.setOnEditorActionListener((v, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_SEARCH) {
                searchUsers();
                return true;
            }
            return false;
        });
        mBinding.etKeyword.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) {}
            @Override public void afterTextChanged(Editable s) { searchUsers(); }
        });
        searchUsers();
    }

    private void searchUsers() {
        String keyword = mBinding.etKeyword.getText().toString().trim();
        ApiClient.getService().searchImUsers(keyword, 20).enqueue(new Callback<ApiResponse<ImUserListData>>() {
            @Override
            public void onResponse(Call<ApiResponse<ImUserListData>> call,
                                   Response<ApiResponse<ImUserListData>> response) {
                if (response.isSuccessful() && response.body() != null) {
                    ApiResponse<ImUserListData> body = response.body();
                    if (body.isTokenExpired()) {
                        handleTokenExpired();
                        return;
                    }
                    if (body.isSuccess() && body.getData() != null) {
                        mAdapter.submit(body.getData().getList());
                        boolean empty = body.getData().getList() == null || body.getData().getList().isEmpty();
                        mBinding.tvEmpty.setVisibility(empty ? View.VISIBLE : View.GONE);
                        return;
                    }
                }
                ToastUtils.show(ChatCreateActivity.this, "搜索失败");
            }

            @Override
            public void onFailure(Call<ApiResponse<ImUserListData>> call, Throwable t) {
                ToastUtils.show(ChatCreateActivity.this, "搜索失败");
            }
        });
    }

    private void handleUserAction(ImUser user) {
        if (user.isFriend()) {
            createConversation(user);
            return;
        }
        ApiClient.getService().addImFriend(new AddFriendRequest(user.getUserId()))
                .enqueue(new Callback<ApiResponse<ImUser>>() {
                    @Override
                    public void onResponse(Call<ApiResponse<ImUser>> call, Response<ApiResponse<ImUser>> response) {
                        if (response.isSuccessful() && response.body() != null) {
                            ApiResponse<ImUser> body = response.body();
                            if (body.isTokenExpired()) {
                                handleTokenExpired();
                                return;
                            }
                            if (body.isSuccess()) {
                                createConversation(user);
                                return;
                            }
                            ToastUtils.show(ChatCreateActivity.this, body.getMsg());
                        }
                    }

                    @Override
                    public void onFailure(Call<ApiResponse<ImUser>> call, Throwable t) {
                        ToastUtils.show(ChatCreateActivity.this, "添加好友失败");
                    }
                });
    }

    private void createConversation(ImUser user) {
        ApiClient.getService().getOrCreateSingleConversation(new SingleConversationRequest(user.getUserId()))
                .enqueue(new Callback<ApiResponse<ImConversationListData.Conversation>>() {
                    @Override
                    public void onResponse(Call<ApiResponse<ImConversationListData.Conversation>> call,
                                           Response<ApiResponse<ImConversationListData.Conversation>> response) {
                        if (response.isSuccessful() && response.body() != null) {
                            ApiResponse<ImConversationListData.Conversation> body = response.body();
                            if (body.isTokenExpired()) {
                                handleTokenExpired();
                                return;
                            }
                            if (body.isSuccess() && body.getData() != null) {
                                Intent intent = new Intent(ChatCreateActivity.this, ChatDetailActivity.class);
                                intent.putExtra(ChatDetailActivity.EXTRA_CONVERSATION_ID, body.getData().getId());
                                intent.putExtra(ChatDetailActivity.EXTRA_PEER_NAME, user.displayName());
                                startActivity(intent);
                                finish();
                                return;
                            }
                            ToastUtils.show(ChatCreateActivity.this, body.getMsg());
                        }
                    }

                    @Override
                    public void onFailure(Call<ApiResponse<ImConversationListData.Conversation>> call, Throwable t) {
                        ToastUtils.show(ChatCreateActivity.this, "创建聊天失败");
                    }
                });
    }
}
