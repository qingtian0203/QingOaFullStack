package com.qingtian.app_qingoa.util;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

/**
 * App 端动态菜单 target 白名单。
 *
 * 后端返回的 target 字符串必须在此白名单内，否则不跳转，
 * 显示 Toast "功能开发中"，防止随意反射跳转到未知 Activity。
 */
public class AppRouteWhitelist {

    private static final Set<String> ALLOWED_TARGETS = new HashSet<>(Arrays.asList(
            "PunchCardActivity",
            "PunchRecordListActivity",
            "PunchAppealActivity",
            "PunchAppealReviewActivity",
            "WorkflowWebActivity"
    ));

    /** 检查 target 是否在白名单内 */
    public static boolean isAllowed(String target) {
        return target != null && ALLOWED_TARGETS.contains(target);
    }

    private AppRouteWhitelist() { /* 工具类不实例化 */ }
}
