package com.qingtian.app_qingoa.ui.punch;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.location.Location;
import android.location.LocationManager;
import android.os.Bundle;
import android.view.View;

import androidx.annotation.NonNull;
import androidx.core.app.ActivityCompat;

import com.qingtian.app_qingoa.base.BaseActivity;
import com.qingtian.app_qingoa.R;
import com.qingtian.app_qingoa.databinding.ActivityPunchCardBinding;
import com.qingtian.app_qingoa.model.PunchResultData;
import com.qingtian.app_qingoa.model.PunchStatusData;
import com.qingtian.app_qingoa.net.ApiClient;
import com.qingtian.app_qingoa.net.ApiResponse;
import com.qingtian.app_qingoa.net.PunchRequest;
import com.qingtian.app_qingoa.util.ToastUtils;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import java.util.Locale;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * v1.5 考勤打卡页。
 *
 * 业务规则：
 * - 上班卡：每天只能打一次，已打后按钮隐藏并显示打卡时间
 * - 下班卡：可重复打卡（加班刷新），服务端返回 updated=true 时提示"下班时间已更新"
 * - 下班卡依赖上班卡：未打上班卡时下班卡按钮禁用（服务端会返回 1007）
 */
public class PunchCardActivity extends BaseActivity {

    private static final int REQUEST_LOCATION = 101;

    /** 当前正在发起哪类打卡，null 表示空闲 */
    private String mPunchingType = null;
    private ActivityPunchCardBinding mBinding;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        mBinding = ActivityPunchCardBinding.inflate(getLayoutInflater());
        setContentView(mBinding.getRoot());

        mBinding.btnBack.setOnClickListener(v -> finish());
        mBinding.btnRecords.setOnClickListener(v ->
                startActivity(new Intent(this, PunchRecordListActivity.class)));
        mBinding.btnClockIn.setOnClickListener(v -> startPunch("clock_in"));
        mBinding.btnClockOut.setOnClickListener(v -> startPunch("clock_out"));
        mBinding.tvTodayDate.setText(new SimpleDateFormat("yyyy-MM-dd  EEEE", Locale.CHINA)
                .format(new Date()));

