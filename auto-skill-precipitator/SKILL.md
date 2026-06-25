---
name: auto-skill-precipitator
description: 自动技能沉淀管道 — 每次任务完成后自动分析交互模式，判断是否应沉淀为新 Skill。无需人工触发，先写草案标记 draft，待用户确认后激活。覆盖 Pattern 识别、草案生成、去重、确认流程。
version: 1.0.0
category: devops
metadata:
  hermes:
    tags: [automation, skill-creation, pattern-recognition, pipeline]
    related_skills: [skill-creator, knowledge-closed-loop, self-improvement]
---

# 自动技能沉淀管道

## When to Use

始终加载（后台模式）。在以下场景触发 Pattern 分析：
- 完成一次故障排查（多个终端/文件操作后）
- 完成一次技术调研（搜索+提取+分析步骤后）
- 完成一次配置部署（多个命令步骤后）
- 用户说了"搞定了""解决了""可以了"等完成信号
- Session 结束前自动运行一次分析

## Quick Reference

| 阶段 | 动作 | 产出 |
|------|------|------|
| Pattern 识别 | 分析会话步骤序列 | 判定是否可复用 |
| 去重检查 | 搜索已有 Skills | 排除重复 |
| 草案生成 | 生成 YAML+步骤草稿 | draft SKILL.md |
| 用户确认 | 通知用户审核 | 激活/拒绝 |

## Procedure

### 1. Pattern 识别

任务完成后，自动分析会话中的操作序列：

```python
patterns = {
    "fixed_steps": True,      # 有固定操作步骤?
    "reusable": True,         # 跨场景可复用?
    "has_commands": True,     # 包含 Shell 命令?
    "has_pitfalls": True,     # 有踩坑记录?
    "complexity": "medium",   # low/medium/high
}
```

**可沉淀判断矩阵：**

| 条件 | 是否沉淀 |
|------|---------|
| 固定步骤 + 可复用 + 含命令 | ✅ 强推荐 |
| 固定步骤 + 可复用 | ✅ 推荐 |
| 仅固定步骤 | ⚠️ 建议再观察 |
| 纯事实/知识 | ❌ 走知识库非Skill |

### 2. 去重检查

草案生成前，搜索已有 Skills 避免重复：

```bash
# 按关键字搜索现有技能
grep -ri "关键词" ~/.hermes/skills/*/SKILL.md | grep "description\|name"
```

如果已有覆盖度 > 80% 的 Skill，标记为"已有覆盖"而非新建。

### 3. 草案生成

生成 draft SKILL.md，标记为 `status: draft`：

```yaml
---
name: proposed-skill-name
description: 草稿说明
status: draft
source_session: YYYYMMDD_HHMMSS
version: 0.1.0
---
```

写入 `~/.hermes/skills/drafts/<name>/SKILL.md`（drafts 目录，不干扰正式技能）。

### 4. 用户确认

通过飞书/终端消息通知用户：

```
📦 自动检测到可沉淀 Skill 草案
名称: xxx
来源: 今天会话
建议分类: devops/software-development
查看: ~/.hermes/skills/drafts/xxx/SKILL.md
确认安装: skill_manage action=create ...
忽略: 无操作自动清除
```

## 沉淀脚本调用

```bash
# 手动触发当前会话分析
python3 ~/.hermes/scripts/skill-precipitator.py

# 查看待确认草案
ls ~/.hermes/skills/drafts/
```

## Pitfalls

| 陷阱 | 说明 |
|------|------|
| ❌ 过度沉淀 | 一次性操作不要生成 Skill（如"今天改了个配置"） |
| ❌ 命名过窄 | 不用会话名如 fix-xxx-today，用类级名 |
| ❌ 不覆盖正式技能 | 草案必须用户确认后才激活，不能自动安装 |
| ❌ 不检查重复 | 生成草案前必须搜索已有技能 |
| ❌ 依赖不存在的 session DB | session-transcript.jsonl 可能有多个消息共享同一 session_id，需去重后用最新消息。agent.log 正则解析可能因格式变化失效。推荐同时扫描知识库 worklog/ 目录作补充源。 |

## Verification

- [ ] draft 写入 `~/.hermes/skills/drafts/` 目录
- [ ] 草案已去重（不覆盖已有技能）
- [ ] 用户已收到通知（飞书/终端）
- [ ] 不干扰正式技能加载
