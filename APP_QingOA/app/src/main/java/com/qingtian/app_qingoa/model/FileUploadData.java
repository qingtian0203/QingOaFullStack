package com.qingtian.app_qingoa.model;

import com.google.gson.annotations.SerializedName;

public class FileUploadData {
    @SerializedName("file_id")
    private String fileId;
    @SerializedName("url")
    private String url;
    @SerializedName("filename")
    private String filename;
    @SerializedName("mime_type")
    private String mimeType;
    @SerializedName("usage")
    private String usage;

    public String getFileId() { return fileId; }
    public String getUrl() { return url; }
    public String getFilename() { return filename; }
    public String getMimeType() { return mimeType; }
    public String getUsage() { return usage; }
}
