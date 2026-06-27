# Gy 口 OCS 实时计费 — Diameter Wireshark 抓包过滤方法

> 适用场景: 在 GGSN/PGW 的 Gy 口抓取 Diameter 包后, 通过 Wireshark 过滤出特定用户的 CCR/CCA 消息流程

## 1. 按手机号码过滤 CCR 消息

GGSN Gy 口上, MSISDN 携带在 `Subscription-Id-Data` AVP 中:

```wireshark
diameter.Subscription-Id-Data == "8613XXXXXXXX"
```

或按 IMSI:

```wireshark
diameter.Subscription-Id-Data == "460XXXXXXXXXXX"
```

- `86` = 中国国家码, `13XXXXXXXX` = 联通手机号
- `460` = 中国 MCC, `XXXXXXXXXXX` = 用户标识段

## 2. 按 Session-ID 关联完整 CCR-CCA 流程

从任一 CCR 消息中提取 Session-Id:

```wireshark
diameter.Session-Id == "b1.xxGGSNxx;13xxxxxxx;277543981"
```

Session-Id 格式: `<来源主机>;<高32位时间戳>;<增量>`

此条件可关联出该用户的整条 CCR-CCA 消息流程:

| 消息 | CC-Request-Type | 方向 | 说明 |
|:----|:----------------|:----|:-----|
| CCR-I | 1 (INITIAL_REQUEST) | PCEF→OCS | 初始化信用控制请求（开始计费） |
| CCA-I | — | OCS→PCEF | 初始配额授予 (Result-Code=2001) |
| CCR-U | 2 (UPDATE_REQUEST) | PCEF→OCS | 配额耗尽/阈值触发后更新请求 |
| CCA-U | — | OCS→PCEF | 续配额授予 |
| CCR-T | 3 (TERMINATION_REQUEST) | PCEF→OCS | 会话终止请求 |
| CCA-T | — | OCS→PCEF | 最终结算确认 |

## 3. 典型流程

```
GGSN (PCEF)                       OCS
  │                                │
  ├── CCR-I (INITIAL) ────────────►│  开始计费
  │◄── CCA-I (配额 + 有效期) ─────┤
  │                                │
  ├── CCR-U (UPDATE) ─────────────►│  配额用尽/定时到
  │◄── CCA-U (新配额) ────────────┤
  │                                │
  ├── CCR-T (TERMINATION) ────────►│  用户下线
  │◄── CCA-T (最终费用) ──────────┤
```

## 4. Gy 关键 AVP

| AVP Code | AVP 名称 | 类型 | 说明 |
|----------|----------|------|------|
| 415 | CC-Request-Type | Enumerated | 1=Initial, 2=Update, 3=Terminate, 4=Event |
| 416 | CC-Request-Number | Unsigned32 | 请求序号（递增） |
| 417 | Subscription-Id | Grouped | 订阅者 ID（含 type + data） |
| 418 | Subscription-Id-Type | Enumerated | 0=END_USER_IMSI, 1=END_USER_SIP_URI, 2=END_USER_NAI, 3=END_USER_PRIVATE |
| 419 | Subscription-Id-Data | UTF8String | MSISDN / IMSI 值 |
| 421 | Granted-Service-Unit | Grouped | 授予配额 (CC-Time/CC-Money/CC-Total-Octets) |
| 422 | Requested-Service-Unit | Grouped | 请求配额 |
| 423 | Used-Service-Unit | Grouped | 已用量上报 |
| 431 | Result-Code | Unsigned32 | 2001=成功, 4012=配额不足, 5002=系统错误 |
| 456 | Multiple-Services-Credit-Control | Grouped | 多业务信用控制 |
| 2011 | Reporting-Reason | Enumerated | 上报原因 (QUOTA_EXHAUSTED, VALIDITY_TIME, REREGISTRATION 等) |

## 5. Wireshark 高级过滤组合

```wireshark
# 只显示 CCR/CCA (命令码 272)
diameter.cmd.code == 272

# 只显示 CCR (R位=1 的 272 消息)
diameter.cmd.code == 272 && diameter.flags.request == 1

# 只显示 CCA (R位=0 的 272 消息)
diameter.cmd.code == 272 && diameter.flags.request == 0

# 按 CC-Request-Type 过滤
diameter.CC-Request-Type == 1    # 只显示 INITIAL
diameter.CC-Request-Type == 2    # 只显示 UPDATE
diameter.CC-Request-Type == 3    # 只显示 TERMINATION

# 按结果码过滤
diameter.Result-Code == 2001     # 只有成功的 CCA
diameter.Result-Code != 2001     # 有问题的消息

# 按某费率组过滤
diameter.Rating-Group == 100

# 按上报原因过滤
diameter.Reporting-Reason == 1   # QUOTA_EXHAUSTED
```

## 6. 参考

- RFC 4006 / RFC 8506 — Diameter Credit-Control Application
- 3GPP TS 32.251 — Telecommunication management; Charging management; Packet Switched (PS) domain charging
- 知识库: `telecom/charging/OCS_Gy_Diameter_Wireshark_Filter.md`
- 知识库: `telecom/Diameter完整消息库速查手册.md` §4 Gy
