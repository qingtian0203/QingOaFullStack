package com.qingtian.app_qingoa.util;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.os.Handler;
import android.os.Looper;
import android.util.LruCache;
import android.view.View;
import android.widget.ImageView;

import com.qingtian.app_qingoa.net.ApiClient;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** 简单矩形图片加载器，用于 IM 图片缩略图。 */
public final class ImageLoader {
    private static final int TARGET_SIZE = 640;
    private static final ExecutorService EXECUTOR = Executors.newFixedThreadPool(2);
    private static final Handler MAIN = new Handler(Looper.getMainLooper());
    private static final LruCache<String, Bitmap> CACHE = new LruCache<String, Bitmap>(8 * 1024 * 1024) {
        @Override
        protected int sizeOf(String key, Bitmap value) {
            return value.getByteCount();
        }
    };

    private ImageLoader() {}

    public static void load(String path, ImageView imageView) {
        if (path == null || path.trim().isEmpty()) {
            imageView.setVisibility(View.GONE);
            return;
        }
        String url = ApiClient.resolveResourceUrl(path.trim());
        imageView.setTag(url);
        Bitmap cached = CACHE.get(url);
        if (cached != null) {
            imageView.setImageBitmap(cached);
            imageView.setVisibility(View.VISIBLE);
            return;
        }
        imageView.setVisibility(View.VISIBLE);
        EXECUTOR.execute(() -> {
            Bitmap bitmap = null;
            try {
                HttpURLConnection connection = (HttpURLConnection) new URL(url).openConnection();
                connection.setConnectTimeout(5000);
                connection.setReadTimeout(5000);
                try (InputStream input = connection.getInputStream()) {
                    bitmap = decode(readBytes(input));
                } finally {
                    connection.disconnect();
                }
            } catch (Exception ignored) {
                bitmap = null;
            }
            Bitmap finalBitmap = bitmap;
            if (finalBitmap != null) {
                CACHE.put(url, finalBitmap);
            }
            MAIN.post(() -> {
                Object tag = imageView.getTag();
                if (!(tag instanceof String) || !url.equals(tag)) {
                    return;
                }
                if (finalBitmap != null) {
                    imageView.setImageBitmap(finalBitmap);
                    imageView.setVisibility(View.VISIBLE);
                } else {
                    imageView.setVisibility(View.VISIBLE);
                }
            });
        });
    }

    private static Bitmap decode(byte[] bytes) {
        BitmapFactory.Options bounds = new BitmapFactory.Options();
        bounds.inJustDecodeBounds = true;
        BitmapFactory.decodeByteArray(bytes, 0, bytes.length, bounds);
        BitmapFactory.Options options = new BitmapFactory.Options();
        options.inSampleSize = sampleSize(bounds.outWidth, bounds.outHeight);
        return BitmapFactory.decodeByteArray(bytes, 0, bytes.length, options);
    }

    private static int sampleSize(int width, int height) {
        int sample = 1;
        while (width / sample > TARGET_SIZE || height / sample > TARGET_SIZE) {
            sample *= 2;
        }
        return sample;
    }

    private static byte[] readBytes(InputStream input) throws Exception {
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        byte[] buffer = new byte[8 * 1024];
        int read;
        while ((read = input.read(buffer)) != -1) {
            output.write(buffer, 0, read);
        }
        return output.toByteArray();
    }
}
