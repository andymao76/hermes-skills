---
name: local-first-audit
description: 系统本地化审计 — 扫描 Hermes 环境（SKILL、知识库、cron、tools）识别 LLM 依赖点，评估哪些可替换为本地方案，标记必须保留 LLM 的环节供人工审批
version: 1.0.0
author: hermes-agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [audit, local-first, optimization, llm-dependency, efficiency]
    related_skills: [hardware-diagnostics, security-audit-sop, second-brain, skill-creator, knowledge-base]
---

# Local-First Audit

## 何时触发

当用户要求以下任意一项时，加载本 Skill：
- "分析系统，优化尽量从本地解决问题"
- "看看哪些地方用 LLM 是浪费的"
- "做一次系统本地化审计"
- "检查 SKILL 和知识库的本地化程度"
- "哪些环节必须 LLM，哪些可以本地"

## 核心理念

LLM token 是昂贵且有限的资源。每次调用前自问：**这个操作用本地工具能否完成？**

三档分类：
| 等级 | 说明 | 示例 |
|------|------|------|
| **本地** | 零 LLM 消耗，纯本机进程 | rg/fd/grep/jq/Python 脚本 |
| **可优化** | 当前走 LLM，但有本地替代方案 | 日报草案用模板生成，LLM 仅润色 |
| **必须 LLM** | 本地无法替代语义理解/推理/创造 | 代码重构、翻译、视觉理解 |

## 审计步骤

### 步骤 1：摸清本地工具清单

```bash
# 核心搜索工具
which rg fdfind fzf bat jq 2>/dev/null

# 本地语义搜索
kb-index status

# 本地知识库索引工具
kb-index status 2>/dev/null || echo "kb-index 未初始化"
```

关键：
- `rg` (ripgrep) = 内容搜索，本机进程，零 token
- `fd` (`fdfind` on Debian) = 文件名搜索，本机进程，零 token
- `fzf` = 终端模糊匹配
- `kb-index` = TF-IDF + LSA 本地语义搜索（完全离线）
- `jq` = JSON 处理
- `bat` = 语法高亮阅读（如有）

### 步骤 2：审计知识库

```bash
# 知识库规模
find ~/knowledge -name "*.md" | wc -l
du -sh ~/knowledge/

# 本地索引状态
kb-index status

# 收件箱积压
find ~/knowledge/00_INBOX -name "*.md" | wc -l

# 分类结构
ls ~/knowledge/ | sort
```

### 步骤 3：审计 SKILL 体系

```bash
# 全部 skill 列表
ls ~/.hermes/skills/ | sort

# 检查每个 skill 的 trigger 描述，判断是否需要 LLM 推理
# 重点关注：daily_report, weekly_report, auto-skill-precipitator, xinwen 等
```

每个 Skill 问三个问题：
1. 这个 skill 的触发条件是纯本地可判断的吗？（文件匹配 vs 语义理解）
2. 这个 skill 的执行流程中哪些步骤真正需要 LLM？
3. 能否加一个本地硬门槛（如文件数量>N 才触发 LLM）？

### 步骤 4：审计 cron 任务

```bash
# 通过 cronjob action='list' 获取完整列表
# 关注：
# - no_agent=true 的已是最优
# - 带 LLM 的 cron 能否改为 no_agent + 纯脚本？
```

分类标准：
- `no_agent=true` + `script=` → 纯本地，最佳
- `no_agent=false` + 纯数据采集 → 可改 no_agent
- `no_agent=false` + 需要语义理解 → 必须 LLM

### 步骤 5：标记必须 LLM 的环节

以下环节确实需要 LLM，本地无法替代：

| # | 环节 | 原因 | 替代尝试 |
|---|------|------|---------|
| 1 | 复杂代码生成/重构 | 需要理解上下文语义、变量作用域 | 简单替换用 sed/patch |
| 2 | 自然语言理解用户意图 | 模糊请求需要语义解析 | 明确指令可免 |
| 3 | 网页搜索/信息获取 | 结果摘要需要相关性判断 | curl+jq 抓取但不理解内容 |
| 4 | 翻译 | 跨语言语义转换 | 简单单词用字典 |
| 5 | 创造类（图片/文案） | 视觉创意/风格 | ASCII 图用本地 |
| 6 | 复杂 RAG 问答 | 需要链路推理 | 直答式查询走 kb-index |
| 7 | 图片/截图理解 | 视觉理解 | OCR 用 tesseract |
| 8 | 浏览器动态交互 | 页面语义理解 | 固定页面走 curl |

### 步骤 6：输出结构化报告

以三级分类呈现审计结果：

```
=== 本地化审计报告 ===

## 已经在本地
- [工具] rg/fd → 内容/文件名搜索
- [数据] kb-index → 1736 文件本地语义索
...

## 可以优化
- [cron] 日报生成 → 改本地模板+LLM润色
- [skill] 技能沉淀 → 加本地 hard-filter
...

## 需要人工选择（必须LLM）
1. 代码重构 — 需要语义理解
2. Web搜索 — 需要信息摘要
3. 翻译 — 跨语言转换
...
```

## 优化建议速查

| 观察 | 建议 |
|------|------|
| `fd` 命令不存在，但 `fdfind` 存在 | `alias fd=fdfind` |
| 知识库 > 1000 文件但未索引 | `kb-index --full` |
| cron 含 LLM 但只做数据采集 | 改 `no_agent=true` + `script=` |
| skill 触发关键词匹配 | 走本地关键词，不经过 LLM |
| 收件箱分类规则不全 | 扩展 `inbox_sorter.py` 规则表 |

## Pitfalls

- **不要保存环境级失败**（"fd 未安装"、"rg 版本低"）为 skill 规则。这些是环境状态，变一次你就要改一次 skill。记在 memory 里或直接在 report 里说。
- **不要写 "X tool is broken" 的否定声明**。工具后来修好了你就成了虚假约束。记录修复步骤，而不是禁止使用。
- **不要存 session 快照**（"2026-06-30 audit found 21 cron jobs"）。存审计方法，而不是某次的结果。
- **kb-index 索引旧了** → 提示用户 `kb-index --full` 重建
- **LLM 环节先标记再执行** → 未经人工确认不自动切换模式
- **本地搜索和 LLM 搜索不是互斥的** → 先本地，命中率不足再 LLM

## 关联 Skill

- **hardware-diagnostics** — 硬件层面健康检查，与此 skill 互补（硬件+软件全栈审计）
- **security-audit-sop** — 安全审计 SOP，同样走"检查→报告→修复"模式
- **second-brain** — 知识库收件箱管理，审计时可以检查 inbox 积压
- **skill-creator** — 审计后发现缺失 skill 时可创建
