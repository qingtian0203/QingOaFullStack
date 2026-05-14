---
name: QingOA 打卡自动化测试
description: QingOA App 打卡业务的端到端自动化测试指南。用于通过投屏截图理解、ADB/uiautomator 操作、API debug 断言和请求日志证明打卡链路真实成功。
---

# QingOA 打卡自动化测试 Skill

## 适用场景

当任务涉及验证 QingOA App 的考勤打卡链路，尤其是“AI 能否理解 App + API + debug 状态并完成自动化测试”时，使用本 Skill。

目标不是只点按钮，而是形成可复现证据链：

```text
截图/视觉理解 -> ADB/uiautomator 操作 -> 业务接口响应 -> debug 断言 -> 请求日志 -> 失败解释
```

## 当前自动化入口

优先使用 QingAgent 测试台的“自动化用例”Tab，读取本仓库 `.agents/cases/attendance_*.yaml`。

当前 13 条考勤用例均应被识别为对应 runner 可执行：

| 用例 | App 自动化边界 |
|---|---|
| `attendance.clock_in_success` | App 进入打卡页、输入坐标、点击上班打卡；API/debug 断言 |
| `attendance.clock_in_out_of_range` | App 进入打卡页、输入越界坐标、点击上班打卡；API/debug 断言 |
| `attendance.clock_in_duplicate` | 第一次上班打卡走 App；第二次重复规则用 API 验证 |
| `attendance.clock_out_success` | API 先构造上班卡，App 完成首次下班打卡；debug 断言 |
| `attendance.clock_out_requires_clock_in` | 无上班卡直接下班打卡，API 验证 `NO_CLOCK_IN` |
| `attendance.clock_out_update` | API/debug 先构造上班卡和首次下班卡，App 只完成二次更新下班；debug 断言 |
| `attendance.record_list_status` | App 进入打卡页后打开记录列表；API/debug 断言 |
| `attendance.record_detail_display` | App 打开记录列表并进入每日详情；API/detail 与 UI 字段断言 |
| `attendance.monthly_summary_full_day_and_missing` | API 构造完整出勤与缺卡日，验证月汇总 |
| `attendance.appeal_submit_and_approve` | 员工端补卡申诉提交走 App；管理者/HR 审批用 API 验证 |
| `attendance.appeal_reject` | 员工端补卡申诉提交走 App；管理者驳回用 API 验证 |
| `attendance.appeal_duplicate_blocked` | API 验证同日同类型补卡重复提交拦截 |
| `attendance.appeal_pending_review_role_scope` | API 验证待审批列表、无关用户/HR 越权、HR 节点流转 |

多人角色切换仍由 API 完成，不在同一个 App case 里强行切账号，避免登录态和缓存状态相互污染。

## 用例数据准备铁律

所有 `attendance_*.yaml` 必须先问清楚：这个场景要验证的按钮、状态、断言依赖哪些已有打卡/申诉数据？这些数据必须在 `preconditions` 中显式准备，不能依赖数据库残留、上一条 case、人工操作或 App 当前缓存。

设计规则：

- 每条 case 默认要可独立重复运行。先调用对应 debug endpoint 清理当天或目标日期数据，再构造本 case 需要的最小数据。
- 如果 case 目标不是验证“通过 UI 创建前置数据”，前置数据优先用 API/debug endpoint 构造；App UI 步骤只覆盖本 case 的核心行为。
- 时间敏感场景必须显式调用 `/debug/freeze-time`，需要上午/下午两个阶段时分阶段冻结。
- `clock_out_success` 这类首次下班场景，应在前置或早期 API 步骤中先有上班卡，再让 App 验证首次下班。
- `clock_out_update` 这类二次更新场景，必须先准备上班卡和已有下班卡，再进入 App 验证“更新下班卡”；不要把上班打卡和第一次下班打卡 UI 流程混进同一个目标 case。
- 负向场景必须显式准备“缺失/冲突”状态，例如无上班卡下班失败要先清空当天上班卡，重复打卡拦截要先种出同类型打卡。
- 修改或新增 case 后，检查 `expected` 是否断言目标业务结果，而不是只证明前置数据种成功。

## 业务背景

- App 包名：`com.qingtian.app_qingoa`
- 登录账号：`konglingjia / 123456`
- 打卡接口：`POST /api/punch/clock`
- 今日状态：`GET /api/punch/today-status`
- 最新打卡断言：`GET /debug/attendance/latest`
- 请求日志：`GET /debug/requests`
- 今日重置：`POST /debug/punch/reset-today`
- 时间冻结：`POST /debug/freeze-time`
- 时间恢复：`DELETE /debug/freeze-time`

### 打卡类型

| punch_type | 含义 | 规则 |
|---|---|---|
| `clock_in` | 上班卡 | 每天只能成功一次 |
| `clock_out` | 下班卡 | 上班卡完成后才能打，可重复更新 |

