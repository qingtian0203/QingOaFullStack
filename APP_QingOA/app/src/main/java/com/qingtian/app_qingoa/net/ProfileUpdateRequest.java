package com.qingtian.app_qingoa.net;

import com.google.gson.annotations.SerializedName;

/** v1.6A：修改个人资料请求体。 */
public class ProfileUpdateRequest {

    @SerializedName("phone")
    private final String phone;

    @SerializedName("email")
    private final String email;

    @SerializedName("office_location")
    private final String officeLocation;

    public ProfileUpdateRequest(String phone, String email, String officeLocation) {
        this.phone = phone;
        this.email = email;
        this.officeLocation = officeLocation;
    }
}
