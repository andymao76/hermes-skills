# ZTLIG SSF 实例与 OMU-ATS-CSC 信令关系分析

> 原文：`~/knowledge/li/HW/hw-li-ztlig-ssf-analysis-experience.md`

## 核心发现

SU-A-CS (PSD) vs SU-B-CS (ATB) 配置对比：

| 项目 | PSD (A站) | ATB (B站) |
|------|-----------|-----------|
| SSF 实例数 | **11** (1300~1310) | **10** (1300~1309) |
| 缺少 | — | SSF_1310 (绑定 ZTLIG2_462 → OMU-ATS-CSC) |

## 原因

OMU-ATS-CSC = 华为 IMS 域融合网元，CSCF (IMS 会话控制) + **ATS (Application Trigger Server)** 复用同一 IP。

### VoWiFi 信令流

```
MO: VOWi Users → A-SBC → S-CSCF ─┬─ ATS ← HSS (获取 last-utran-cell-id-3gpp)
                                   │
MT: I-CSCF → S-CSCF → A-SBC → VoLTE Users
                ↑
              ATS ← HSS (删除该位置)
                │
              mAGCF → 2/3G Users
```

### 关键点

- ATS 通过 **Sh 接口** 从 HSS 获取/删除用户位置信息，不负责媒体面
- ZTLIG2_462 (NEID=2491250814467) 捕获 VoWiFi SIP 信令 + PANI 位置
- ZTLIG2_465 (NEID=7022, ATB-A-SBC) 捕获 IMS 信令面（无位置）
- **SSF 实例数 = 需要独立会话管理的 SIP 信令出口数**，不等于 NE 数

### 华为 SVC 部署模式

| 场景 | 运营商 | 功能 | SSF |
|------|--------|------|-----|
| VoWiFi全量 | SU | OMU+ATS+CSCF | 需要 |
| 仅补充业务CDR | ZAIN/MTN | 仅 OMU | 不需 |

## 配置对比方法论

1. 进程实例数对比 → 定位差异
2. IP 分组归类 → 区分镜像地址 vs 结构差异
3. 非 IP 差异深追 → diff | grep -v IP
4. SSF 差异追根 → ZTLIG2 → NE → 网络拓扑验证
