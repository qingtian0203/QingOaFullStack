---
name: QingOA 请假自动化执行入口
description: QingOA v1.7 请假/WAP/workflow 自动化测试入口。供 QingAgent 或其他 AI 定位权威 QingOA 文档、启动服务、选择 case、调用 debug 断言和排查自动化失败；不作为请假业务规则源头。
---

# QingOA 请假自动化执行入口

## 定位

这个 Skill 属于 QingOA 仓库的**自动化业务入口**。QingAgent 只提供 ADB / WAP / API / case runner / 报告等通用执行能力，不在平台仓库维护 QingOA 业务细节。

业务规则、状态机、接口契约以 QingOA 文档为准：

- `/Users/konglingjia/AIProject/AI 文档/qingoa/qingoa_v1_7_design.md`
- `/Users/konglingjia/AIProject/AI 文档/qingoa/qingoa_v1_7_execution_plan.md`

使用方式：先读上面的 QingOA 文档确认业务事实，再用本 Skill 执行自动化测试。

不要把它和打卡 PoC 混在一起：

- 打卡：App 原生页面 + ADB/uiautomator + `/debug/attendance/latest`。
- 请假：WAP 流程中心 + workflow API + `/debug/leave/latest`。

打卡相关先读 `.agents/skills/qingoa-punch-automation/SKILL.md`。

## 用例数据准备铁律

所有请假、WAP、workflow 自动化 case 都必须先判断目标行为依赖哪些流程数据，并在 `preconditions` 里显式准备。不要依赖上一条 case、当前数据库残留、某个账号刚好有待办、WAP localStorage 或人工预置状态。

设计规则：

- 每条 case 默认要可独立重复运行。先调用 `/debug/workflow/reset`、业务 debug reset 或对应清理接口，再构造本 case 需要的最小流程数据。
- 如果目标不是验证“新建申请 UI 流程”，前置流程实例、任务、审批节点优先用 API/debug endpoint 构造；WAP/App WebView 步骤只覆盖本 case 真正要验证的动作。
- 如果目标是验证“退回后重提”“审批按钮矩阵”“催办进入 urged bucket”等中间状态，必须先在前置里把流程推进到对应状态，再开始 UI/API 断言。
- 多角色场景必须显式准备 actor、token、instance、task 和 bucket，不能假设 manager 或 HR 当前正好有任务。
- 时间、附件、非法日期、重复提交等场景要显式准备冲突或边界数据，负向 case 不能靠偶然脏数据触发。
- 修改或新增 case 后，检查 `expected` 是否断言目标业务结果和 workflow 状态一致性，而不是只证明前置数据构造成功。

## 关键项目路径

| 资源 | 路径 |
|---|---|
| API 后端 | `/Users/konglingjia/AIProject/QingOaFullStack/API_QingOA` |
| App | `/Users/konglingjia/AIProject/QingOaFullStack/APP_QingOA` |
| WAP | `/Users/konglingjia/AIProject/QingOaFullStack/WAP_QingOA` |
| 业务设计源头 | `/Users/konglingjia/AIProject/AI 文档/qingoa/qingoa_v1_7_design.md` |
| 执行计划源头 | `/Users/konglingjia/AIProject/AI 文档/qingoa/qingoa_v1_7_execution_plan.md` |
| 自动化 case | `/Users/konglingjia/AIProject/QingOaFullStack/.agents/cases/` |

## 自动化入口

WAP 默认由 API 同源挂载：

```text
http://127.0.0.1:8010/wap/#/workflow
```

浏览器自动化测试时 token 获取顺序：

1. App WebView JS Bridge。
2. `localStorage` token。
3. WAP 调试登录表单，调用 `POST /api/auth/login`。

QingAgent 浏览器自动化通常走第 3 条。

## 定位策略

WAP 自动化优先用 `data-testid`，不要依赖视觉坐标。

已知关键选择器：

- `workflow-tab-{key}`，例如 `workflow-tab-todo`
- `workflow-new-leave_request`
- `leave-type-select`
- `leave-start-date`
- `leave-end-date`
- `leave-reason-input`
- `leave-submit-button`
- `workflow-action-approve`
- `workflow-action-reject`
- `workflow-action-return`
- `workflow-action-resubmit`
- `workflow-action-cancel`
- `workflow-action-urge`

如果按钮显示异常，先检查 API 响应里的 `available_actions`，再查 WAP 组件；具体动作矩阵以 QingOA v1.7 文档为准。

## 自动化 case

当前骨架文件：

- `.agents/cases/leave_2_days_manager_approve.yaml`
- `.agents/cases/leave_4_days_manager_hr_approve.yaml`
- `.agents/cases/leave_return_and_resubmit.yaml`
- `.agents/cases/leave_invalid_date_rejected.yaml`
- `.agents/cases/leave_urge_visible_in_urged_bucket.yaml`
- `.agents/cases/wap_leave_workflow_e2e.yaml`

`urge_visible_in_urged_bucket` 归入 `leave_workflow_api`，因为催办是 workflow engine 能力，不属于考勤打卡业务线。

case 中的断言建议区分两类：

```yaml
- type: assert
  value: "$step3.response.data.status == manager_approved"

- type: http_call
  method: GET
  url: "/debug/leave/latest?username=konglingjia"
```

不要把表达式断言和 HTTP 调用混成同一种字符串。

## 最小执行链路

1. 重置 workflow：`POST /debug/workflow/reset?username=konglingjia`。
2. 登录 WAP。
3. 新建请假申请。
4. 进入详情页，保存 `process_instance_id`。
5. manager 审批。
6. 如果超过阈值，HR 继续审批。
7. `GET /debug/leave/latest` 断言最终状态。
8. `GET /debug/workflow/state` 断言 instance / task / leave_request 一致。

任何一步和业务预期不一致时，先回到 QingOA v1.7 文档确认业务规则，再判断是自动化脚本问题、WAP 问题还是 API 问题。

## 验证命令

API 侧：

```bash
cd /Users/konglingjia/AIProject/QingOaFullStack/API_QingOA
./venv/bin/python -m pytest tests/test_v1_api.py
```

WAP 侧：

```bash
cd /Users/konglingjia/AIProject/QingOaFullStack/WAP_QingOA
npm run build
```

QingAgent 平台侧（如果改动了平台执行器）：

```bash
cd /Users/konglingjia/AIProject/QingAgent
./venv/bin/python -m compileall qingagent
```
