# X2 IRI 消息结构分析（华为 ATS9900）

> 分析日期：2026-06-22
> 来源：`TC_VoLTE2.0_监听_05_0102` — VoLTE用户被叫被监听，通话使用AMRWB编码

---

## 一、X2 IRI 消息日志格式

华为 ATS9900 的 X2 上报日志由两部分组成：

### 1. 文本译码（ASN.1 PER 解码结果）

```
流水号:  
消息名称:  iRI_CALL_Report
网络ID:  5f
时间:  2014-07-22 08:44:37
消息解释：
iRI-Report-record { -- SEQUENCE -- IRI_Parameters
    domainID {0 4 0 2 2 1 6},
    iRIversion '06'H,
    lawfulInterceptionIdentifier '31'H  -- "1",
    ...
}
```

### 2. 二进制码流（内存 dump）

```
1C EB 62 00 03 00 00 00 XX XX XX 00 XX XX XX 01 XX XX XX 00 CC CC...
```

码流头格式：
| 偏移 | 长度 | 字段 | 说明 |
|:----:|:----:|:----:|------|
| 0x00 | 4 | 固定标识 | `1C EB 62 00` (Hi3/X2) |
| 0x04 | 4 | Length | 小端序 (通常=3) |
| 0x08 | 4 | Ptr1 | ASN.1 结构地址 |
| 0x0C | 4 | Ptr2 | 上下文指针 |
| 0x10 | 4 | Ptr3 | 数据段指针 |
| 0x14 | N | Padding | `0xCC` 填充 |
| ... | — | PER数据 | `F0 72 73 00...` |

---

## 二、关键字段映射

| X2 IRI 字段 | 值示例 | 解码说明 |
|:------------|:-------|:---------|
| `domainID` | `{0 4 0 2 2 1 6}` | 固定域标识 |
| `iRIversion` | `'06'H` | IRI 版本 |
| `lawfulInterceptionIdentifier` | `'31'H` = "1" | LIID，十六进制→ASCII |
| `operator-Identifier` | `'313233'H` = "123" | OPERID，hex→ASCII |
| `network-Element-Identifier` | `'8413f5'H` (e164-Format) | CIN，反序BCD |
| `generalizedTime` | `'3230313430373232303835373535'H` = "20140722085755" | 时间戳，hex→ASCII |
| `intercepted-Call-Direct` | `'02'H` | 呼叫方向 |
| `imsChargingID` | `'706373636630362e...'H` = "pcscf06.198.bb.20140722005245" | IMS计费ID |
| `reportReason` | `'00'H` / `'03'H` / `'08'H` | X2 报告原因 |
| `callID` | `'6e6c776b...'H` = "nlwkwbiml...@192.6.170.222" | SIP Call-ID |
| `sipMessageDirection` | `'01'H` = MO / `'00'H` = MT | SIP消息方向 |
| `sipMessage` | `'494e56495445...'H` = "INVITE..." | 完整SIP消息，hex→ASCII |

---

## 三、reportReason 枚举

| 值 | 含义 | 典型场景 |
|:--:|------|---------|
| `00` | 呼叫发起 (Call Initiation) | INVITE |
| `03` | 会话进行中 (Session Progress) | 183, 180 |
| `08` | 补充业务 (Supplementary Service) | 含 SS Invoke |

---

## 四、双节点上报特征

A-SBC + I-SBC 均上报 X2，通过 Via header 区分：

| 节点 | IP | Via 特征 |
|:----:|:---:|:---------|
| A-SBC | 192.6.170.222 | `Role=3;Dpt=eb0a_*` |
| I-SBC | 192.6.170.221 | `Role=3;Dpt=7cb4_*` |

A-SBC 先上报 (Max-Forwards=N)，I-SBC 随后 (MF=N-1)。

---

## 五、报告原因：补充业务事件

当 reportReason='08'，消息含 supplementaryService 段：

```
dSS1-SS-Code '17'H     -- SS 操作码
dSS1-OperateType '05'H  -- 操作类型
```

---

## 六、关联文档

- `li/HW/LI-Protocol/` — 华为 LI 协议测试用例
- `telecom/lawful_interception/pcap-volte-sip-i-li-data-layer-analysis.md` — PCAP LI 数据层分析
