# skill.yaml → SKILL.md 格式转换参考

## 背景

社区生态（agentskills.io、wondelai/skills）使用 `skill.yaml` 格式定义技能，但 Hermes Agent 使用 `SKILL.md`（YAML frontmatter + Markdown 主体）。

当用户提供 `skill.yaml` 格式的技能定义时，需要转换为 Hermes 的 `SKILL.md` 格式。

## skill.yaml 典型结构

```yaml
name: skill-name
description: 技能描述
version: 1.0.0
author: 用户自定义

triggers:
  - pattern: "触发词1"
    action: action_name
  - pattern: "触发词2"
    action: action_name

memory:
  - key: config_key
    description: 配置说明
    default:
      setting: value

actions:
  action_name:
    prompt: |
      执行指令...

help: |
  使用示例：
  - "示例命令"
```

## SKILL.md 目标结构

```markdown
---
name: skill-name
description: 技能描述，包含触发场景
trigger: 触发词1、触发词2
---

# 技能标题

## 触发方式

- `触发词1` → 动作说明
- `触发词2` → 动作说明

## 工作流

1. 步骤说明

## 配置项

| 参数 | 默认值 | 说明 |
|------|--------|------|
| setting | value | 说明 |
```

## 字段映射表

| skill.yaml | SKILL.md frontmatter | 说明 |
|------------|---------------------|------|
| `name` | `name` | 直接复制 |
| `description` | `description` | 直接复制 |
| `triggers[].pattern` | `trigger` | 合并为逗号分隔字符串 |
| `author` | 可选 frontmatter | 可保留 |
| `actions[].prompt` | Markdown 主体 | 转为 ## 章节和小节 |
| `memory[].default` | 配置表格 | 转为 Markdown 表格 |
| `help` | 使用示例章节 | 转为 ## 使用示例 |

## 常见陷阱

1. **skill.yaml 的 `triggers` 是正则匹配列表**，Hermes 的 `trigger` 是逗号分隔的关键词列表。用户习惯的触发词（如"记一下"、"生成日报"）可以直接写，不需要正则
2. **skill.yaml 的 `memory` 是结构化存储**，Hermes 中没有对应的运行时存储。配置项转为 SKILL.md 中的说明性表格，行为逻辑由 agent 根据 SKILL.md 描述自动判断
3. **Hermes 的 SKILL.md 没有 `actions` 映射**——所有逻辑都在 Markdown 主体中描述，agent 根据语言理解自动触发对应行为
4. **skill.yaml 的标准安装方式是 `git clone`**，Hermes 的标准安装是复制到 `~/.hermes/skills/`。如果用户从社区仓库安装，先 `git clone` 再复制 `skills/*` 目录

## 转换步骤

1. 提取 `name`、`description` → frontmatter
2. 合并 `triggers[*].pattern` → `trigger` 字段（去重，取最自然的说法）
3. 将 `actions[*].prompt` 重写为自然语言 ## 章节（去掉花括号模板语法，改为平实的流程描述）
4. 将 `memory[*].default` 转为配置表格
5. 将 `help` 转为使用示例章节
6. 补全 frontmatter 的 `name` 和 `description` 字段
7. 验证：`skill_view(name)` 确认可加载
