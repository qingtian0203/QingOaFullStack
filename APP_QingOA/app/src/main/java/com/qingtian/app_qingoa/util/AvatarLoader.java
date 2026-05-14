package com.qingtian.app_qingoa.util;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.BitmapShader;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Shader;
import android.os.Handler;
import android.os.Looper;
import android.util.LruCache;
import android.view.View;
import android.widget.ImageView;
import android.widget.TextView;

import com.qingtian.app_qingoa.net.ApiClient;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** v1.6A：轻量头像加载器，避免为了演示 App 引入完整图片库。 */
public final class AvatarLoader {

    private static final int AVATAR_SIZE = 256;
    private static final ExecutorService EXECUTOR = Executors.newSingleThreadExecutor();
    private static final Handler MAIN = new Handler(Looper.getMainLooper());
    private static final LruCache<String, Bitmap> MEMORY_CACHE = new LruCache<String, Bitmap>(4 * 1024 * 1024) {
        @Override
        protected int sizeOf(String key, Bitmap value) {
            return value.getByteCount();
        }
    };

    private AvatarLoader() {}

    public static void load(String avatarUrl, ImageView imageView, TextView fallbackView) {
        if (avatarUrl == null || avatarUrl.trim().isEmpty()) {
            showFallback(imageView, fallbackView);
            return;
        }
        String url = ApiClient.resolveResourceUrl(avatarUrl.trim());
        if (url.equals(imageView.getTag()) && imageView.getDrawable() != null
                && imageView.getVisibility() == View.VISIBLE) {
            return;
        }
        imageView.setTag(url);
        Bitmap cached = MEMORY_CACHE.get(url);
        if (cached != null) {
            showBitmap(imageView, fallbackView, cached);
            return;
        }
        EXECUTOR.execute(() -> {
            Bitmap bitmap = null;
            try {
                HttpURLConnection connection = (HttpURLConnection) new URL(url).openConnection();
                connection.setConnectTimeout(5000);
                connection.setReadTimeout(5000);
                connection.setInstanceFollowRedirects(true);
                connection.setUseCaches(true);
                try (InputStream input = connection.getInputStream()) {
                    bitmap = decodeCircularBitmap(readBytes(input));
                } finally {
                    connection.disconnect();
                }
            } catch (Exception ignored) {
                bitmap = null;
            }
            Bitmap finalBitmap = bitmap;
            if (finalBitmap != null) {
                MEMORY_CACHE.put(url, finalBitmap);
            }
            MAIN.post(() -> {
                Object tag = imageView.getTag();
                if (!(tag instanceof String) || !url.equals(tag)) {
                    return;
                }
                if (finalBitmap != null) {
                    showBitmap(imageView, fallbackView, finalBitmap);
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

    private static void showBitmap(ImageView imageView, TextView fallbackView, Bitmap bitmap) {
        imageView.setImageBitmap(bitmap);
        imageView.setVisibility(View.VISIBLE);
        fallbackView.setVisibility(View.GONE);
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

    private static Bitmap decodeCircularBitmap(byte[] bytes) {
        BitmapFactory.Options bounds = new BitmapFactory.Options();
        bounds.inJustDecodeBounds = true;
        BitmapFactory.decodeByteArray(bytes, 0, bytes.length, bounds);
        BitmapFactory.Options options = new BitmapFactory.Options();
        options.inSampleSize = calculateSampleSize(bounds.outWidth, bounds.outHeight);
        Bitmap source = BitmapFactory.decodeByteArray(bytes, 0, bytes.length, options);
        if (source == null) {
            return null;
        }
        Bitmap scaled = centerCropScale(source);
        if (scaled != source) {
            source.recycle();
        }
        return circleCrop(scaled);
    }

    private static int calculateSampleSize(int width, int height) {
        int sampleSize = 1;
        while (width / sampleSize > AVATAR_SIZE * 2 || height / sampleSize > AVATAR_SIZE * 2) {
            sampleSize *= 2;
        }
        return sampleSize;
    }

    private static Bitmap centerCropScale(Bitmap source) {
        int sourceWidth = source.getWidth();
        int sourceHeight = source.getHeight();
        float scale = Math.max(AVATAR_SIZE / (float) sourceWidth, AVATAR_SIZE / (float) sourceHeight);
        int scaledWidth = Math.round(sourceWidth * scale);
        int scaledHeight = Math.round(sourceHeight * scale);
        Bitmap scaled = Bitmap.createScaledBitmap(source, scaledWidth, scaledHeight, true);
        int x = Math.max(0, (scaledWidth - AVATAR_SIZE) / 2);
        int y = Math.max(0, (scaledHeight - AVATAR_SIZE) / 2);
        Bitmap cropped = Bitmap.createBitmap(scaled, x, y, AVATAR_SIZE, AVATAR_SIZE);
        if (scaled != source && cropped != scaled) {
            scaled.recycle();
        }
        return cropped;
    }

    private static Bitmap circleCrop(Bitmap source) {
        Bitmap output = Bitmap.createBitmap(AVATAR_SIZE, AVATAR_SIZE, Bitmap.Config.ARGB_8888);
        Canvas canvas = new Canvas(output);
        Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        paint.setShader(new BitmapShader(source, Shader.TileMode.CLAMP, Shader.TileMode.CLAMP));
        float radius = AVATAR_SIZE / 2f;
        canvas.drawCircle(radius, radius, radius, paint);
        source.recycle();
        return output;
    }
}
