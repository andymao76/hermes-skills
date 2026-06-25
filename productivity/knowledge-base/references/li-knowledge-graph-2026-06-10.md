# LI 知识图谱构建记录（2026-06-10）

本会话产出 15 篇笔记的 LI 技术资料知识图谱，经历 3 次迭代完善。

## 迭代历程

| 迭代 | 笔记数 | 新增内容 | 修正 |
|------|--------|---------|------|
| v1 | 7 | 5GC/EPC/7750/SAM/ASN.1/EVE-NG | — |
| v2 | 13 | +HW/ZTE/Ericsson/UTIMACO/LI标准/OWLS平台 | 总索引标签、框图等距 |
| v3 | 15 | +2G/3G核心网、+NSN LI体系 | NISS→SICMS、厂商框增至5个 |

## 关键用户修正记录

| 修正 | 说明 |
|------|------|
| "L1" → "LI" | Lawful Intercept vs Level 1 |
| 缺少HW CS/PS | 华为电路域+分组域 |
| 缺少ZTE/爱立信/UTIMACO | 中兴/爱立信/Utimaco LI体系 |
| 缺少2G/3G | GSM/UMTS核心网、HLR/HSS、IMS |
| 缺少NSN | 诺西LI体系（待补充） |
| NISS → SICMS | 管理平台名称修正 |
| 框图重叠 | 等距布局公式修复 |

## 等距布局公式

```
gap = (canvas_w - N × box_w) / (N + 1)
box_x[k] = left_margin + gap + k × (box_w + gap)
# N=5框, canvas_w=1200, box_w=210
# gap = (1200 - 1050) / 6 = 25
# x: 25, 260, 495, 730, 965
```

## 产出文件

- `~/knowledge/research/li-tech-library-index.md` — 总索引
- `~/knowledge/research/li-knowledge-graph.html` — HTML图谱
- `~/knowledge/research/li-knowledge-graph.svg` — SVG矢量图
- 15 篇独立笔记在 `~/knowledge/research/`
