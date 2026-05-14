package com.qingtian.app_qingoa.ui.chat;

import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;

import androidx.annotation.Nullable;
import androidx.recyclerview.widget.LinearLayoutManager;

import com.qingtian.app_qingoa.base.BaseActivity;
import com.qingtian.app_qingoa.databinding.ActivityChatDetailBinding;
import com.qingtian.app_qingoa.model.FileUploadData;
import com.qingtian.app_qingoa.model.ImMessageListData;
import com.qingtian.app_qingoa.net.ApiClient;
import com.qingtian.app_qingoa.net.ApiResponse;
import com.qingtian.app_qingoa.net.MarkReadRequest;
import com.qingtian.app_qingoa.net.SendImMessageRequest;
import com.qingtian.app_qingoa.session.UserSession;
import com.qingtian.app_qingoa.util.ToastUtils;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;

import okhttp3.MediaType;
import okhttp3.MultipartBody;
import okhttp3.RequestBody;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class ChatDetailActivity extends BaseActivity {
    public static final String EXTRA_CONVERSATION_ID = "conversation_id";
    public static final String EXTRA_PEER_NAME = "peer_name";
    private static final int REQUEST_PICK_IMAGE = 81;
    private static final long POLL_INTERVAL_MS = 5000L;

    private ActivityChatDetailBinding mBinding;
    private MessageAdapter mAdapter;
    private int mConversationId;
    private final Handler mHandler = new Handler(Looper.getMainLooper());
    private boolean mPolling;
    private final Runnable mPollTask = new Runnable() {
        @Override
        public void run() {
            if (!mPolling) return;
            loadMessages(false);
            mHandler.postDelayed(this, POLL_INTERVAL_MS);
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        mBinding = ActivityChatDetailBinding.inflate(getLayoutInflater());
        setContentView(mBinding.getRoot());
        mConversationId = getIntent().getIntExtra(EXTRA_CONVERSATION_ID, 0);
        String peerName = getIntent().getStringExtra(EXTRA_PEER_NAME);
        mBinding.tvTitle.setText(peerName != null ? peerName : "聊天");
        mBinding.btnBack.setOnClickListener(v -> finish());

        mAdapter = new MessageAdapter();
        if (UserSession.getInstance().getUserInfo() != null) {
            mAdapter.setCurrentUserId(UserSession.getInstance().getUserInfo().getUserId());
        }
        LinearLayoutManager layoutManager = new LinearLayoutManager(this);
        mBinding.rvMessages.setLayoutManager(layoutManager);
        mBinding.rvMessages.setAdapter(mAdapter);
        mBinding.btnSend.setOnClickListener(v -> sendText());
        mBinding.btnImage.setOnClickListener(v -> pickImage());
        loadMessages(true);
    }

    @Override
    protected void onResume() {
        super.onResume();
        startPolling();
    }

    @Override
    protected void onPause() {
        super.onPause();
        stopPolling();
    }

    @Override
    protected void onDestroy() {
        stopPolling();
        super.onDestroy();
    }

    private void startPolling() {
        if (mPolling) return;
        mPolling = true;
        mHandler.postDelayed(mPollTask, POLL_INTERVAL_MS);
    }

    private void stopPolling() {
        mPolling = false;
        mHandler.removeCallbacks(mPollTask);
    }

    private void loadMessages(boolean scrollToBottom) {
        if (mConversationId <= 0) return;
        ApiClient.getService().getImMessages(mConversationId, 100)
                .enqueue(new Callback<ApiResponse<ImMessageListData>>() {
                    @Override
                    public void onResponse(Call<ApiResponse<ImMessageListData>> call,
                                           Response<ApiResponse<ImMessageListData>> response) {
                        if (response.isSuccessful() && response.body() != null) {
                            ApiResponse<ImMessageListData> body = response.body();
                            if (body.isTokenExpired()) {
                                handleTokenExpired();
                                return;
                            }
                            if (body.isSuccess() && body.getData() != null) {
                                mAdapter.submit(body.getData().getList());
                                markRead(mAdapter.lastMessageId());
                                if (scrollToBottom && mAdapter.getItemCount() > 0) {
                                    mBinding.rvMessages.scrollToPosition(Math.max(0, mAdapter.getItemCount() - 1));
                                }
                            }
                        }
                    }

                    @Override
                    public void onFailure(Call<ApiResponse<ImMessageListData>> call, Throwable t) {
                        ToastUtils.show(ChatDetailActivity.this, "消息加载失败");
                    }
                });
    }

    private void markRead(int lastMessageId) {
        if (lastMessageId <= 0) return;
        ApiClient.getService().markImRead(mConversationId, new MarkReadRequest(lastMessageId))
                .enqueue(new Callback<ApiResponse<Void>>() {
                    @Override public void onResponse(Call<ApiResponse<Void>> call, Response<ApiResponse<Void>> response) {}
                    @Override public void onFailure(Call<ApiResponse<Void>> call, Throwable t) {}
                });
    }

    private void sendText() {
        String content = mBinding.etMessage.getText().toString().trim();
        if (content.isEmpty()) {
            ToastUtils.show(this, "消息不能为空");
            return;
        }
        mBinding.btnSend.setEnabled(false);
        ApiClient.getService().sendImMessage(mConversationId, SendImMessageRequest.text(content))
                .enqueue(new Callback<ApiResponse<ImMessageListData.Message>>() {
                    @Override
                    public void onResponse(Call<ApiResponse<ImMessageListData.Message>> call,
                                           Response<ApiResponse<ImMessageListData.Message>> response) {
                        mBinding.btnSend.setEnabled(true);
                        if (response.isSuccessful() && response.body() != null) {
                            ApiResponse<ImMessageListData.Message> body = response.body();
                            if (body.isTokenExpired()) {
                                handleTokenExpired();
                                return;
                            }
                            if (body.isSuccess()) {
                                mBinding.etMessage.setText("");
                                loadMessages(true);
                                return;
                            }
                            ToastUtils.show(ChatDetailActivity.this, body.getMsg());
                        }
                    }

                    @Override
                    public void onFailure(Call<ApiResponse<ImMessageListData.Message>> call, Throwable t) {
                        mBinding.btnSend.setEnabled(true);
                        ToastUtils.show(ChatDetailActivity.this, "发送失败");
                    }
                });
    }

    private void pickImage() {
        Intent intent = new Intent(Intent.ACTION_GET_CONTENT);
        intent.setType("image/*");
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        startActivityForResult(Intent.createChooser(intent, "选择图片"), REQUEST_PICK_IMAGE);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == REQUEST_PICK_IMAGE && resultCode == RESULT_OK && data != null && data.getData() != null) {
            uploadImage(data.getData());
        }
    }

    private void uploadImage(Uri uri) {
        try {
            String mime = getContentResolver().getType(uri);
            if (mime == null || mime.trim().isEmpty()) {
                mime = "image/png";
            }
            byte[] bytes = readBytes(uri);
            RequestBody fileBody = RequestBody.create(MediaType.parse(mime), bytes);
            MultipartBody.Part part = MultipartBody.Part.createFormData("file", "chat_image.png", fileBody);
            RequestBody usage = RequestBody.create(MediaType.parse("text/plain"), "im_image");
            mBinding.btnImage.setEnabled(false);
            ApiClient.getService().uploadFile(part, usage)
                    .enqueue(new Callback<ApiResponse<FileUploadData>>() {
                        @Override
                        public void onResponse(Call<ApiResponse<FileUploadData>> call,
                                               Response<ApiResponse<FileUploadData>> response) {
                            mBinding.btnImage.setEnabled(true);
                            if (response.isSuccessful() && response.body() != null) {
                                ApiResponse<FileUploadData> body = response.body();
                                if (body.isTokenExpired()) {
                                    handleTokenExpired();
                                    return;
                                }
                                if (body.isSuccess() && body.getData() != null) {
                                    sendImage(body.getData().getFileId());
                                    return;
                                }
                                ToastUtils.show(ChatDetailActivity.this, body.getMsg());
                            }
                        }

                        @Override
                        public void onFailure(Call<ApiResponse<FileUploadData>> call, Throwable t) {
                            mBinding.btnImage.setEnabled(true);
                            ToastUtils.show(ChatDetailActivity.this, "图片上传失败");
                        }
                    });
        } catch (Exception e) {
            ToastUtils.show(this, "图片读取失败");
        }
    }

    private void sendImage(String fileId) {
        ApiClient.getService().sendImMessage(mConversationId, SendImMessageRequest.image(fileId))
                .enqueue(new Callback<ApiResponse<ImMessageListData.Message>>() {
                    @Override
                    public void onResponse(Call<ApiResponse<ImMessageListData.Message>> call,
                                           Response<ApiResponse<ImMessageListData.Message>> response) {
                        if (response.isSuccessful() && response.body() != null) {
                            ApiResponse<ImMessageListData.Message> body = response.body();
                            if (body.isTokenExpired()) {
                                handleTokenExpired();
                                return;
                            }
                            if (body.isSuccess()) {
                                loadMessages(true);
                                return;
                            }
                            ToastUtils.show(ChatDetailActivity.this, body.getMsg());
                        }
                    }

                    @Override
                    public void onFailure(Call<ApiResponse<ImMessageListData.Message>> call, Throwable t) {
                        ToastUtils.show(ChatDetailActivity.this, "图片发送失败");
                    }
                });
    }

    private byte[] readBytes(Uri uri) throws Exception {
        try (InputStream input = getContentResolver().openInputStream(uri);
             ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            if (input == null) {
                throw new IllegalStateException("image input is null");
            }
            byte[] buffer = new byte[8 * 1024];
            int read;
            while ((read = input.read(buffer)) != -1) {
                output.write(buffer, 0, read);
            }
            return output.toByteArray();
        }
    }
}
