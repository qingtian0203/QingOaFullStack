package com.qingtian.app_qingoa.net;

import com.qingtian.app_qingoa.model.LoginData;
import com.qingtian.app_qingoa.model.MenuData;
import com.qingtian.app_qingoa.model.NoticeDetailData;
import com.qingtian.app_qingoa.model.NoticeListData;
import com.qingtian.app_qingoa.model.PunchRecordDetailData;
import com.qingtian.app_qingoa.model.PunchRecordListData;
import com.qingtian.app_qingoa.model.PunchResultData;
import com.qingtian.app_qingoa.model.PunchStatusData;
import com.qingtian.app_qingoa.model.UserInfo;

import retrofit2.Call;
import retrofit2.http.Body;
import retrofit2.http.GET;
import retrofit2.http.POST;
import retrofit2.http.Path;
import retrofit2.http.Query;

/**
 * Retrofit 接口定义。
 * Header 注入（Authorization: Bearer token）由 ApiClient 拦截器统一处理。
 */
public interface ApiService {

    // ────────── 认证模块 ──────────

    @POST("api/auth/login")
    Call<ApiResponse<LoginData>> login(@Body LoginRequest body);

    @POST("api/auth/logout")
    Call<ApiResponse<Void>> logout();

    /**
     * 双重职责：
     * 1. SplashActivity 启动时校验 Token
     * 2. MineFragment 展示用户信息
     */
    @GET("api/auth/user-info")
    Call<ApiResponse<UserInfo>> getUserInfo();

    // ────────── 首页模块 ──────────

    @GET("api/home/menu")
    Call<ApiResponse<MenuData>> getMenu();

    @GET("api/home/notices")
    Call<ApiResponse<NoticeListData>> getNotices(
            @Query("page") int page,
            @Query("size") int size
    );

    /** v1.5A 新增：通知详情 */
    @GET("api/notices/{id}")
    Call<ApiResponse<NoticeDetailData>> getNoticeDetail(@Path("id") int id);

    // ────────── 我的模块（v1.5A 新增） ──────────

    /** 我的页动态功能入口，字段结构与 home/menu 完全一致 */
    @GET("api/mine/menu")
    Call<ApiResponse<MenuData>> getMineMenu();

    // ────────── 打卡模块 ──────────

    @GET("api/punch/today-status")
    Call<ApiResponse<PunchStatusData>> getTodayStatus();

    /**
     * v1.5A 新增：统一打卡接口，替代旧的 /api/punch/clock-in。
     * 通过 PunchRequest.punchType 区分上班/下班卡。
     */
    @POST("api/punch/clock")
    Call<ApiResponse<PunchResultData>> clock(@Body PunchRequest body);

    /** @deprecated v1.5 起请使用 clock()，旧接口保留供兼容 */
    @Deprecated
    @POST("api/punch/clock-in")
    Call<ApiResponse<PunchResultData>> clockIn(@Body PunchRequest body);

    @GET("api/punch/records")
    Call<ApiResponse<PunchRecordListData>> getPunchRecords(
            @Query("page") int page,
            @Query("size") int size
    );

    /** v1.5A 新增：打卡详情 */
    @GET("api/punch/records/{id}")
    Call<ApiResponse<PunchRecordDetailData>> getPunchRecordDetail(@Path("id") int id);
}
