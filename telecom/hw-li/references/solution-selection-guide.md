# HW LI 方案选型矩阵

## 六大方案

| 方案 | 名称 | 核心网元 | 适用场景 |
|:----:|------|----------|---------|
| 一 | 集中监听IP复制 | ATS + CSC + CCTF + MRP | 大容量AGCF，非华为SBC |
| 二 | 分布式监听IP复制 | ATS + SBC + MGCF | 所有场景（主推） |
| 三 | FMC监听IP复制 | ATS + CSC + CCTF + MRP + SBC | VOBB+VoLTE(RCS) |
| 四 | 集中监听SIP呼叫 | ATS + CSC + CCTF + UMG | 监听中心不接受IP复制 |
| 五 | 集中监听窄带呼叫 | ATS + CSC + CCTF + UMG | TDM方式，不接受改造 |
| 六 | 分布式监听SIP呼叫 | ATS + SBC + MGCF | 监听中心不接受IP复制 |

## 选型优先级

IP复制（方案一/二/三）> 引导为IP复制 > FMC（方案三）> SIP呼叫（方案四/六）> 窄带（方案五）

## 关键约束

- VoLTE(RCS)方案：集中监听IP复制非主推（有限制）
- TDM/SIP呼叫：不建议用于VoLTE方案
- 云化限制：CCTF/MGW云化无路标；MRP云化IMS12.1未落地
- AGCF容量>33%时需配置SE测算成本

完整文档：`knowledge/li/HW/hw-li-solution-selection-guide.md`
