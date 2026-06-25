---
name: fact-check-tools-comparison
category: research
description: 辟谣/去伪存真工具对比指南。Snopes、Kaval、PolitiFact、AFP Fact Check、Google Fact Check Explorer 等工具的适用场景和选型建议。
---

# 辟谣 / 去伪存真工具对比指南

## 触发条件

- 用户问 "Snopes好不好"、"最好的辟谣工具"、"验证消息真假"、"fact check" 等
- 需要验证一条消息、截图、链接的真伪
- 比较不同的辟谣平台

## 核心工具对比

| 工具 | 适合场景 | 能力 | 费用 | 评分 |
|:-----|:---------|:-----|:----|:----:|
| **Snopes** | 查已有城市传说/网络传言（US为主） | 1994年至今辟谣数据库 | 免费 | ⭐⭐⭐⭐ |
| **Kaval** | 实时验证消息/图片/链接 | AI引擎，145+来源，WhatsApp机器人 | 免费 | ⭐⭐⭐⭐⭐ |
| **Google Fact Check Explorer** | 聚合搜索已有辟谣结论 | 跨平台聚合IFCN认证 | 免费 | ⭐⭐⭐⭐ |
| **PolitiFact** | 美国政客言论验证 | Truth-O-Meter评级 | 免费 | ⭐⭐⭐⭐ |
| **AFP Fact Check** | 国际/亚洲/非洲内容 | 法新社团队85+国家 | 免费 | ⭐⭐⭐⭐ |
| **Reuters Fact Check** | 全球新闻事实核查 | 路透社团队 | 免费 | ⭐⭐⭐⭐ |

## 选型决策树

```
用户需要验证一条消息
├─ 是中文/亚洲/国际内容？
│  ├─ 是 → AFP Fact Check / Reuters
│  └─ 否 → 继续
├─ 是政治言论？
│  ├─ 是 → PolitiFact
│  └─ 否 → 继续
├─ 是城市传说/网络奇谭？
│  ├─ 是 → Snopes
│  └─ 否 → 继续
├─ 需要最快出结果？
│  ├─ 是 → Kaval（粘贴链接/图片/文字）
│  └─ 否 → 继续
└─ 查已有结论？
   └─ Google Fact Check Explorer
```

## 使用流程

1. **确定内容类型**：文字消息/图片截图/链接/视频
2. **选工具**：Kaval（最快）→ Google FCE（查结论）→ Snopes/AFP（深度查）
3. **交叉验证**：至少2个独立来源结论一致才可信
4. **注意**：2026年AI生成假内容激增，优先用支持图片分析的工具

## 常见误区

- ❌ Snopes不能查实时消息，只能查已有的辟谣文章
- ❌ 不要只看一个来源就下结论
- ❌ 中文互联网谣言的覆盖度普遍不足，需组合多个工具
- ✅ 最佳组合：Kaval（实时） + Google FCE（聚合） + Snopes/AFP（深度）

## 相关资源

- https://www.snopes.com/
- https://toolbox.google.com/factcheck/explorer
- https://www.politifact.com/
- https://factcheck.afp.com/
- https://www.reuters.com/fact-check/
- https://kaval.app/ (2026 AI fact-check)
