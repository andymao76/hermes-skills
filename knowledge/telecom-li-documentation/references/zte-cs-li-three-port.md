# ZTE CS LI 三接口参考 (HI1 + HI2 + HI3)

> 综合参考：中兴 ZXUN LIG CS 域 ETSI 三接口体系
> 来源：ZTE 官方文档 — HI1 Port 1 v1.14, HI2 Port 2 v1.30, HI3 Port 3 v1.01

## 体系架构

```
LEA 操作员 → HI1(Telnet/SSH CLI 65xx) → LIG
                                              │
                      ┌───────────────────────┼───────────────────────┐
                      ▼                       ▼                       ▼
                   X1(配置)                 X2(接收IRI)             X3(接收CC)
                      │                       │                       │
                   PS/EPC/IMS NE              │                       │
                      │                       │                       │
                   ┌─▼─────────────┐  ┌───────▼────────┐  ┌──────────▼───────────┐
                   │  HI2 ASN.1/BER │  │  HI3 ISDN/PRI  │  │  HI3 SIP-I/BICC      │
                   │  FTP/ROSE      │  │  语音 CC       │  │  多媒体 CC           │
                   └────────────────┘  └────────────────┘  └──────────────────────┘
                            全部交付至 → LEMF
```

## HI1 — 命令接口

**传输**: Telnet 或 SSH，默认提示符 `>>>`
**端口**: 标准 23/22

### 用户三级权限

| 级别 | 代码 | 角色 | 权限 |
|------|------|------|------|
| NE 超级管理员 | 260 | 系统自动创建 | 创建 261/262，管理 IP 白名单 |
| LEA 管理组 | 261 | LEA 级管理员 | 创建 262，配置通信参数 |
| LEA 操作组 | 262 | 普通操作员 | 目标增删改查 |

### 核心命令

| 命令 | 代码 | 功能 | 适用权限 |
|------|------|------|---------|
| `ADD LITGT` | 6505 | 添加拦截目标 | 261/262 |
| `DEL LITGT` | 6506 | 删除拦截目标 | 261/262 |
| `MOD LITGT` | 6507 | 修改拦截目标 | 261/262 |
| `SHW LITGT` | 6508 | 查询拦截目标 | 261/262 |
| `SHW TGTINF` | 6510 | 查询目标身份+位置 | 261/262 |
| `SET BARRING` | 6529 | 设置呼叫限制 | 261/262 |
| `CON CC` | 6531 | 连接 CS 通话内容 | 261/262 |
| `ADD OP` | 6516 | 创建操作员 | 260/261 |
| `ADD HI1IP` | 6521 | 添加白名单 IP | 260 专属 |

### ADD LITGT 关键参数

- `MCID` — LEA ID (1-250)
- `LIID` — 拦截标识 (1-25 字符)
- `TT` — 目标类型 (2=MSISDN前缀, 3=IMEI, 5=IMSI, 6=MSISDN, 8=SIP-URI, 20=ECGI)
- `TI` — 目标号码
- `IT` — 拦截类型 (1=IRI, 2=CC, 3=All)
- `SPEECHTYPE` — 语音模式 (0=Single Combined, 1=Multi-leg Separate, 2=Single Separate)
- `FD` — 拦截失败处理 (0=继续, 1=断话)
- `HI3A` — CS 域填 ISDN 号码，PS 域填 IP 地址
- `HI3PORT` — HI3 端口（当 HI3A 为 IP 时使用）

### SHW TGTINF 输出关键字段

- `STATE` — 0=关机, 2=服务中, 4=活跃
- `PSSTATE` — detach/idle/connected
- `IMSSTATE` — registered/un-registered
- `CGI` — MCC-MNC-LAC-CI 格式
- `TAI/ECGI` — EPS 域位置
- `BARRING` — Bitmap (bit0=呼出, bit1=呼入)
- `SCSCFNAME` — IMS-HSS 独有
- `ACTSSLIST` — 已激活补充业务

## HI2 — IRI 接口 (ASN.1/BER)

**传输**: ASN.1/BER over TCP/IP，通过 FTP 或 ROSE 链接
**基于标准**: 3GPP TS 33.108 V10.4.0，ZTE 有扩展
**OID**: `{itu-t(0) identified-organization(4) etsi(0) securityDomain(2) lawfulIntercept(2) threeGPP(4) hi2CS(3) r7(7) version-1(1)}`

### IRI 记录类型

| 类型 | Tag | 用途 |
|------|-----|------|
| iRI-Begin-record | A1 | 呼叫开始 |
| iRI-End-record | A2 | 呼叫结束 |
| iRI-Continue-record | A3 | 呼叫中间事件 |
| iRI-Report-record | A4 | 非呼叫事件 |
| iRI-Alarm-record | B0 | 网元告警 |

### ZTE 扩展事件 (Umts-Cs-Event, Tag 9F21)

| 值 | 事件 | 记录类型 | 说明 |
|----|------|---------|------|
| 1 | call-establishment | Begin/Cont | 呼叫建立 |
| 2 | answer | Continue | 应答 |
| 5 | release | End/Cont | 释放 |
| 6 | sMS | Report | 短信 |
| 7 | location-update | Report | 位置更新 |
| 8 | subscriber-Controlled-Input | Report | DTMF/USSD/UUS |
| 9 | switchOffEvent | Report | 关机 |
| 10 | cCLinkStateReportEvent | Report | HI3 链路状态 |
| 11 | switchOnEvent | Report | 开机（ZTE 扩展）|

### IRI-Parameters 关键字段 (BER TLV Tags)

