# Qing OA FullStack V1

QingAgent 自动化测试实验靶场后端。目标是提供一套透明、可控、可断言的 OA 缩水版接口，用于验证 AI 是否能基于 Skill 与业务代码完成本地自动化测试。

## 技术栈

- FastAPI
- SQLAlchemy ORM
- SQLite
- opaque token 鉴权
- 内存调试基础设施：场景注入、请求日志、冻结时间

## 当前版本状态

当前后端支撑 `APP_QingOA` v1.6A：

- `konglingjia/123456` 为主测试账号，展示名为晴天
- `faraday/123456` 用于远距离定位异常场景
- 首页菜单只开放考勤打卡，未实现菜单保持灰显
- 我的页菜单开放我的打卡记录；OKR 目标由 App 底部 Tab 承载
- 上班卡每天只允许一次，下班卡允许更新
- `/api/punch/records` 保持明细接口；App 端按 `punch_date` 聚合成每日考勤卡
- OKR 支持列表、详情、创建、KR 进度更新、软删除，所有接口按当前 Token 用户隔离
- 我的页个人资料由 `/api/user/profile` 提供权威数据，`/api/auth/user-info` 只负责启动 Token 校验
- v1.6A 头像更新仅保存 `avatar_url` 字符串，不做 multipart 文件上传
- 通知已读按用户维度记录在 `notice_reads`，一个用户已读不影响其他用户

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
| `manager` | `123456` | 直属上级，v1.6B 补卡审批预留账号 |
| `hr` | `123456` | HR 管理员，v1.6B 二级审批预留账号 |

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
- `GET /api/punch/today-status`
- `POST /api/punch/clock`
- `POST /api/punch/clock-in`
- `GET /api/punch/records`
- `GET /api/punch/records/{id}`
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
| 首页公告列表 | `GET /api/home/notices` 返回每条公告的 `is_read` |
| 打开公告详情 | App 调 `POST /api/notices/{id}/read`，该用户未读数减少 |
| 多账号隔离 | `notice_reads` 按 `notice_id + user_id` 唯一约束，互不影响 |

## 调试接口

`/debug/*` v1 不需要鉴权，仅用于本地测试环境。

- `POST /debug/reset-data`
- `POST /debug/inject-scenario`
- `GET /debug/scenarios`
- `DELETE /debug/scenarios`
- `DELETE /debug/scenarios/{id}`
- `GET /debug/state`
- `GET /debug/requests`
- `POST /debug/punch/reset-today`
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