        loadTodayStatus();
    }

    /** 加载今日上班/下班卡状态，更新双卡片 UI */
    private void loadTodayStatus() {
        ApiClient.getService().getTodayStatus()
                .enqueue(new Callback<ApiResponse<PunchStatusData>>() {
                    @Override
                    public void onResponse(Call<ApiResponse<PunchStatusData>> call,
                                           Response<ApiResponse<PunchStatusData>> response) {
                        if (!isFinishing() && response.isSuccessful() && response.body() != null) {
                            ApiResponse<PunchStatusData> body = response.body();
                            if (body.isTokenExpired()) { handleTokenExpired(); return; }
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

    /**
     * 根据接口数据更新上班/下班卡 UI。
     * - clock_in done：隐藏按钮，显示打卡时间，禁止重复
     * - clock_out done：显示时间，按钮改为"更新下班时间"（加班场景）
     * - clock_in 未打：下班卡按钮置灰（依赖顺序约束）
     */
    private void updateStatusUI(PunchStatusData data) {
        PunchStatusData.PunchInfo clockIn = data.getClockIn();
        PunchStatusData.PunchInfo clockOut = data.getClockOut();

        // ── 上班卡 ──
        if (clockIn != null && clockIn.isDone()) {
            mBinding.tvClockInStatus.setText("已完成");
            mBinding.tvClockInStatus.setTextColor(0xFF4CAF50);
            mBinding.tvClockInStatus.setBackgroundResource(R.drawable.bg_tag_success);
            mBinding.dotClockIn.setBackgroundResource(R.drawable.bg_timeline_dot_success);
            mBinding.tvClockInTime.setVisibility(View.VISIBLE);
            mBinding.tvClockInTime.setText(clockIn.getTime());
            mBinding.btnClockIn.setVisibility(View.GONE);
        } else {
            mBinding.tvClockInStatus.setText("未打卡");
            mBinding.tvClockInStatus.setTextColor(0xFFA8AFBD);
            mBinding.tvClockInStatus.setBackgroundResource(R.drawable.bg_tag_pending);
            mBinding.dotClockIn.setBackgroundResource(R.drawable.bg_timeline_dot_pending);
            mBinding.tvClockInTime.setVisibility(View.VISIBLE);
            mBinding.tvClockInTime.setText("等待打卡");
            mBinding.btnClockIn.setVisibility(View.VISIBLE);
            mBinding.btnClockIn.setText("上班打卡\n" + formatActionTime());
            mBinding.btnClockIn.setContentDescription("qingoa_punch_clock_in_button");
            mBinding.btnClockIn.setBackgroundResource(R.drawable.bg_punch_circle);
        }

        // ── 下班卡 ──
        boolean clockInDone = clockIn != null && clockIn.isDone();
        if (clockOut != null && clockOut.isDone()) {
            mBinding.tvClockOutStatus.setText("已完成");
            mBinding.tvClockOutStatus.setTextColor(0xFF4CAF50);
            mBinding.tvClockOutStatus.setBackgroundResource(R.drawable.bg_tag_success);
            mBinding.dotClockOut.setBackgroundResource(R.drawable.bg_timeline_dot_success);
            mBinding.tvClockOutTime.setVisibility(View.VISIBLE);
            mBinding.tvClockOutTime.setText(clockOut.getTime());
            mBinding.btnClockOut.setEnabled(true);
            mBinding.btnClockOut.setVisibility(View.VISIBLE);
            mBinding.btnClockOut.setAlpha(1.0f);
            mBinding.btnClockOut.setBackgroundResource(R.drawable.bg_punch_circle);
            mBinding.btnClockOut.setText("更新打卡\n" + formatActionTime());
            mBinding.btnClockOut.setContentDescription("qingoa_punch_clock_out_update_button");
        } else {
            mBinding.tvClockOutStatus.setText("未打卡");
            mBinding.tvClockOutStatus.setTextColor(0xFFA8AFBD);
            mBinding.tvClockOutStatus.setBackgroundResource(R.drawable.bg_tag_pending);
            mBinding.dotClockOut.setBackgroundResource(R.drawable.bg_timeline_dot_pending);
            mBinding.tvClockOutTime.setVisibility(View.VISIBLE);
            mBinding.tvClockOutTime.setText(clockInDone ? "等待打卡" : "上班卡完成后开启");
            mBinding.btnClockOut.setText("下班打卡\n" + formatActionTime());
            mBinding.btnClockOut.setContentDescription("qingoa_punch_clock_out_button");
            mBinding.btnClockOut.setEnabled(clockInDone);
            mBinding.btnClockOut.setVisibility(clockInDone ? View.VISIBLE : View.GONE);
            mBinding.btnClockOut.setAlpha(clockInDone ? 1.0f : 0.45f);
            mBinding.btnClockOut.setBackgroundResource(clockInDone
                    ? R.drawable.bg_punch_circle : R.drawable.bg_punch_circle_disabled);
        }

        // 打卡点名称
        List<PunchStatusData.PunchPoint> points = data.getPunchPoints();
        if (points != null && !points.isEmpty()) {
            mBinding.tvPunchPoint.setText("打卡点：" + points.get(0).getName()
                    + "（范围 " + points.get(0).getRadius() + "m）");
        }
    }

    private String formatActionTime() {
        return new SimpleDateFormat("HH:mm:ss", Locale.CHINA).format(new Date());
    }

    /** 触发打卡（先检查测试坐标覆盖，再走真实 GPS） */
    private void startPunch(String punchType) {
        mPunchingType = punchType;
        double[] testCoords = getTestCoords();
        if (testCoords != null) {
            doPunch(testCoords[0], testCoords[1], punchType);
            return;
        }
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION)
                != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this,
                    new String[]{Manifest.permission.ACCESS_FINE_LOCATION}, REQUEST_LOCATION);
            return;
        }
        getLocationAndPunch(punchType);
    }

    private double[] getTestCoords() {
        String latStr = mBinding.etTestLat.getText() != null
                ? mBinding.etTestLat.getText().toString().trim() : "";
        String lngStr = mBinding.etTestLng.getText() != null
                ? mBinding.etTestLng.getText().toString().trim() : "";
        if (!latStr.isEmpty() && !lngStr.isEmpty()) {
            try {
                return new double[]{Double.parseDouble(latStr), Double.parseDouble(lngStr)};
            } catch (NumberFormatException e) {
                ToastUtils.show(this, "坐标格式错误，使用真实 GPS");
            }
        }
        return null;
    }

    private void getLocationAndPunch(String punchType) {
        LocationManager lm = (LocationManager) getSystemService(LOCATION_SERVICE);
        Location last = null;
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION)
                == PackageManager.PERMISSION_GRANTED) {
            last = lm.getLastKnownLocation(LocationManager.GPS_PROVIDER);
            if (last == null) last = lm.getLastKnownLocation(LocationManager.NETWORK_PROVIDER);
        }
        if (last != null) {
            doPunch(last.getLatitude(), last.getLongitude(), punchType);
        } else {
            ToastUtils.show(this, "获取定位失败，请开启 GPS 后重试");
        }
    }

    /** 调用 /api/punch/clock 接口 */
    private void doPunch(double lat, double lng, String punchType) {
        if (lat < -90 || lat > 90) { ToastUtils.show(this, "纬度无效"); return; }
        if (lng < -180 || lng > 180) { ToastUtils.show(this, "经度无效"); return; }

        setLoading(true);
        String deviceId = android.provider.Settings.Secure.getString(
                getContentResolver(), android.provider.Settings.Secure.ANDROID_ID);

        ApiClient.getService()
                .clock(new PunchRequest(lat, lng, deviceId, punchType))
                .enqueue(new Callback<ApiResponse<PunchResultData>>() {
                    @Override
                    public void onResponse(Call<ApiResponse<PunchResultData>> call,
                                           Response<ApiResponse<PunchResultData>> response) {
                        setLoading(false);
                        if (response.isSuccessful() && response.body() != null) {
                            ApiResponse<PunchResultData> body = response.body();
                            if (body.isTokenExpired()) { handleTokenExpired(); return; }

                            // 上班卡重复：服务端返回 1008
                            if (body.getCode() == 1008) {
                                ToastUtils.show(PunchCardActivity.this, "今日上班卡已打，不可重复");
                                return;
                            }
                            // 未打上班卡就打下班卡
                            if (body.getCode() == 1007) {
                                ToastUtils.show(PunchCardActivity.this, "请先打上班卡");
                                return;
                            }

                            // 展示服务端消息（首次打卡 or 下班刷新 updated=true）
                            ToastUtils.show(PunchCardActivity.this, body.getMsg());
                            if (body.isSuccess()) {
                                // 打卡成功，刷新双卡片状态
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
                && grantResults[0] == PackageManager.PERMISSION_GRANTED
                && mPunchingType != null) {
            getLocationAndPunch(mPunchingType);
        } else {
            ToastUtils.show(this, "需要定位权限才能打卡");
        }
    }

    private void setLoading(boolean loading) {
        mBinding.btnClockIn.setEnabled(!loading);
        mBinding.btnClockOut.setEnabled(!loading);
        mBinding.progressBar.setVisibility(loading ? View.VISIBLE : View.GONE);
    }
}