| Tag | 字段 | 说明 |
|-----|------|------|
| 81 | lawfulInterceptionIdentifier | LIID |
| A2 | communicationIdentifier | CID(Call ID) |
| A3 | timestamp | 事件时间 |
| 84 | intercepted-Call-Direct | 1=MO, 2=MT |
| 85 | intercepted-Call-State | 1=idle, 2=setUp, 3=connected |
| A8 | locationOfTheTarget | CGI/LAI/RAI/TAI/ECGI 位置 |
| A9 | partyInformation | IMSI/IMEI/MSISDN/号码 |
| 8B | release-Reason | Q.850 释放原因 |
| 8C | nature-Of-The-intercepted-call | 0=CS, 1=SMS, 20=USSD |
| AD | serviceCenterAddress | 短信中心 |
| AE | SMS-report | 短信内容(最长270字节) |
| AA | callContentLinkInformation | HI3 链路状态 |

### PartyInformation 标识（A9 内嵌）

| 子Tag | 字段 | 编码 |
|-------|------|------|
| 81 | imei | 8 字节 MAP 格式 |
| 83 | imsi | 3-8 字节 MAP 格式 |
| 84 | callingPartyNumber | ISUP/DSS1/MAP 格式三重 CHOICE |
| 85 | calledPartyNumber | ISUP/MAP/DSS1 三重 CHOICE |
| 86 | msISDN | 1-9 字节 MAP AddressString |

### Location 位置扩展

| Tag | 类型 | 长度 | 说明 |
|-----|------|------|------|
| [2] | globalCellID | 5-7 | CGI |
| [4] | rAI | 6 | 路由区 |
| [6] | umtsLocation | 可变 | 经纬度点/圆/多边形 |
| [7] | sAI | 7 | PLMN(3)+LAC(2)+SAC(2) |
| [9] | tAI | 6 | 从 MME 获取 |
| [10] | eCGI | 8 | 从 MME 获取 |

### UMTSLocation 三种形态

- `point` — 经纬度坐标 (latitudeSign + latitude(0..8388607) + longitude(-8388608..8388607))
- `pointWithUnCertainty` — 坐标 + 不确定度 (0-127)
- `polygon` — 1-15 个点组成的多边形

## HI3 — CC 内容交付

**传输**: 标准 ISDN 电路交换呼叫
**信令协议**: ISUP / PRI / BICC / **SIP-I** (V1.01 新增)
**方向**: 单向（IIF→LEMF，反向不接通）

### Mono/Stereo 模式

| 模式 | 通道数 | 说明 |
|------|--------|------|
| Mono | 1 路 | 上行+下行混合（对应 SPEECHTYPE=0 Combined）|
| Stereo | 2 路 | 上行(Rx)+下行(Tx)分开（对应 SPEECHTYPE=2 Single Separate）|

### ISUP/BICC/SIP-I IAM 消息参数

| 参数 | 值 |
|------|-----|
| Calling party's category | 10 (ordinary calling subscriber) |
| Transmission medium | speech=3(3.1kHz), video=2(64K UDI) |
| **主叫号码** | NEID (网元标识) |
| **被叫号码** | HI3 Address (LEMF 号码) |
| Forward call indicators | 国内呼叫+ISUP全程 |

### 子地址关联（关键 — IRI↔CC 关联）

**Called Party Subaddress** (被叫方子地址)：
| 顺序 | 字段 | 说明 |
|------|------|------|
| 1 | Operator ID | 运营商标识 |
| 2 | CIN | Call Identity Number |
| 3 | CCLID | CC Link ID |

**Calling Party Subaddress** (主叫方子地址)：
| 顺序 | 字段 | 说明 |
|------|------|------|
| 1 | **LIID** | **核心关联键** |
| 2 | Direction | 方向（上行/下行） |
| 3 | Service Octets | 业务类型 |

### PRI SETUP 消息参数

与 ISUP 基本相同，Bearer Capability 写死：
- Speech: G711 A-law, 64K Circuit-Mode, CCITT
- 非语音：沿用原始呼叫 ISDN BC

## 三接口关联关系

```
HI1 ADD LITGT (配置目标)
   ├─ MCID + LIID → 用于 HI2 IRI 关联
   ├─ TT + TI → 目标身份
   ├─ IT=3 → 同时拦截 IRI+CC
   ├─ HI3A → HI3 的 LEMF 地址
   └─ SPEECHTYPE → HI3 Mono/Stereo 模式

HI2 IRI-Parameters (信令报告)
   ├─ lawfulInterceptionIdentifier = LIID ← HI1 的 LIID
   ├─ communicationIdentifier = CID ← 与 HI3 CC-Link-Identifier 关联
   └─ callContentLinkInformation → HI3 链路状态

HI3 ISDN/SIP-I 呼叫 (CC 交付)
   ├─ Calling Party Subaddress[1] = LIID ← 与 HI2 关联
   ├─ Called Party Subaddress[2] = CIN ← 与 HI2 CID 关联
   └─ Called Party Number = HI3 Address ← HI1 配置的 HI3A
```

## 返回码体系 (HI1 关键)

| 代码 | 含义 | 处理 |
|------|------|------|
| 0 | Succeed | — |
| 1 | The target has existed | 检查 LIID 或 TT+TI |
| 2 | The target does not exist | 检查输入数据 |
| 26 | Old password error | — |
| 31 | User already exists | — |
| 60 | MC still has targets | 先删目标再删 MC |
| 2001 | Same LIID or TT+TI existed | 输入不同 LIID |
