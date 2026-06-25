---
name: fact-checking-tools-comparison
category: research
description: 辟谣/去伪存真工具对比指南 — Snopes/Kaval/Google Fact Check/PolitiFact/AFP，各工具优劣与选型建议
version: 1.0
author: Hermes Agent
license: MIT
platforms: [CLI, Telegram, Discord]
---

# 辟谣/去伪存真工具对比

## 工具矩阵

| 工具 | 最佳用途 | 覆盖范围 | 速度 | 费用 | 综合评分 |
|:-----|:---------|:---------|:----:|:----:|:--------:|
| **Snopes** | 英文城市传说/网络传言/历史谣言 | 美国为主，30年积累 | 🐢中 | 免费 | ⭐⭐⭐ (专但窄) |
| **Kaval** | 即时验证消息/截图/链接/文本 | 全球145+来源，AI驱动 | ⚡秒级 | 部分免费 | ⭐⭐⭐⭐⭐ |
| **Google Fact Check Explorer** | 聚合搜索已知辟谣 | 全球IFCN认证机构 | ⚡快 | 免费 | ⭐⭐⭐⭐ |
| **PolitiFact** | 美国政客言论Truth-O-Meter | 美国政治 | 🐢中 | 免费 | ⭐⭐⭐⭐ |
| **AFP Fact Check** | 国际/亚洲/英文辟谣 | 全球，法新社记者团队 | 🐢中 | 免费 | ⭐⭐⭐⭐ |
| **事实查核实验室(台湾)** | 繁体中文谣言 | 台湾为主 | 🐢中 | 免费 | ⭐⭐⭐ |
| **澎湃明查** | 简体中文热点查证 | 中国大陆 | 🐢中 | 免费 | ⭐⭐⭐ |

## 最佳组合方案（2026）

> **Kaval（实时） + Google Fact Check Explorer（查历史） + Snopes（查经典传说） = 三件套**

| 场景 | 首选工具 | 备选 |
|:-----|:---------|:-----|
| 紧急验证一条消息/图片/链接 | **Kaval** | Google Fact Check |
| 查互联网经典传说/城市奇谈 | **Snopes**（30年沉淀，无法替代） | 无 |
| 查已有辟谣结论 | **Google Fact Check Explorer** | AFP |
| 查美国政客言论 | **PolitiFact** | Snopes |
| 查国际新闻/南亚/中东内容 | **AFP Fact Check** | Kaval |
| 查简体中文热点 | **澎湃明查 + 微信辟谣助手** | - |

## 注意事项

- 辟谣工具滞后于谣言传播速度，不能100%依赖
- 中文内容辟谣覆盖最差，需要多源交叉验证
- Snopes 不擅长：实时分析新鲜claim、图片/视频/链接验证、国际/中文内容
