# QingOaFullStack

全栈透明 OA 演示项目总仓库，用于 QingAgent 自动化测试实验。

## 目录规划

```text
QingOaFullStack/
├── API_QingOA/      # FastAPI + SQLite 接口后台
├── APP_QingOA/      # Android App
└── WAP_QingOA/      # Vue3/Vite WAP 流程中心
```

当前已完成 `API_QingOA`、`APP_QingOA` 与 `WAP_QingOA` 的 v1.6C 联调基础：登录、首页菜单、通知已读、上下班打卡、下班更新、每日打卡记录聚合、OKR 列表/详情/创建/KR 进度更新、我的页个人资料刷新、头像 URL 更新、补卡申诉两级审批、流程底座、WAP 流程中心、接口调试与请求日志。

当前需求文档放在：

```text
/Users/konglingjia/AIProject/AI 文档/qingoa/qingoa_v1_6_design.md
/Users/konglingjia/AIProject/AI 文档/qingoa/qingoa_v1_7_design.md
```

## 后端启动

```bash
cd /Users/konglingjia/AIProject/QingOaFullStack/API_QingOA
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

默认端口：`8010`。

`API_QingOA` 会在检测到 `WAP_QingOA/dist` 后自动把 WAP 挂载到 `/wap/`：

```text
http://127.0.0.1:8010/wap/#/workflow?tab=todo
```

## WAP 构建

```bash
cd /Users/konglingjia/AIProject/QingOaFullStack/WAP_QingOA
npm install
npm run build
```

开发期也可以单独跑 Vite：

```bash
npm run dev
```

## App 现状

`APP_QingOA` 是 Android 原生演示 App，当前主要页面：

- 登录 / Splash Token 校验
- 首页菜单 + 通知公告
- 考勤打卡：上班卡不可重复，下班卡可更新
- 打卡记录：接口仍返回明细，App 按自然日聚合成每日考勤卡
- OKR：底部中间 Tab，支持目标列表、详情、创建目标、更新 KR 当前值
- 通知公告：支持用户维度已读状态，首页显示当前用户未读数
- 我的页：cache-then-network 展示个人资料，支持编辑手机/邮箱/办公地点与头像 URL
- 补卡申诉：我的页入口提交补卡申请，直属上级审批通过后进入 HR 二审，HR 通过后自动生成 `status=makeup` 打卡记录
- 待我审批：`manager/123456` 处理一级审批，`hr/123456` 处理二级审批
- 高管预留账号：`thanos/123456`，展示名为灭霸，作为 `manager` 的上级，预留给 v1.7 退回修改 / 高级审批场景
- 流程中心：首页和我的页入口打开 WAP WebView，默认进入待办 Tab
- 静态头像试验图：`https://oa.qingagent.top/static/avatars/qingoa_icon.png`
- 表单体验：登录页、OKR 新建页已接入软键盘避让，输入框聚焦时会自动滚动到键盘上方

```bash
cd /Users/konglingjia/AIProject/QingOaFullStack/APP_QingOA
JAVA_HOME=$(/usr/libexec/java_home -v 17) ./gradlew testDebugUnitTest assembleDebug
```

## 验证命令

```bash
cd /Users/konglingjia/AIProject/QingOaFullStack/API_QingOA
.venv/bin/pytest -q

cd /Users/konglingjia/AIProject/QingOaFullStack/WAP_QingOA
npm run build

cd /Users/konglingjia/AIProject/QingOaFullStack/APP_QingOA
JAVA_HOME=$(/usr/libexec/java_home -v 17) ./gradlew testDebugUnitTest assembleDebug
```
