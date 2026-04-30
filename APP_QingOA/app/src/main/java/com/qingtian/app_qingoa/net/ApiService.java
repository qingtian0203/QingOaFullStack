package com.qingtian.app_qingoa.net;

import com.qingtian.app_qingoa.model.LoginData;
import com.qingtian.app_qingoa.model.UserInfo;
import com.qingtian.app_qingoa.model.MenuData;
import com.qingtian.app_qingoa.model.NoticeListData;
import com.qingtian.app_qingoa.model.PunchStatusData;
import com.qingtian.app_qingoa.model.PunchResultData;
import com.qingtian.app_qingoa.model.PunchRecordListData;

import retrofit2.Call;
import retrofit2.http.Body;
import retrofit2.http.GET;
import retrofit2.http.POST;
import retrofit2.http.Query;

/**
 * Retrofit 接口定义，对应后台所有业务接口。
 * Header 注入（Authorization: Bearer token）由 ApiClient 拦截器统一处理，这里无需声明。
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

    // ────────── 打卡模块 ──────────

    @GET("api/punch/today-status")
    Call<ApiResponse<PunchStatusData>> getTodayStatus();

    @POST("api/punch/clock-in")
    Call<ApiResponse<PunchResultData>> clockIn(@Body PunchRequest body);

    @GET("api/punch/records")
    Call<ApiResponse<PunchRecordListData>> getPunchRecords(
            @Query("page") int page,
            @Query("size") int size
    );
}
