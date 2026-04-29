# AGENTS.md

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
