# OWLS 虚实碰撞（SNS Mapping）原理

## 整体流程

Web 添加虚拟账号 → Kafka → 前端舆情爬取 → Flink 入库 GP → 离线碰撞（Auto/Manual）→ 置信度计算 → 结果展示

## 碰撞原理

虚账号（人工添加的社交账号）与实数据（Hive 中 `trs_m_tls_sns` 的 SNS 详单）按**应用特定时间窗口**匹配：

| 应用 | 文本 | 图片 | 视频 |
|------|------|------|------|
| Facebook | ±2min | ±2min | ±5min |
| Twitter | ±2min | ±2min | ±5min |
| YouTube | — | — | ±5min |
| Instagram/TikTok/VK | ±2min | ±2min | ±5min |

## 置信度公式

```
score = W1 × (scoreAll / acc_cnt)
      + W2 × (bs_cnt / max(bs_cnt, msis_cnt))
      + W3 × (acc_cnt / max(msis_cnt, acc_cnt))
```

W1+W2+W3=1

- `W1` 正向匹配：平均每次虚拟账号匹配得分（`sigmoid(1/cnt)` 打分，少量高排他碰撞得分高）
- `W2` 反向匹配：碰撞覆盖面
- `W3` 一对一：虚拟账号覆盖度

## 单次打分

```
onescore = sigmoid(1/cnt) × typeCoe
```

typeCoe：图片/视频 ×0.2，文本 ×1.0

## 详细文档

详见 `~/knowledge/research/OWLS_虚实碰撞置信度逻辑.md`
