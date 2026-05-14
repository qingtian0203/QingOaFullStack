# Qing OA FullStack V1

QingAgent 自动化测试实验靶场后端。目标是提供一套透明、可控、可断言的 OA 缩水版接口，用于验证 AI 是否能基于 Skill 与业务代码完成本地自动化测试。

## 技术栈

- FastAPI
- SQLAlchemy ORM
- SQLite
- opaque token 鉴权
- 内存调试基础设施：场景注入、请求日志、冻结时间

## 当前版本状态

当前后端支撑 `APP_QingOA` / `WAP_QingOA` v1.6C：

- `konglingjia/123456` 为主测试账号，展示名为晴天
- `faraday/123456` 用于远距离定位异常场景
- 首页菜单只开放考勤打卡，未实现菜单保持灰显
- 我的页菜单开放我的打卡记录、补卡申诉、待我审批；OKR 目标由 App 底部 Tab 承载
- 上班卡每天只允许一次，下班卡允许更新
- `/api/punch/records` 保持明细接口；App 端按 `punch_date` 聚合成每日考勤卡
- OKR 支持列表、详情、创建、KR 进度更新、软删除，所有接口按当前 Token 用户隔离
- 我的页个人资料由 `/api/user/profile` 提供权威数据，`/api/auth/user-info` 只负责启动 Token 校验
- v1.6A 头像更新仅保存 `avatar_url` 字符串，不做 multipart 文件上传
- 通知已读按用户维度记录在 `notice_reads`，一个用户已读不影响其他用户
- v1.6B 支持考勤异常状态、补卡申诉、直属上级 + HR 两级审批
- v1.6B 预埋 `process_instances/process_tasks` 流程底座，供 v1.6C WAP 流程中心复用
- v1.6C 提供通用 workflow 模板、待办、实例、详情、审批、驳回、催办接口
- v1.6C `GET /debug/workflow/state` 固定返回 `instances/tasks/punch_appeals`，方便 QingAgent 做后端断言
- v1.6C 支持同源挂载 `../WAP_QingOA/dist` 到 `/wap/`
- 静态资源挂载在 `/static/*`，当前内置头像试验图：`/static/avatars/qingoa_icon.png`

## 启动

```bash
cd /Users/konglingjia/AIProject/QingOaFullStack/API_QingOA
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

默认端口为 `8010`，配置在 [backend/core/config.py](/Users/konglingjia/AIProject/QingOaFullStack/API_QingOA/backend/core/config.py)。

也可以手动用 uvicorn 启动：

```bash
uvicorn main:app --host 0.0.0.0 --port 8010 --reload
```

模拟器访问：

```text
http://10.0.2.2:8010
```

真机访问：

```text
http://<Mac 局域网 IP>:8010
```

## 初始账号

| 账号 | 密码 | 说明 |
|---|---|---|
| `konglingjia` | `123456` | 正常员工，有打卡权限，展示名为晴天 |
| `nopunch` | `123456` | 无打卡权限 |
| `expired` | `123456` | 正常账号，Token 过期场景通过注入实现 |
| `faraday` | `123456` | 正常员工，超范围打卡由 App 测试模式上报远处坐标实现 |
| `manager` | `123456` | 直属上级，v1.6B 补卡一级审批账号；上级为 thanos |
| `hr` | `123456` | HR 管理员，v1.6B 补卡二级审批账号 |
| `thanos` | `123456` | 高管演示账号，展示名为灭霸，预留给 v1.7 退回修改 / 高级审批场景 |

## 核心接口

- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/user-info`
- `GET /api/home/menu`
- `GET /api/mine/menu`
- `GET /api/home/notices`
- `GET /api/home/unread-count`
- `GET /api/notices/{id}`
- `POST /api/notices/{id}/read`
- `GET /api/user/profile`
- `PUT /api/user/profile`
- `POST /api/user/avatar`
- `GET /static/avatars/qingoa_icon.png`
- `GET /api/punch/today-status`
- `POST /api/punch/clock`
- `POST /api/punch/clock-in`
- `GET /api/punch/records`
- `GET /api/punch/records/{id}`
- `POST /api/punch/appeal`
- `GET /api/punch/appeals`
- `GET /api/punch/appeals/pending-review`
- `POST /api/punch/appeals/{id}/review`
- `GET /api/punch/monthly-summary`
- `GET /api/workflow/tasks`
- `GET /api/workflow/templates`
- `GET /api/workflow/instances`
- `GET /api/workflow/instances/{id}`
- `POST /api/workflow/tasks/{id}/approve`
- `POST /api/workflow/tasks/{id}/reject`
- `POST /api/workflow/instances/{id}/urge`
- `GET /debug/workflow/state`
- `GET /api/okr/list`
- `GET /api/okr/{id}`
- `POST /api/okr/create`
- `PUT /api/okr/{id}/key-results/{kr_id}`
- `DELETE /api/okr/{id}`

`/api/punch/clock-in` 为 v1 兼容接口，v1.5 App 请使用 `/api/punch/clock` 并传 `punch_type=clock_in|clock_out`。

### v1.5A 打卡规则

