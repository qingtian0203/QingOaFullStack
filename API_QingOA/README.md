# Qing OA FullStack V1

QingAgent 自动化测试实验靶场后端。目标是提供一套透明、可控、可断言的 OA 缩水版接口，用于验证 AI 是否能基于 Skill 与业务代码完成本地自动化测试。

## 技术栈

- FastAPI
- SQLAlchemy ORM
- SQLite
- opaque token 鉴权
- 内存调试基础设施：场景注入、请求日志、冻结时间

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

## 核心接口

- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/user-info`
- `GET /api/home/menu`
- `GET /api/mine/menu`
- `GET /api/home/notices`
- `GET /api/notices/{id}`
- `GET /api/punch/today-status`
- `POST /api/punch/clock`
- `POST /api/punch/clock-in`
- `GET /api/punch/records`
- `GET /api/punch/records/{id}`

`/api/punch/clock-in` 为 v1 兼容接口，v1.5 App 请使用 `/api/punch/clock` 并传 `punch_type=clock_in|clock_out`。

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
pytest
```

测试会自动使用临时 SQLite 库，不会重置正在联调的 `data/qing_oa_v1.db`。

如需手动指定数据库，可设置：

```bash
QINGOA_DATABASE_URL=sqlite:////tmp/qing_oa_v1_debug.db python run.py
```
