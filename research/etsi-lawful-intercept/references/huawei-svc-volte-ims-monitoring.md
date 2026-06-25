---
title: 华为SVC_VoLTE_IMS监听场景
tags: [华为, SVC, VoLTE, IMS, LI, X1, X2, X3, iMS-IRI-Report]
---

# 华为 SVC VoLTE IMS 监听场景

## 概述

华为 SVC（Single Voice Core）场景下的 VoLTE ETSI 监听方案。IMS 采用与接入无关的集中式监听模式，通过封装 SIP 消息的方式整合 ETSI 监听。

参考标准：**ETSI ES 201 671**、**TS 102.232**

---

## 一、CS-Event 标识

所有 IMS IRI 报告（iMS-Gen-IRI-Report）都通过 **IRI-REPORT-RECORD** 消息发送。在 CS-Event 中添加了枚举值：

| 枚举值 | 名称 | 说明 |
|--------|------|------|
| 18 (0x12) | **iMS-GEN-IRI-REPORT** | 标识该报告为 IMS 类型的 IRI 报告 |

---

## 二、X3 媒体面

### X3 接口实现方式

| 监听模式 | X3 实现方式 |
|---------|------------|
| ETSI CS 监听 | 通过 ISUP/PRA/SIP 发起调用复制媒体数据 |
| IMS 拦截 | 通过 **RTP 复制** 媒体数据 |

### IP 包数据模式 X3（IMS-base / NGN）

IMS 场景下采用基于 IMS 基础监听的 IP 包数据模式的 X3：

1. 将截获对象的会话媒体流 **CC** 复制
2. 加上 **X3 接口消息头**
3. 通过 **UDP/IP** 发送给 LIG 或 LEMF

**CC（IPCC）格式**：
```
IP Header | UDP Header | RTP Header | RTP Payload
```

**解包与组装**：
- 含 RTP Payload：IGW 解包，LIG 组装
- 无 CC 的 IRI 报告：LIG 发送 CC 无效报告给 LEA

适用范围：**IMS-base** 和 **NGN**

### 各网元语音通道输出方式

| 网元 | X3 输出模式 | 原因 |
|------|-----------|------|
| SBC | 仅收发分离（TX/RX 分离） | 无混音硬件模块 |
| mAGCF/MGW | 支持收发合并 / 收发分离 | 硬件支持混音 |
| MGCF/MGW | 支持收发合并 / 收发分离 | 硬件支持混音 |

### X3 流程

用户呼叫 → SBC 检测到被监听用户 → 复制媒体流 + X3 消息头 → 发送到 LIG → SBC 无混音 → TX/RX 分离 → 2 个文件 (.1 / .2)

### X3Address

| 属性 | 说明 |
|------|------|
| 用途 | 表示被拦截目标的 X3 接口报文输出地址，与 OutputNum 功能相同 |
| 优势 | 支持未来其他扩展方式的 IP 模式和 X3 地址 |
| 类型 | **Choice** |
| 格式 | SIP URI / TEL URI 格式的 IPv4、IPv6 或 X3 地址 |

**X1SetTarget 约束**：X3Address 和 OutputNum 不能同时存在。

---

## 三、X2 信令面（基于 IMS 标准拦截）

### 上报机制

网元（如 SBC）通过 **iMS-IRI-Report** 封装成 **IRI-Report-Record** 向 LIG 上报 IRI 事件。iMS-IRI-Report 内含 **iMS-Gen-IRI-Report**，核心是完整的 SIP 消息。

三类报告信息：会话信息、通信信息、补充服务信息。

### iMS-Gen-IRI-Report 参数结构

#### 1) reportReason（4 字节）

| 取值 | 说明 |
|------|------|
| Initial | 找到拦截目标 |
| Additional | 拦截目标是新的 |
| Redirect | 重定向 |
| B2BUA | B2BUA 场景 |
| Term_And_Orig | AS 终止 INVITE，发起新呼叫 |
| Combine | 两个呼叫合并 |
| Split | 呼叫拆分两条线路 |
| Join | 参与者参加会议 |
| SupplementaryService | 补充服务报告 |

#### 2) connectionParameter

| 参数 | 说明 |
|------|------|
| I. dialogParameter | 原始对话，CallID + FromTag + ToTag(可选) |
| II. newDialogParameter | 新对话（B2BUA/Term_and_Orig/Combine） |
| III. callID | SIP CallID 头域 |
| IV. fromTag | SIP FromTag 头域 |
| V. toTag | SIP ToTag 头域 |

#### 3) additionalParameter — 取决于实现
#### 4) transitCarrier — 仅 CALEA 模式

### 方向指示

| 模式 | RTP 方向标识 | RTP 关联方式 |
|------|-------------|-------------|
| IMSBASE（SBC） | 头字节 0x51↑/0x50↓ | LIID + imschargingid |
| SIP-I（MSC/mAGCF） | 靠 ISUP 消息 | 四元组 |

### 端口协商

CC **不做端口协商**，固定为 x3port（102.232-5 IMS 方式），直接通过配置端口发送。

---

## 四、ICID（IMS 计费标识符）

| 属性 | 说明 |
|------|------|
| 生成者 | 参与 SIP 事务的第一个 IMS 实体（如 P-CSCF） |
| 特性 | 一次会话相同，IMS 网络唯一 |
| 关联 | LIID + imsChargingID（ICID）关联 RTP 流 |
| 示例 | pcscf06.198.bb.20140722005245 |

---

## 五、多号码拦截

reportReason=Additional 的 IRI，LIG 复制多个 IR 和 CC 给 LEA。

拦截目标：a) 主叫方 / b) 终止端调用者和被调用者 / c) 终止端调用者和被调用者

---

## 六、CS 与 IMS 模式选择

取决于 **LIG 和 IMS 实体（P-CSCF、S-CSCF、TAS、CCTF）的本地配置**。

---

## 七、真实 IRI 抓包解码示例

完整 13 步 VoLTE 呼叫流程的 IRI 解码数据见知识库：
`知识/telecom/lawful_interception/华为SVC_IMS_X2报告抓包示例.md`

关键观察：
1. ICID 全程不变，CallID 全程不变
2. Dialog 从 183 分配后固定
3. sipMessageDirection=01（上行）/ 00（下行）
4. P-Charging-Vector ecid 上行/下行不同
5. supplementaryService 和 transitCarrier 均为 void
