---
name: git-commit-agent-prefix
description: QingOaFullStack 项目的 git 提交前缀规则。凡是在本仓库创建 commit、生成 commit message、amend、squash 或改写提交信息前都使用此 skill，要求 Codex 和 Antigravity 先识别自身身份，并在提交标题最前面加 [codex] 或 [antigravity]。
---

# Git 提交 Agent 前缀规则

## 规则目标

任何 AI Agent 在 `QingOaFullStack` 仓库里创建或修改 git commit 前，都必须明确标记“这次提交是谁做的”。

## 必须使用的提交前缀

运行 `git commit` 前，先识别当前 AI Agent 身份：

- 当前是 Codex 时，提交标题必须以 `[codex]` 开头。
- 当前是 Antigravity 时，提交标题必须以 `[antigravity]` 开头。
- 如果无法确认当前 Agent 身份，先问用户，不要创建无前缀提交。

前缀必须放在 commit subject 的最前面。

示例：

```text
[codex] 增加 QingOA 服务控制 Tab
[codex] fix: handle token expiry from home fragment
[antigravity] 增加 Android 打卡页面
[antigravity] docs: 更新 API base URL 说明
```

## 提交流程

1. 确认用户明确要求提交。不要仅因为文件变了就自动提交。
2. 执行 `git status --short`，避免把无关的用户改动一起 stage。
3. 根据当前 Agent 身份选择 `[codex]` 或 `[antigravity]`。
4. commit subject 格式必须是 `[agent] <正常提交说明>`。
5. 如果是 amend 或修改已有提交信息，已有合法前缀应保留；只有当前缀与实际执行提交的 Agent 不一致时才替换。

## 注意事项

- 不要重复前缀。比如 `[codex] [codex] 修复问题` 应改成 `[codex] 修复问题`。
- 不要把前缀放到 conventional commit 类型后面。应使用 `[codex] feat: ...`，不要使用 `feat: [codex] ...`。
- 不要从 `git config user.name`、分支名、IDE 名称或历史提交里推断 Agent 身份。
- Antigravity 的工作不要标 `[codex]`，Codex 的工作不要标 `[antigravity]`。
