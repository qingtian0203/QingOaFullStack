package com.qingtian.app_qingoa.model;

import com.google.gson.annotations.SerializedName;

import java.util.List;

public class ImUserListData {
    @SerializedName("list")
    private List<ImUser> list;

    public List<ImUser> getList() { return list; }
}
