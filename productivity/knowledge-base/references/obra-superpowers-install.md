# Obra Superpowers 安装与使用

## 安装

```bash
git clone https://github.com/obra/superpowers.git ~/.hermes/skills/superpowers
```

安装后自动包含 14 个 SKILL.md 文件，Agent 在需要时自动加载。

## 包含的子技能

| 子技能 | 用途 |
|--------|------|
| brainstorming | 展开需求规格，等待确认 |
| test-driven-development | RED-GREEN-REFACTOR 严格模式 |
| systematic-debugging | 先诊断再修复 |
| subagent-driven-development | 派生子代理 + 两阶段审查 |
| verification-before-completion | 验证通过才算完成 |
| writing-plans | 编写可执行计划 |
| requesting-code-review | 代码审查流程 |
| worktree-skills | Git worktree 管理 |

## 安装验证

```bash
find ~/.hermes/skills/superpowers -name "SKILL.md" | wc -l
# 预期输出: 14
```

## 参考

- 官方仓库: https://github.com/obra/superpowers
- 224k stars, 19.9k forks, MIT 协议
- 支持 Claude Code / Codex CLI / Gemini CLI / Cursor
