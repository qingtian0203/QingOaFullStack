package com.qingtian.app_qingoa.ui.chat;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.qingtian.app_qingoa.databinding.ItemChatConversationBinding;
import com.qingtian.app_qingoa.model.ImConversationListData;
import com.qingtian.app_qingoa.model.ImMessageListData;
import com.qingtian.app_qingoa.model.ImUser;

import java.util.ArrayList;
import java.util.List;

public class ConversationAdapter extends RecyclerView.Adapter<ConversationAdapter.ViewHolder> {
    public interface OnItemClickListener {
        void onItemClick(ImConversationListData.Conversation item);
    }

    private final List<ImConversationListData.Conversation> mItems = new ArrayList<>();
    private final OnItemClickListener mListener;

    public ConversationAdapter(OnItemClickListener listener) {
        mListener = listener;
    }

    public void submit(List<ImConversationListData.Conversation> items) {
        mItems.clear();
        if (items != null) {
            mItems.addAll(items);
        }
        notifyDataSetChanged();
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        ItemChatConversationBinding binding = ItemChatConversationBinding.inflate(
                LayoutInflater.from(parent.getContext()), parent, false);
        return new ViewHolder(binding);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        ImConversationListData.Conversation item = mItems.get(position);
        ImUser peer = item.getPeer();
        String name = peer != null ? peer.displayName() : "未知用户";
        holder.binding.tvAvatar.setText(peer != null ? peer.initial() : "IM");
        holder.binding.tvName.setText(name);
        holder.binding.tvSummary.setText(summary(item.getLastMessage()));
        holder.binding.tvTime.setText(shortTime(item.getUpdatedAt()));
        int unread = item.getUnreadCount();
        holder.binding.tvUnread.setVisibility(unread > 0 ? View.VISIBLE : View.GONE);
        holder.binding.tvUnread.setText(unread > 99 ? "99+" : String.valueOf(unread));
        holder.itemView.setContentDescription("qingoa_chat_conversation_" + item.getId());
        holder.itemView.setOnClickListener(v -> {
            if (mListener != null) {
                mListener.onItemClick(item);
            }
        });
    }

    @Override
    public int getItemCount() {
        return mItems.size();
    }

    private String summary(ImMessageListData.Message message) {
        if (message == null) {
            return "暂无消息";
        }
        if (message.isImage()) {
            return "[图片]";
        }
        String content = message.getSummary();
        if (content == null || content.isEmpty()) {
            content = message.getContent();
        }
        return content == null || content.isEmpty() ? "新消息" : content;
    }

    private String shortTime(String value) {
        if (value == null) {
            return "";
        }
        return value.length() >= 16 ? value.substring(5, 16) : value;
    }

    static class ViewHolder extends RecyclerView.ViewHolder {
        final ItemChatConversationBinding binding;

        ViewHolder(ItemChatConversationBinding binding) {
            super(binding.getRoot());
            this.binding = binding;
        }
    }
}
