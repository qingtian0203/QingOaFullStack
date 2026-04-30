package com.qingtian.app_qingoa.util;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import android.widget.Toast;

/** 统一 Toast 工具，支持从非主线程调用 */
public class ToastUtils {

    private static final Handler sMainHandler = new Handler(Looper.getMainLooper());

    private ToastUtils() {}

    public static void show(Context context, String message) {
        if (Looper.myLooper() == Looper.getMainLooper()) {
            Toast.makeText(context.getApplicationContext(), message, Toast.LENGTH_SHORT).show();
        } else {
            // 网络回调在子线程，切回主线程显示
            sMainHandler.post(() ->
                    Toast.makeText(context.getApplicationContext(), message, Toast.LENGTH_SHORT).show()
            );
        }
    }

    public static void showLong(Context context, String message) {
        if (Looper.myLooper() == Looper.getMainLooper()) {
            Toast.makeText(context.getApplicationContext(), message, Toast.LENGTH_LONG).show();
        } else {
            sMainHandler.post(() ->
                    Toast.makeText(context.getApplicationContext(), message, Toast.LENGTH_LONG).show()
            );
        }
    }
}
