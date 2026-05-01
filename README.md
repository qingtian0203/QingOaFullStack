# QingOaFullStack

全栈透明 OA 演示项目总仓库，用于 QingAgent 自动化测试实验。

## 目录规划

```text
QingOaFullStack/
├── API_QingOA/      # FastAPI + SQLite 接口后台
├── APP_QingOA/      # Android App
└── WAP_QingOA/      # WAP / H5 页面，v2 再加入
```

当前已完成 `API_QingOA` 与 `APP_QingOA` 的 v1.6A 联调基础：登录、首页菜单、通知已读、上下班打卡、下班更新、每日打卡记录聚合、OKR 列表/详情/创建/KR 进度更新、我的页个人资料刷新、头像 URL 更新、接口调试与请求日志。

## 后端启动

```bash
cd /Users/konglingjia/AIProject/QingOaFullStack/API_QingOA
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

默认端口：`8010`。

## App 现状

`APP_QingOA` 是 Android 原生演示 App，当前主要页面：

- 登录 / Splash Token 校验
- 首页菜单 + 通知公告
- 考勤打卡：上班卡不可重复，下班卡可更新
- 打卡记录：接口仍返回明细，App 按自然日聚合成每日考勤卡
- OKR：底部中间 Tab，支持目标列表、详情、创建目标、更新 KR 当前值
- 通知公告：支持用户维度已读状态，首页显示当前用户未读数
- 我的页：cache-then-network 展示个人资料，支持编辑手机/邮箱/办公地点与头像 URL
- 表单体验：登录页、OKR 新建页已接入软键盘避让，输入框聚焦时会自动滚动到键盘上方

```bash
cd /Users/konglingjia/AIProject/QingOaFullStack/APP_QingOA
JAVA_HOME=$(/usr/libexec/java_home -v 17) ./gradlew testDebugUnitTest assembleDebug
```

## 验证命令

```bash
cd /Users/konglingjia/AIProject/QingOaFullStack/API_QingOA
.venv/bin/pytest -q

cd /Users/konglingjia/AIProject/QingOaFullStack/APP_QingOA
JAVA_HOME=$(/usr/libexec/java_home -v 17) ./gradlew testDebugUnitTest assembleDebug
```