| 场景 | 行为 |
|---|---|
| 上班打卡成功 | 生成 `punch_type=clock_in` 记录 |
| 重复上班打卡 | 返回 `1008`，不生成新记录 |
| 未上班先下班 | 返回 `1007` |
| 下班打卡成功 | 生成 `punch_type=clock_out` 记录 |
| 重复下班打卡 | 更新当天下班记录，返回 `updated=true` |
| 超范围打卡 | 返回 `1004`，不生成记录，请看 `/debug/requests` 中的坐标日志 |

### v1.5B OKR 规则

| 场景 | 行为 |
|---|---|
| 查询 OKR 列表 | `GET /api/okr/list`，可选 `period` |
| 查询详情 | 返回 OKR 基础信息与 `key_results` |
| 创建 OKR | `key_results` 至少 1 条，`target_value` 必须大于 0 |
| 更新 KR 进度 | `current_value` 可超过 `target_value`，单条进度封顶 100 |
| 访问他人 OKR | 返回 `1010` |
| 删除 OKR | 软删除，`status=cancelled`，列表和详情不再返回 |

### v1.6A 用户资料与通知已读规则

| 场景 | 行为 |
|---|---|
| App 启动校验 | `GET /api/auth/user-info` 返回 profile 子集，返回 `1002` 时跳登录 |
| 我的页刷新 | `GET /api/user/profile` 返回头像、手机、邮箱、办公地点等完整资料 |
| 修改资料 | `PUT /api/user/profile` 支持 `phone/email/office_location`，邮箱格式错误返回 `2003` |
| 修改头像 | `POST /api/user/avatar` 仅传 `avatar_url` 字符串，非法图片 URL 返回 `2001` |
| 头像试验图 | 可填 `https://oa.qingagent.top/static/avatars/qingoa_icon.png` |
| 首页公告列表 | `GET /api/home/notices` 返回每条公告的 `is_read` |
| 打开公告详情 | App 调 `POST /api/notices/{id}/read`，该用户未读数减少 |
| 多账号隔离 | `notice_reads` 按 `notice_id + user_id` 唯一约束，互不影响 |

### v1.6B 考勤异常、补卡申诉与流程底座

| 场景 | 行为 |
|---|---|
| 迟到/早退判断 | `clock_in > 09:10` 记为 `late`，`clock_out < 17:50` 记为 `early_leave` |
| 超范围打卡 | 返回 `1004`，不生成 `punch_records`，仅在 `/debug/requests` 保留坐标日志 |
| 提交补卡 | `POST /api/punch/appeal` 创建 `punch_appeals`、`process_instances` 和直属上级 `todo` 任务 |
| 重复提交 | 同一用户、日期、卡类型已有 `submitted/manager_approved` 申诉时返回 `1011` |
| 上级通过 | 申诉进入 `manager_approved`，生成 HR `todo` 任务，暂不生成补卡记录 |
| 上级驳回 | 申诉进入 `rejected_by_manager`，流程 `rejected`，不进入 HR |
| HR 通过 | 申诉进入 `approved`，流程 `completed`，自动生成 `status=makeup/source=appeal` 的打卡记录 |
| HR 驳回 | 申诉进入 `rejected_by_hr`，流程 `rejected`，不生成补卡记录 |
| 流程预埋 | `/api/workflow/*` 读取任务、实例、详情和催办，v1.6C WAP 流程中心复用 |

### v1.6C WAP 流程中心规则

| 场景 | 行为 |
|---|---|
| 获取新办入口 | `GET /api/workflow/templates` 返回补卡申诉入口卡片，WAP 发起补卡为 Optional |
| 待办 / 催办 | `GET /api/workflow/tasks?bucket=todo|urged` 按当前登录用户返回待处理任务 |
| 进行中 / 退回 / 已完成 | `GET /api/workflow/instances?bucket=processing|returned|completed` 返回当前用户相关流程 |
| 详情 | `GET /api/workflow/instances/{id}` 返回流程详情、业务摘要和时间线 |
| WAP 审批 | `POST /api/workflow/tasks/{id}/approve` 或 `/reject`，复用补卡申诉两级审批状态机 |
| 催办 | `POST /api/workflow/instances/{id}/urge` 将当前待办标记为 `urged=true` |
| Debug 断言 | `GET /debug/workflow/state?username=konglingjia` 固定返回 `{instances,tasks,punch_appeals}` |
| WAP 托管 | 构建 `WAP_QingOA` 后访问 `/wap/#/workflow?tab=todo` |

## 调试接口

`/debug/*` v1 不需要鉴权，仅用于本地测试环境。

- `POST /debug/reset-data`
- `POST /debug/inject-scenario`
- `GET /debug/scenarios`
- `DELETE /debug/scenarios`
- `DELETE /debug/scenarios/{id}`
- `GET /debug/state`
- `GET /debug/requests`
- `GET /debug/attendance/latest`
- `GET /debug/workflow/state`
- `POST /debug/punch/reset-today`
- `POST /debug/attendance/recalculate`
- `POST /debug/freeze-time`
- `DELETE /debug/freeze-time`

## 标准测试链路

```bash
.venv/bin/pytest -q
```

测试会自动使用临时 SQLite 库，不会重置正在联调的 `data/qing_oa_v1.db`。

如需手动指定数据库，可设置：

```bash
QINGOA_DATABASE_URL=sqlite:////tmp/qing_oa_v1_debug.db python run.py
```
