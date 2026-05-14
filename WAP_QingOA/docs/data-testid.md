# QingOA WAP v1.7 自动化定位清单

本文记录 v1.7 流程中心 WAP 页面给 QingAgent 自动化测试使用的稳定 DOM 定位点。自动化脚本优先使用 `data-testid`，再退回文本识别。

## 流程中心

| 场景 | data-testid | 说明 |
| --- | --- | --- |
| Tab 导航 | `workflow-tab-{key}` | key 值如 `new` / `todo` / `urge` / `running` / `returned` / `done` |
| 新办入口 | `workflow-new-{template_id}` | 例如请假入口 `workflow-new-leave_request` |
| 待办任务 | `workflow-task-{task_id}` | 点击进入流程详情 |
| 流程实例 | `workflow-instance-{instance_id}` | 催办/进行中/退回/已完成列表点击入口 |
| 退回空态 | `workflow-empty-returned` | 退回 Tab 无数据时的断言点 |

## 请假申请

| 场景 | data-testid | 说明 |
| --- | --- | --- |
| 表单容器 | `leave-create-form` | 新建请假页面已打开 |
| 请假类型 | `leave-type-select` | `annual` / `sick` / `personal` |
| 开始日期 | `leave-start-date` | `YYYY-MM-DD` |
| 结束日期 | `leave-end-date` | `YYYY-MM-DD` |
| 天数预览 | `leave-days-preview` | 用于断言是否进入 HR 二审提示 |
| 请假原因 | `leave-reason-input` | 文本输入 |
| 提交按钮 | `leave-submit-button` | 成功后跳详情页 |

## 流程详情

| 场景 | data-testid | 说明 |
| --- | --- | --- |
| 详情头部 | `workflow-detail-head` | 流程标题、申请人、状态 |
| 请假业务信息 | `leave-detail-business` | 请假类型、日期、天数、原因 |
| 退回原因 | `leave-return-reason` | 退回状态下展示 |
| 时间线 | `workflow-timeline` | 容器 |
| 时间线节点 | `workflow-timeline-{node_key}` | 如 `workflow-timeline-manager_review`、`workflow-timeline-hr_review` |
| 审批区 | `workflow-review-actions` | 当前登录人有待办时出现 |
| 审批备注 | `workflow-review-note` | 审批/驳回/退回备注 |
| 通过按钮 | `workflow-action-approve` | 调 `available_actions` 中的 approve |
| 驳回按钮 | `workflow-action-reject` | 调 `available_actions` 中的 reject |
| 退回按钮 | `workflow-action-return` | 调 `available_actions` 中的 return |
| 重提表单 | `leave-resubmit-form` | returned 后申请人可见 |
| 重提类型 | `leave-resubmit-type` | 重新选择请假类型 |
| 重提开始日期 | `leave-resubmit-start-date` | 重新计算天数 |
| 重提结束日期 | `leave-resubmit-end-date` | 重新计算天数 |
| 重提原因 | `leave-resubmit-reason` | 修改原因 |
| 重提按钮 | `leave-resubmit-button` | 调 resubmit |
| 取消按钮 | `workflow-action-cancel` | 申请人取消 |
| 催办按钮 | `workflow-action-urge` | 申请人催办 |

## 状态约定

- 请假退回状态统一为 `returned`。
- WAP 不从 `leave.status` 判断是直属上级退回还是 HR 退回。
- 如果需要判断退回节点，读取 `timeline[*].node_key`：`manager_review` 或 `hr_review`。