### 状态含义

| status | 含义 |
|---|---|
| `normal` | 正常 |
| `late` | 迟到 |
| `early_leave` | 早退 |
| `makeup` | 补卡生成 |

## 元素定位策略

优先级固定为：

```text
resource-id 精确定位 > contentDescription 语义定位 > text 定位 > 视觉/OCR 辅助 > 坐标兜底
```

不要直接依赖投屏窗口坐标。不同屏幕、scrcpy 缩放、窗口位置都会让坐标漂移。

### 关键 resource-id

| 页面 | 元素 | resource-id |
|---|---|---|
| 首页 | 菜单列表 | `com.qingtian.app_qingoa:id/rv_menu` |
| 打卡页 | 返回 | `com.qingtian.app_qingoa:id/btn_back` |
| 打卡页 | 打卡记录入口 | `com.qingtian.app_qingoa:id/btn_records` |
| 打卡页 | 上班打卡按钮 | `com.qingtian.app_qingoa:id/btn_clock_in` |
| 打卡页 | 下班/更新打卡按钮 | `com.qingtian.app_qingoa:id/btn_clock_out` |
| 打卡页 | 纬度覆盖输入 | `com.qingtian.app_qingoa:id/et_test_lat` |
| 打卡页 | 经度覆盖输入 | `com.qingtian.app_qingoa:id/et_test_lng` |
| 打卡记录页 | 记录列表 | `com.qingtian.app_qingoa:id/rv_records` |

### 关键 contentDescription

| 元素 | contentDescription |
|---|---|
| 首页考勤入口 | `qingoa_home_punch_entry` |
| 打卡记录入口 | `qingoa_punch_record_entry` |
| 上班打卡按钮 | `qingoa_punch_clock_in_button` |
| 下班打卡按钮 | `qingoa_punch_clock_out_button` |
| 更新下班打卡按钮 | `qingoa_punch_clock_out_update_button` |
| 今日日期 | `qingoa_punch_today_date` |
| 上班状态 | `qingoa_punch_clock_in_status` |
| 下班状态 | `qingoa_punch_clock_out_status` |
| 打卡点摘要 | `qingoa_punch_point_summary` |
| 纬度输入 | `qingoa_punch_test_lat_input` |
| 经度输入 | `qingoa_punch_test_lng_input` |
| 打卡记录 item | `qingoa_punch_record_item_{date}_{status}` |
| 打卡详情容器 | `qingoa_punch_record_detail_content` |
| 打卡详情类型 | `qingoa_punch_record_detail_type` |
| 打卡详情日期 | `qingoa_punch_record_detail_date` |
| 打卡详情打卡点 | `qingoa_punch_record_detail_point` |
| 打卡详情设备 | `qingoa_punch_record_detail_device` |
| 我的页补卡申诉入口 | `qingoa_mine_punch_appeal_entry` |
| 我的页补卡审批入口 | `qingoa_mine_punch_appeal_review_entry` |
| 补卡申诉日期输入 | `qingoa_punch_appeal_date_input` |
| 补卡申诉上班卡选项 | `qingoa_punch_appeal_clock_in_radio` |
| 补卡申诉下班卡选项 | `qingoa_punch_appeal_clock_out_radio` |
| 补卡申诉期望时间输入 | `qingoa_punch_appeal_expect_time_input` |
| 补卡申诉原因输入 | `qingoa_punch_appeal_reason_input` |
| 补卡申诉提交按钮 | `qingoa_punch_appeal_submit_button` |
| 补卡申诉列表 | `qingoa_punch_appeal_list` |
| 补卡申诉通过按钮 | `qingoa_punch_appeal_approve_button` |
| 补卡申诉驳回按钮 | `qingoa_punch_appeal_reject_button` |

## 标准 11 步流程

## 旧版一键 PoC 执行器

这是早期验证脚本，只用于排查单条打卡链路。日常回归优先使用 QingAgent 测试台和 `.agents/cases/attendance_*.yaml`，不要继续扩展硬编码 PoC。

前置条件：

- QingOA API 已启动，且 App 当前连接的 API 与 `--api-base` 是同一个环境。
- `adb devices` 能看到一台 `device` 状态的模拟器或真机。
- App 已安装：`com.qingtian.app_qingoa`。

成功打卡：

```bash
cd /Users/konglingjia/AIProject/QingAgent
./venv/bin/python -m qingagent.qingoa_punch_poc \
  --api-base http://127.0.0.1:8010 \
  --mode success
```

超范围失败：

```bash
cd /Users/konglingjia/AIProject/QingAgent
./venv/bin/python -m qingagent.qingoa_punch_poc \
  --api-base http://127.0.0.1:8010 \
  --mode out_of_range
```

如果 App 使用的是 Cloudflare 域名环境，把 `--api-base` 改成同一个域名：

