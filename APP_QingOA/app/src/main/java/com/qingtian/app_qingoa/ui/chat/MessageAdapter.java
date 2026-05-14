package com.qingtian.app_qingoa.ui.chat;

import android.graphics.Color;
import android.view.Gravity;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.qingtian.app_qingoa.R;
import com.qingtian.app_qingoa.databinding.ItemChatMessageBinding;
import com.qingtian.app_qingoa.model.FileUploadData;
import com.qingtian.app_qingoa.model.ImMessageListData;
import com.qingtian.app_qingoa.util.ImageLoader;

import java.util.ArrayList;
import java.util.List;

public class MessageAdapter extends RecyclerView.Adapter<MessageAdapter.ViewHolder> {
    private final List<ImMessageListData.Message> mItems = new ArrayList<>();
    private int mCurrentUserId;

    public void setCurrentUserId(int currentUserId) {
        mCurrentUserId = currentUserId;
    }

    public void submit(List<ImMessageListData.Message> items) {
        mItems.clear();
        if (items != null) {
            mItems.addAll(items);
        }
        notifyDataSetChanged();
    }

    public int lastMessageId() {
        return mItems.isEmpty() ? 0 : mItems.get(mItems.size() - 1).getId();
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        ItemChatMessageBinding binding = ItemChatMessageBinding.inflate(
                LayoutInflater.from(parent.getContext()), parent, false);
        return new ViewHolder(binding);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        ImMessageListData.Message item = mItems.get(position);
        boolean mine = item.getSenderId() == mCurrentUserId;
        holder.binding.messageRow.setGravity(mine ? Gravity.END : Gravity.START);
        holder.binding.bubble.setBackgroundResource(mine ? R.drawable.bg_chat_bubble_self : R.drawable.bg_chat_bubble_other);
        holder.binding.tvTime.setText(shortTime(item.getCreatedAt()));
        holder.binding.tvTime.setTextColor(mine ? Color.parseColor("#EAF1FF") : holder.itemView.getResources().getColor(R.color.oa_text_muted));
        holder.binding.tvContent.setTextColor(mine ? Color.WHITE : holder.itemView.getResources().getColor(R.color.oa_text_primary));
        holder.itemView.setContentDescription("qingoa_chat_message_" + item.getId());
        if (item.isImage()) {
            holder.binding.tvContent.setText("[图片]");
            holder.binding.ivImage.setVisibility(View.VISIBLE);
            FileUploadData file = item.getFile();
            ImageLoader.load(file != null ? file.getUrl() : "", holder.binding.ivImage);
        } else {
            holder.binding.tvContent.setText(item.getContent());
            holder.binding.ivImage.setVisibility(View.GONE);
        }
    }

    @Override
    public int getItemCount() {
        return mItems.size();
    }

    private String shortTime(String value) {
        if (value == null) {
            return "";
        }
        return value.length() >= 16 ? value.substring(5, 16) : value;
    }

    static class ViewHolder extends RecyclerView.ViewHolder {
        final ItemChatMessageBinding binding;

        ViewHolder(ItemChatMessageBinding binding) {
            super(binding.getRoot());
            this.binding = binding;
        }
    }
}
