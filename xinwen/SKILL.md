---
name: xinwen
description: 新闻情报雷达 — 专为信息过载场景设计的新闻分级决策工具。
  自动将海量新闻分为🔴关键/🟡关注/⚪一般/🔇噪音四级，语义去重合并重复报道，
  根据用户画像自适应排序，输出带影响判断和行动建议的决策简报。
  支持快速扫描/每日情报/领域深挖/追踪更新四种模式。
  SkillHub 导入版。
category: research
---

# 新闻情报雷达

> 不是告诉你发生了什么，而是帮你判断什么该看、为什么重要、下一步该怎么办。

## 核心能力

- **四级智能分级**：基于多源覆盖度、热度、画像匹配度、信源可信度四维评分
- **语义去重合并**：同一事件多源报道自动合并，保留不同视角
- **决策简报**：按价值而非来源分类，每条关键情报附带影响判断和建议行动
- **用户画像自适应**：读取 USER.md 和 MEMORY.md，自动匹配关注领域
- **话题追踪联动**：一键生成追踪命令模板，持续跟踪关键事件
- **30+信源支撑**：全球科技、开源社区、国内资讯、金融财经、AI深度五大分类
- **快速扫描模式**：10秒内只看最关键的3-5条

## 触发方式

新闻雷达、情报雷达、今日简报、有什么重要的、科技早报、财经早报、AI早报、快速看看、扫描一下

## 使用方式

```bash
# 快速扫描（只看关键和关注，5条以内）
python3 {skill_dir}/scripts/intelligence.py --mode quick

# 每日情报（完整抓取+全量分析）
python3 {skill_dir}/scripts/intelligence.py --mode daily

# 领域深挖（单领域详细分析）
python3 {skill_dir}/scripts/intelligence.py --mode topic --topic AI深度

# 追踪更新（按关键词追踪）
python3 {skill_dir}/scripts/intelligence.py --mode trace --keyword "GPT-5"

# JSON 输出
python3 {skill_dir}/scripts/intelligence.py --mode quick --json
```

## 分级说明

| 等级 | 含义 | 判定规则 |
|------|------|----------|
| 🔴关键 | 必须关注 | 3+源报道，或评分≥65，或与核心领域高度匹配 |
| 🟡关注 | 值得留意 | 2源报道，或评分40-64，或与领域间接相关 |
| ⚪一般 | 可选浏览 | 单源报道，热度一般，评分<40 |
| 🔇噪音 | 已折叠 | 重复/广告/营销/无关 |

## 信源一览

| 分类 | 信源 |
|------|------|
| 全球科技 | Hacker News、Product Hunt、TechCrunch、The Verge、Ars Technica |
| 开源社区 | GitHub Trending、GitHub Show HN、V2EX |
| 国内资讯 | 36氪、微博热搜、IT之家、腾讯科技、知乎热榜、B站热门 |
| 金融财经 | 东方财富、雪球、华尔街见闻、财联社 |
| AI深度 | HuggingFace Papers、ArXiv AI、8个AI Newsletter RSS |

## 文件结构

```
scripts/
├── intelligence.py    # 主引擎
├── fetch_sources.py   # 30+信源抓取
├── classifier.py      # 智能分级
├── deduplicator.py    # 语义去重合并
├── profiler.py        # 用户画像
├── tracker.py         # 话题追踪
└── briefing.py        # 简报格式化
instructions/         # 情报指令模板
references/           # 分级规则/去重策略/信源配置
```

## 依赖

```bash
pip3 install requests beautifulsoup4
```

## 来源

SkillHub 导入
