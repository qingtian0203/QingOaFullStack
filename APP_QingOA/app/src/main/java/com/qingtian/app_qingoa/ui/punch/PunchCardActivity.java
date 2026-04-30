package com.qingtian.app_qingoa.ui.punch;

import android.Manifest;
import android.content.pm.PackageManager;
import android.location.Location;
import android.location.LocationManager;
import android.os.Bundle;
import android.view.View;

import androidx.annotation.NonNull;
import androidx.core.app.ActivityCompat;

import com.qingtian.app_qingoa.base.BaseActivity;
import com.qingtian.app_qingoa.databinding.ActivityPunchCardBinding;
import com.qingtian.app_qingoa.model.PunchResultData;
import com.qingtian.app_qingoa.model.PunchStatusData;
import com.qingtian.app_qingoa.net.ApiClient;
import com.qingtian.app_qingoa.net.ApiResponse;
import com.qingtian.app_qingoa.net.PunchRequest;
import com.qingtian.app_qingoa.util.ToastUtils;

import java.util.List;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * 打卡页。
 * 流程：
 * 1. 进入时加载今日打卡状态
 * 2. 点击打卡 → 获取 GPS 坐标（优先使用测试模式覆盖坐标）→ 调接口
 * 3. 测试坐标覆盖区：lat/lng 输入框留空则使用真实 GPS，有值则覆盖上报坐标
 *    （这是 QingAgent 自动化测试的关键入口，用于稳定复现超范围/范围内场景）
 */
public class PunchCardActivity extends BaseActivity {

    private static final int REQUEST_LOCATION = 101;
    private ActivityPunchCardBinding mBinding;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        mBinding = ActivityPunchCardBinding.inflate(getLayoutInflater());
        setContentView(mBinding.getRoot());

        mBinding.btnBack.setOnClickListener(v -> finish());
        mBinding.btnPunch.setOnClickListener(v -> startPunch());

        loadTodayStatus();
    }

    /** 加载今日打卡状态，更新 UI */
    private void loadTodayStatus() {
        ApiClient.getService().getTodayStatus().enqueue(new Callback<ApiResponse<PunchStatusData>>() {
            @Override
            public void onResponse(Call<ApiResponse<PunchStatusData>> call,
                                   Response<ApiResponse<PunchStatusData>> response) {
                if (response.isSuccessful() && response.body() != null) {
                    ApiResponse<PunchStatusData> body = response.body();
                    if (body.isTokenExpired()) {
                        handleTokenExpired();
                        return;
                    }
                    if (body.isSuccess() && body.getData() != null) {
                        updateStatusUI(body.getData());
                    }
                }
            }

            @Override
            public void onFailure(Call<ApiResponse<PunchStatusData>> call, Throwable t) {
                ToastUtils.show(PunchCardActivity.this, "获取打卡状态失败");
            }
        });
    }

    private void updateStatusUI(PunchStatusData data) {
        if (data.hasPunched()) {
            mBinding.tvStatusIcon.setText("✓");
            mBinding.tvStatusIcon.setTextColor(0xFF4CAF50);
            mBinding.tvStatus.setText("今日已打卡");
            mBinding.tvStatus.setTextColor(0xFF4CAF50);
            mBinding.btnPunch.setEnabled(false);
            mBinding.btnPunch.setText("已完成打卡");

            if (data.getPunchTime() != null) {
                mBinding.tvPunchTime.setVisibility(View.VISIBLE);
                mBinding.tvPunchTime.setText("打卡时间：" + data.getPunchTime());
            }
        }

        // 显示打卡点名称
        List<PunchStatusData.PunchPoint> points = data.getPunchPoints();
        if (points != null && !points.isEmpty()) {
            mBinding.tvPunchPoint.setText("打卡点：" + points.get(0).getName());
        }
    }

    /** 触发打卡（先检查权限，再获取坐标） */
    private void startPunch() {
        // 优先检查测试坐标覆盖输入框
        double[] testCoords = getTestCoords();
        if (testCoords != null) {
            // 测试模式：直接用覆盖坐标打卡
            doPunch(testCoords[0], testCoords[1]);
            return;
        }

        // 正常模式：需要定位权限
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION)
                != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this,
                    new String[]{Manifest.permission.ACCESS_FINE_LOCATION}, REQUEST_LOCATION);
            return;
        }
        getLocationAndPunch();
    }

    /**
     * 读取测试坐标覆盖输入框。
     * @return double[]{lat, lng} 如果有有效输入，否则返回 null（使用真实 GPS）
     */
    private double[] getTestCoords() {
        String latStr = mBinding.etTestLat.getText() != null
                ? mBinding.etTestLat.getText().toString().trim() : "";
        String lngStr = mBinding.etTestLng.getText() != null
                ? mBinding.etTestLng.getText().toString().trim() : "";

        if (!latStr.isEmpty() && !lngStr.isEmpty()) {
            try {
                double lat = Double.parseDouble(latStr);
                double lng = Double.parseDouble(lngStr);
                return new double[]{lat, lng};
            } catch (NumberFormatException e) {
                ToastUtils.show(this, "坐标格式错误，使用真实 GPS");
            }
        }
        return null;
    }

    private void getLocationAndPunch() {
        LocationManager lm = (LocationManager) getSystemService(LOCATION_SERVICE);
        Location last = null;

        // 优先 GPS，其次网络定位
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION)
                == PackageManager.PERMISSION_GRANTED) {
            last = lm.getLastKnownLocation(LocationManager.GPS_PROVIDER);
            if (last == null) {
                last = lm.getLastKnownLocation(LocationManager.NETWORK_PROVIDER);
            }
        }

        if (last != null) {
            doPunch(last.getLatitude(), last.getLongitude());
        } else {
            ToastUtils.show(this, "获取定位失败，请开启 GPS 后重试");
        }
    }

    /** 调用打卡接口 */
    private void doPunch(double lat, double lng) {
        setLoading(true);
        String deviceId = android.provider.Settings.Secure.getString(
                getContentResolver(), android.provider.Settings.Secure.ANDROID_ID);

        ApiClient.getService()
                .clockIn(new PunchRequest(lat, lng, deviceId))
                .enqueue(new Callback<ApiResponse<PunchResultData>>() {
                    @Override
                    public void onResponse(Call<ApiResponse<PunchResultData>> call,
                                           Response<ApiResponse<PunchResultData>> response) {
                        setLoading(false);
                        if (response.isSuccessful() && response.body() != null) {
                            ApiResponse<PunchResultData> body = response.body();
                            if (body.isTokenExpired()) {
                                handleTokenExpired();
                                return;
                            }
                            ToastUtils.show(PunchCardActivity.this, body.getMsg());
                            if (body.isSuccess()) {
                                // 打卡成功，刷新状态
                                loadTodayStatus();
                            }
                        }
                    }

                    @Override
                    public void onFailure(Call<ApiResponse<PunchResultData>> call, Throwable t) {
                        setLoading(false);
                        ToastUtils.show(PunchCardActivity.this, "网络请求失败");
                    }
                });
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions,
                                           @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == REQUEST_LOCATION
                && grantResults.length > 0
                && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            getLocationAndPunch();
        } else {
            ToastUtils.show(this, "需要定位权限才能打卡");
        }
    }

    private void setLoading(boolean loading) {
        mBinding.btnPunch.setEnabled(!loading);
        mBinding.progressBar.setVisibility(loading ? View.VISIBLE : View.GONE);
    }
}
