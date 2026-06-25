# HW LI 方案选型矩阵（从 telecom-protocol-code-stream-analysis 引用）

完整文档见：
- `knowledge/li/HW/hw-li-solution-selection-guide.md`（详细选型矩阵）
- `telecom/hw-li` skill 的 `references/solution-selection-guide.md`

## 速查

| 场景 | 主推方案 |
|------|:--------:|
| VOBB（小容量AGCF） | 分布式监听IP复制 |
| VOBB（大容量AGCF） | 集中监听IP复制 |
| VoLTE(RCS) | 分布式监听IP复制 |
| FMC融合 | FMC监听IP复制 |
| 非华为SBC | 集中监听 |
