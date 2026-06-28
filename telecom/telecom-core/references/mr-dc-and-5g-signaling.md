# 5G 组网方式及双连接（MR-DC）参考

## SA vs NSA

| | SA (Standalone) | NSA (Non-Standalone) |
|--|----------------|---------------------|
| 核心网 | 5GC | EPC 或 5GC |
| 接入网 | NR 独立 | NR + LTE 联合 |
| 控制面 | NR | LTE 或 NR |
| 代表 | Option2, Option5 | Option3/4/7 系列 |

## MR-DC (Multi-RAT Dual Connectivity) 九种选项

### Option3 系列 — EN-DC (E-UTRA-NR Dual Connectivity)
- **核心网**：EPC
- **MN（主节点）**：eNB（LTE）
- **SN（辅节点）**：gNB（NR）

| 选项 | 承载分裂位置 | 特点 |
|------|------------|------|
| Option3 | eNB 做 MCG Split Bearer | 数据在 LTE 侧分裂 |
| Option3A | gNB 建 SCG Bearer | 承载不分裂 |
| Option3X | gNB 做 SCG Split Bearer | 数据在 NR 侧分裂 |

**协议栈**：MN(eNB) ↔ EPC 用 S1；MN ↔ SN 用 X2；控制面密钥源自 EPC。

### Option4 系列 — NE-DC (NR-E-UTRA Dual Connectivity)
- **核心网**：5GC
- **MN**：gNB（NR）
- **SN**：ng-eNB（eLTE eNB）

| 选项 | 承载分裂位置 |
|------|------------|
| Option4 | gNB 做 MCG Split Bearer |
| Option4A | ng-eNB 建 SCG Bearer |

### Option7 系列 — NGEN-DC (NG-RAN E-UTRA-NR Dual Connectivity)
- **核心网**：5GC
- **MN**：ng-eNB（eLTE eNB）
- **SN**：gNB（NR）

| 选项 | 承载分裂位置 |
|------|------------|
| Option7 | ng-eNB 做 MCG Split Bearer |
| Option7A | gNB 建 SCG Bearer |
| Option7X | gNB 做 SCG Split Bearer |

## 5G 信令流程概要

### NR 初始接入（SA，核心 11 步）

1. UE → gNB: Random Access (Msg1~Msg4)
2. UE → gNB: RRC Conn Req
3. gNB → UE: RRC Conn Setup（初始BWP、定时器）
4. UE → gNB: RRC Conn Setup Comp（PLMN、AMF、NAS）
5. gNB → AMF: Initial UE Message
6-9. AMF ↔ UE: 鉴权 + 加密
10. AMF → gNB: INIT CONTEXT Setup Req
11. gNB → UE: UE Capability Enquiry/Info
12-13. gNB ↔ UE: 安全模式
14-15. gNB ↔ UE: RRC Reconfig（激活BWP）
16. gNB → AMF: INIT CONTEXT Setup Rsp
17-19. PDU Session 建立（5QI、QoS Flow、DRB）

### 切换类型

| 类型 | 路径 | 特点 |
|------|------|------|
| 站内切换 | 同 gNB | A3 测量 + RRC Reconfig |
| Xn 切换 | S-gNB ↔ T-gNB | 直接交互，PATH SWITCH 更新 |
| NG 切换 | S-gNB → AMF → T-gNB | 经核心网转发 |
| 异系统 | NR ↔ LTE | 经 5GC ↔ EPC Relocation |

### 双连接基本流程

| 流程 | 用途 |
|------|------|
| SN Addition | 创建 SN 上 UE 上下文，建立双连接 |
| SN Modification | 修改双连接参数，MN/SN 均可发起 |
| SN Release | 释放双连接，MN/SN 均可发起 |
| SN Change | 辅节点切换（换一个 SN） |
| MN Handover | 主节点切换（可带/不带 SN Change） |
