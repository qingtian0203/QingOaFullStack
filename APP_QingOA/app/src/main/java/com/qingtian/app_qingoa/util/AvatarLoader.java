package com.qingtian.app_qingoa.util;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.widget.ImageView;
import android.widget.TextView;

import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** v1.6A：轻量头像加载器，避免为了演示 App 引入完整图片库。 */
public final class AvatarLoader {

    private static final ExecutorService EXECUTOR = Executors.newSingleThreadExecutor();
    private static final Handler MAIN = new Handler(Looper.getMainLooper());

    private AvatarLoader() {}

    public static void load(String avatarUrl, ImageView imageView, TextView fallbackView) {
        if (avatarUrl == null || avatarUrl.trim().isEmpty()) {
            showFallback(imageView, fallbackView);
            return;
        }
        String url = avatarUrl.trim();
        imageView.setTag(url);
        EXECUTOR.execute(() -> {
            Bitmap bitmap = null;
            try {
                HttpURLConnection connection = (HttpURLConnection) new URL(url).openConnection();
                connection.setConnectTimeout(5000);
                connection.setReadTimeout(5000);
                connection.setInstanceFollowRedirects(true);
                try (InputStream input = connection.getInputStream()) {
                    bitmap = BitmapFactory.decodeStream(input);
                } finally {
                    connection.disconnect();
                }
            } catch (Exception ignored) {
                bitmap = null;
            }
            Bitmap finalBitmap = bitmap;
            MAIN.post(() -> {
                Object tag = imageView.getTag();
                if (!(tag instanceof String) || !url.equals(tag)) {
                    return;
                }
                if (finalBitmap != null) {
                    imageView.setImageBitmap(finalBitmap);
                    imageView.setVisibility(View.VISIBLE);
                    fallbackView.setVisibility(View.GONE);
                } else {
                    showFallback(imageView, fallbackView);
                }
            });
        });
    }

    public static void showFallback(ImageView imageView, TextView fallbackView) {
        imageView.setTag(null);
        imageView.setImageDrawable(null);
        imageView.setVisibility(View.GONE);
        fallbackView.setVisibility(View.VISIBLE);
    }
}
