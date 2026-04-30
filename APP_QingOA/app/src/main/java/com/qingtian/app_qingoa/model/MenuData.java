package com.qingtian.app_qingoa.model;

import com.google.gson.annotations.SerializedName;

import java.util.List;

/** 首页菜单接口返回的 data 字段 */
public class MenuData {

    @SerializedName("menus")
    private List<MenuItem> menus;

    public List<MenuItem> getMenus() { return menus; }

    /** 单个菜单项 */
    public static class MenuItem {

        @SerializedName("id")
        private int id;

        @SerializedName("name")
        private String name;

        @SerializedName("icon")
        private String icon;

        @SerializedName("action")
        private String action;

        @SerializedName("target")
        private String target;

        /** 是否启用（false 表示灰显，点击弹 disabled_reason） */
        @SerializedName("enabled")
        private boolean enabled;

        @SerializedName("disabled_reason")
        private String disabledReason;

        public int getId() { return id; }
        public String getName() { return name; }
        public String getIcon() { return icon; }
        public String getAction() { return action; }
        public String getTarget() { return target; }
        public boolean isEnabled() { return enabled; }
        public String getDisabledReason() { return disabledReason; }
    }
}
