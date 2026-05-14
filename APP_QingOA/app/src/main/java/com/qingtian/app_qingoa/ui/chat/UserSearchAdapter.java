package com.qingtian.app_qingoa.ui.chat;

import android.view.LayoutInflater;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.qingtian.app_qingoa.databinding.ItemChatUserBinding;
import com.qingtian.app_qingoa.model.ImUser;

import java.util.ArrayList;
import java.util.List;

public class UserSearchAdapter extends RecyclerView.Adapter<UserSearchAdapter.ViewHolder> {
    public interface OnActionClickListener {
        void onActionClick(ImUser user);
    }

    private final List<ImUser> mItems = new ArrayList<>();
    private final OnActionClickListener mListener;

    public UserSearchAdapter(OnActionClickListener listener) {
        mListener = listener;
    }

    public void submit(List<ImUser> items) {
        mItems.clear();
        if (items != null) {
            mItems.addAll(items);
        }
        notifyDataSetChanged();
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        ItemChatUserBinding binding = ItemChatUserBinding.inflate(
                LayoutInflater.from(parent.getContext()), parent, false);
        return new ViewHolder(binding);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        ImUser user = mItems.get(position);
        holder.binding.tvAvatar.setText(user.initial());
        holder.binding.tvName.setText(user.displayName());
        holder.binding.tvSubtitle.setText(user.getUsername() + " · " + user.getRole());
        holder.binding.btnAction.setText(user.isFriend() ? "发起聊天" : "添加");
        holder.binding.btnAction.setContentDescription("qingoa_chat_user_action_" + user.getUsername());
        holder.itemView.setContentDescription("qingoa_chat_user_" + user.getUsername());
        holder.binding.btnAction.setOnClickListener(v -> {
            if (mListener != null) {
                mListener.onActionClick(user);
            }
        });
        holder.itemView.setOnClickListener(v -> {
            if (mListener != null) {
                mListener.onActionClick(user);
            }
        });
    }

    @Override
    public int getItemCount() {
        return mItems.size();
    }

    static class ViewHolder extends RecyclerView.ViewHolder {
        final ItemChatUserBinding binding;

        ViewHolder(ItemChatUserBinding binding) {
            super(binding.getRoot());
            this.binding = binding;
        }
    }
}
