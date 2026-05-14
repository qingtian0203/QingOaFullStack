# AGENTS.md

## 项目定位

QingOA 是 QingAgent 自动化测试能力的第一个全栈验证项目，包含 App、API、WAP 和 debug endpoint。它是被测对象，不是 QingAgent 平台本身。

因此，QingOA 的业务规则、页面标识、接口契约、自动化 case 和 debug 断言语义都应维护在本仓库；QingAgent 只负责通用执行能力（ADB / WAP / API / case runner / 报告）。

## AI 入口地图

| 任务类型 | 先读 |
|---|---|
| QingOA 打卡自动化、三场景打卡、`/debug/attendance/latest` | `.agents/skills/qingoa-punch-automation/SKILL.md` |
| QingOA 请假 / WAP / workflow 自动化、v1.7 case | `.agents/skills/qingoa-leave-workflow-automation/SKILL.md` |
| 自动化 case 骨架 | `.agents/cases/*.yaml` |
| 版本设计和规划 | `/Users/konglingjia/AIProject/AI 文档/qingoa/` |
| Git 提交前缀规则 | `.agents/skills/git-commit-agent-prefix/SKILL.md` |

## 目录边界

- `.agents/skills/`：QingOA 专属 AI 工作流入口，描述“怎么围绕 QingOA 自动化测试工作”。
- `.agents/cases/`：QingOA 自动化测试 case 骨架，跟随 QingOA 业务和页面变化维护。
- `/Users/konglingjia/AIProject/AI 文档/qingoa/`：版本设计、执行计划和长期规划。
- QingAgent 仓库：只维护平台执行器和通用能力，不维护 QingOA 业务事实。

## 自动化 case 数据准备铁律

新增或修改 `.agents/cases/*.yaml` 前，必须先判断该 case 要验证的业务行为依赖哪些已有数据，并把这些数据写入 `preconditions`，不要依赖上一个 case、当前数据库残留、App 登录缓存或人工预置状态。

通用原则：

- 每条 case 必须尽量可独立重复运行，先清理会影响断言的数据，再构造本 case 需要的最小数据。
- 如果目标不是验证“创建前置数据的 UI 流程”，前置数据优先用 API/debug endpoint 构造；UI 步骤只覆盖本 case 真正要验证的行为。
- 时间相关业务必须在前置里显式冻结时间，并在需要的阶段重新冻结，不能依赖真实当前时间。
- 负向场景也要显式准备“缺失状态”或“冲突状态”，例如先清空上班卡再验证无上班卡下班失败。
- 多角色流程必须在前置里准备角色、流程实例、待办/已办状态，不能假设某个账号当前正好有任务。
- 修改 case 时同时检查 `expected` 是否仍然断言本 case 的目标结果，而不是只证明前置数据种成功。

## Git 提交规则

在本仓库创建、amend、squash 或改写任何 git commit 前，AI Agent 必须先识别自己是谁，并给 commit subject 加固定前缀：

- Codex 的提交必须以 `[codex]` 开头
- Antigravity 的提交必须以 `[antigravity]` 开头

示例：

```text
[codex] 修复 QingOA App Token 过期处理
[antigravity] 增加打卡页面
```

如果无法确认当前 Agent 身份，先问用户。不要创建无前缀提交。

Codex 使用的详细工作流见 `.agents/skills/git-commit-agent-prefix/SKILL.md`。
