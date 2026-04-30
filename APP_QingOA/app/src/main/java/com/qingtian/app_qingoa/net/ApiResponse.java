package com.qingtian.app_qingoa.net;

/**
 * 统一接口响应包装类。
 * 对应后台 {"code":0,"msg":"success","data":{}} 格式。
 * @param <T> 业务数据类型
 */
public class ApiResponse<T> {

    /** 0=成功，非0=失败 */
    private int code;
    private String msg;
    private T data;

    public int getCode() { return code; }
    public String getMsg() { return msg; }
    public T getData() { return data; }

    /** 是否成功 */
    public boolean isSuccess() { return code == 0; }

    /** Token 是否过期（App 收到后需跳登录页） */
    public boolean isTokenExpired() { return code == 1002; }
}
