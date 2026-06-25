# SSF 实例与 OMU-ATS-CSC 信令关系分析

> 来源：A1项目 SU-A-CS / SU-B-CS 配置对比分析 + VoWiFi 架构分析
> 日期：2026-06-22

## 核心发现

SU-A-CS（PSD）和 SU-B-CS（ATB）两份 ztlig.cfg **结构完全一致**，唯一的非IP差异：
- PSD 有 **11 个 SSF** (1300~1310)
- ATB 只有 **10 个 SSF** (1300~1309)

缺少的 `SSF_1310` 绑定关系：
```
SSF_1310 → ztlig2seq=462 → ZTLIG2_462 → tneid=3 → NE_662 (OMU-ATS-CSC)
```

## OMU-ATS-CSC 是什么

华为 **SVC** (Service Control) 设备，CSCF + ATS **复用同一 IP**：

| 组件 | 角色 |
|------|------|
| **CSCF** | IMS 会话控制 (S-CSCF 或 I-CSCF) |
| **ATS** | Application Trigger Server，通过 Sh 接口从 HSS 获取位置信息 |

## VoWiFi 呼叫中的角色

```
VOWi Users → A-SBC → S-CSCF ──┬──→ I-CSCF → S-CSCF → A-SBC → VoLTE Users
                              │                       ↑
                            ATS ← HSS               ATS ← HSS
                            (获取位置)               (删除位置)
```

- ATS 从 HSS 获取 `last-utran-cell-id-3gpp` → 放入 PANI 头域
- ZTLIG2_462 (OMU-ATS-CSC) 捕获带 PANI 的 SIP 信令 → 提取位置
- 需要独立 **SSF** 做 SIP 会话管理
- MT 侧 ATS 删除该位置信息

## 部署模式判断

| 场景 | SVC 启用功能 | 是否需要额外 SSF |
|------|-------------|----------------|
| VoWiFi 全量信令 | OMU + ATS + CSCF | **需要**（苏丹 SU） |
| 仅补充业务 CDR | 仅 OMU | 不需要（ZAIN、MTN） |

**原则**：SSF 实例数 = 需要独立会话管理的 SIP 信令出口数，不直接等于网元数。

## 参考配置

| 运营商 | SVC 设备功能 | 配置表现 |
|--------|-------------|----------|
| 苏丹(SU) A站 PSD | OMU+ATS+CSCF | 11 SSF, ZTLIG2_462 带 SSF_1310 |
| 苏丹(SU) B站 ATB | 无此出口 | 10 SSF, 无 SSF_1310 |
| ZAIN PSD | 仅 OMU | 无额外 SSF |
| MTN PSD | 仅 OMU | 无额外 SSF |