```bash
./venv/bin/python -m qingagent.qingoa_punch_poc \
  --api-base https://oa.qingagent.top \
  --mode success
```

输出目录：

```text
/Users/konglingjia/AIProject/QingAgent/runtime/qingoa_punch_poc/<时间戳>-<模式>/
```

目录里会包含：

- `report.md`
- `01_before_punch.png`
- `02_after_punch.png`
- `attendance_latest.json`
- `requests.json`
- `debug_state.json`

无设备时只能做 API 侧烟测，不算完整 PoC：

```bash
./venv/bin/python -m qingagent.qingoa_punch_poc --skip-adb
```

1. **检查 API 服务**
   - 请求：`GET /debug/state`
   - 失败解释：API 未启动或端口不对，后续 App 操作没有断言基础。

2. **重置今日打卡**
   - 请求：`POST /debug/punch/reset-today`
   - body：`{"username":"konglingjia"}`
   - 失败解释：测试数据不可控，本轮结果不能作为证明。

3. **冻结时间**
   - 请求：`POST /debug/freeze-time`
   - body：`{"datetime":"2026-05-03 09:01:00"}`
   - 失败解释：无法稳定复现迟到/正常等时间相关规则。

4. **启动 App 并登录**
   - 优先检查本地 token；如已登录直接进入首页。
   - 失败解释：登录态或网络配置异常，不属于打卡业务失败。

5. **进入考勤打卡页**
   - 优先用 contentDescription `qingoa_home_punch_entry`。
   - 失败解释：首页菜单配置、路由白名单或 UI 定位失败。

6. **写入测试坐标**
   - 正常坐标：`lat=39.811774`, `lng=116.295234`
   - 越界坐标：`lat=39.700000`, `lng=116.100000`
   - 失败解释：坐标输入框不可定位，无法稳定复现定位场景。

7. **点击上班打卡**
   - 优先点击 `btn_clock_in` 或 `qingoa_punch_clock_in_button`。
   - 失败解释：UI 未进入可打卡状态，或控件定位失败。

8. **截图确认 UI 状态**
   - 视觉目标：上班状态显示“已完成”，按钮隐藏或不可重复打。
   - 失败解释：前端状态没有刷新，可能是 UI bug 或接口失败。

9. **后端断言最新打卡**
   - 请求：`GET /debug/attendance/latest?username=konglingjia&punch_type=clock_in`
   - 必须断言：`record != null`、`record.punch_type == "clock_in"`、`record.point_name == "晴天打卡点"`。
   - 失败解释：UI 显示成功但后端无记录，这是“前端伪成功”高价值 bug。

10. **检查请求日志**
    - 请求：`GET /debug/requests`
    - 必须找到：`POST /api/punch/clock`，`response_code == 0` 或预期错误码。
    - 失败解释：接口未发出、鉴权失败、网络失败或场景注入影响。

11. **生成测试报告**
    - 必须包含：截图、ADB 操作摘要、接口响应、debug 断言、请求日志、失败解释。
    - 失败解释：没有报告就不能复盘，无法证明 QingAgent 真正理解链路。

## 超范围场景

不要依赖真实 GPS 漂移。默认使用已知越界坐标：

```json
{
  "lat": 39.700000,
  "lng": 116.100000,
  "device_id": "android_device_001",
  "punch_type": "clock_in"
}
```

预期结果：

- 业务接口返回 `1004`
- UI 出现“不在打卡范围内”类似提示
- `/debug/attendance/latest?username=konglingjia&punch_type=clock_in` 中 `record` 仍为空
- `/debug/requests` 存在本次坐标请求日志

## 失败分类

| 分类 | 判断依据 | 处理建议 |
|---|---|---|
| 环境失败 | API 不通、App 未安装、adb offline | 先修环境，不归因业务 |
| 定位失败 | uiautomator 找不到元素，视觉也无法确认 | 补 contentDescription 或调整 UI 测试标识 |
| 前端失败 | API 成功但 UI 没刷新 | 检查 Activity 状态刷新和绑定逻辑 |
| 后端失败 | UI 成功但 debug 无记录 | 检查业务写库、事务、用户身份 |
| 规则失败 | 返回 1004/1007/1008 等预期错误码 | 按业务场景判断是否通过 |

## 最小验收标准

本 Skill 的第一版通过标准：

1. QingAgent 测试台能识别 13 条考勤用例为对应 runner 可执行。
2. 上班成功、下班成功、无上班卡下班失败、超范围、重复拦截、下班更新、记录列表、记录详情、月汇总、申诉通过、申诉驳回、重复申诉、审批权限均能形成 App/API/debug 证据链。
3. 每次运行都能输出截图、请求日志、debug 断言或明确失败原因。
4. 失败时能明确区分“环境失败 / UI 定位失败 / 前端伪成功 / 后端规则失败”。
