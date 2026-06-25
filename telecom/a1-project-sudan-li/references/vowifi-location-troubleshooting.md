# VoWiFi 位置信息不显示排查指南

## 场景描述

VoWiFi 呼叫的 tcpdump 抓包中能提取到 cell-id 和 WiFi 公网 IP，但 OWLS Web 界面上位置信息未显示。

## 典型特征（来自 A1 项目实际排查）

### 呼叫信令路径

```
UE (WiFi) ──IPsec── ePDG ──GTP── PGW ──SGi── P-CSCF/SBC ── IMS Core
                          ↓
                SIP INVITE 携带 P-Access-Network-Info
                → SBC 可附加 last-utran-cell-id-3gpp
                → ZTLIG 提取位置 → OWLS TMC Record → Kafka → Web
```

### 关键数据示例（华为 HW LI + ZTLIG）

```json
// OWLS TMC JSON 有 Location（接入面）
{
  "NetworkType": 11,           // E-UTRAN (LTE)
  "LocationType": 1,           // 呼叫实时位置
  "Location": "6340704523F4C", // MCC.MNC.CellID
}

// OWLS TMC JSON 无 Location（IMS信令面）
{
  "NetworkType": 13,           // IMS 信令面
  // 无 LocationType / Location 字段
}
```

## SIP P-Access-Network-Info 头域详解

### 标准格式

| 接入类型 | 参数示例 |
|---|---|
| LTE (VoLTE) | `3GPP-E-UTRAN-FDD; utran-cell-id-3gpp=634.07.04523F4C` |
| Wi-Fi (VoWiFi) | `IEEE-802.11;"sbc-domain=atbpcscf01.ims.mnc007.mcc634.3gppnetwork.org";"ue-ip=10.200.212.64";"ue-port=5060";"Wlan-ue-local-ip=196.202.142.135";"Wlan-ue-local-port=47746"` |
| GERAN (2G) | `3GPP-GERAN;cgi-3gpp=6340703FF64FD;network-provided` |
| E-UTRAN 扩展 | `3GPP-E-UTRAN;utran-cell-id-3gpp=xxx;"sbc-domain=psdpcscf01..."` |

### VoWiFi IEEE-802.11 PANI 参数说明

| 参数 | 含义 | 示例值 |
|---|---|---|
| `sbc-domain` | P-CSCF/SBC 域名 | `atbpcscf01.ims.mnc007.mcc634.3gppnetwork.org` |
| `ue-ip` | UE 在 ePDG 隧道内的 IP | `10.200.212.64` |
| `ue-port` | UE SIP 信令端口 | `5060` |
| `Wlan-ue-local-ip` | **UE 的 WiFi 公网 IP** | `196.202.142.135` |
| `Wlan-ue-local-port` | UE 的 WiFi 本地端口 | `47746` |

### SBC 附加的扩展参数

在 VoWiFi 场景中，SBC（如华为 atbpcscf01）可能在 IEEE-802.11 PANI 末尾**附加 LTE 小区信息**：

```
P-Access-Network-Info: IEEE-802.11;
  "sbc-domain=atbpcscf01.ims.mnc007.mcc634.3gppnetwork.org";
  "ue-ip=10.200.212.64";"ue-port=5060";
  "Wlan-ue-local-ip=196.202.142.135";"Wlan-ue-local-port=47746";
  "last-utran-cell-id-3gpp=6340704523F4C"
```

**关键发现：**
- `last-utran-cell-id-3gpp` 是 **SBC 附加的非标准扩展参数**，非标准 PANI 的 `utran-cell-id-3gpp`
- 它代表 UE **最后注册的 LTE 小区**，而非当前 WiFi 连接的物理位置
- 当 SBC 转发 SIP 消息到网络内部时（ue-ip 从 UE 隧道 IP 变为 SBC 自身 IP），该参数不一定出现在每一跳
- 该参数只在 SBC 内部转发路径中出现，UE 侧的 IEEE-802.11 PANI 中不含此参数
- HW ZTLIG 能正确从 `last-utran-cell-id-3gpp` 中提取 cell ID 写入 OWLS TMC 的 Location 字段

## OWLS LigCdr 中的位置字段

### LocationType 取值含义

| LocationType | 含义 | 来源 |
|---|---|---|
| 1 | 呼叫实时位置 (Call-related) | SIP INVITE/UPDATE 的 PANI |
| 2 | 紧急呼叫位置 | 紧急呼叫 |
| 4 | 注册/附着位置 | SIP REGISTER 的 PANI |
| 5 | 位置更新 | TA/LA Update |

### NetworkType 取值含义

| NetworkType | 含义 |
|---|---|
| 0/1/2 | GSM/GERAN (2G) |
| 3/4 | UTRAN (3G) |
| 10/11 | E-UTRAN (LTE/VoLTE) |
| 13 | IMS (SIP 信令面) |
| 14/15 | NR (5G) |
| 20 | WLAN (WiFi) |

## 排查步骤

### 步骤 1：确认 Kafka 消息中是否含有位置信息

从筛选文件或 Kafka topic 中提取 LigCdr 消息：

```bash
grep -E "Location|LocationType" 120120415.txt | head -20
# 或
kafka-console-consumer --bootstrap-server localhost:9092 \
  --topic OWLS_TMC_REALTIME --from-beginning --max-messages 100 |
  grep "120120415" | python -m json.tool
```

### 步骤 2：检查同一个 CidNum 是否存在多条记录

同一 CID 可能先发 IMS 无位置、后发接入面有位置：

```
14:53:13 → NetworkType=13 (IMS),       无 Location  ← 先到达
14:53:16 → NetworkType=11 (E-UTRAN),   Location=xxx  ← 3秒后到达
14:53:20 → NetworkType=11 (E-UTRAN),   Location=xxx  ← 180 Ringing
14:53:24 → NetworkType=11 (E-UTRAN),   Location=xxx  ← 应答
14:53:34 → NetworkType=11 (E-UTRAN),   Location=xxx  ← 通话结束
```

### 步骤 3：确认 Web UI 的 LocationType 显示逻辑

- 检查 OWLS Web 是否只展示 `LocationType=4`，忽略 `LocationType=1`
- 直接查数据库确认该记录的 `location` 和 `locationtype` 字段

### 步骤 4：分析 tcpdump 中的 PANI 原始内容

```bash
# 从 pcap 搜索特定号码的 SIP 消息
tcpdump -r bond1_20260616_145309.pcap0 -A 2>/dev/null |
  grep -A5 "P-Access-Network-Info" | head -40

# 搜索筛选文件中已提取的 Location 值是否在 pcap 中出现
tcpdump -r bond1_20260616_145309.pcap0 -A 2>/dev/null |
  grep -oP 'P-Access-Network-Info: [^\n]+' | sort -u
```

### 步骤 5：验证端到端数据链路

```
UE SIP INVITE (IEEE-802.11 PANI)
  → SBC 转发 (可能附加 last-utran-cell-id-3gpp)
  → ZTLIG X2 接口解析
  → OWLS TMC Kafka 消息 (Kafka topic: OWLS_TMC_REALTIME / OWLS_TMC_OFFLINE)
  → OWLS Web 后台入库与展示
```

在每一步验证位置数据的完整性和一致性。

## 常见根因对照

| 根因 | 验证方法 | 修复方向 |
|---|---|---|
| LocationType=1 被 Web 忽略 | 检查 OWLS Web 代码的 location 显示逻辑 | 修复Web展示逻辑，支持 LocationType=1 |
| CidNum 去重取了无位置的IMS记录 | 按时间查看 CidNum 的完整记录序列 | 修改去重逻辑，优先取有位置信息的记录 |
| Location 字段入库但前端未渲染 | 直接查数据库该记录的所有字段 | 前端补全 location 字段渲染 |
| NetworkType 映射过滤 | 确认 Web 是否对 NetworkType=11 的位置做了特殊过滤 | 调整过滤条件 |
| **混合接入类型 PANI 解析失败** | 检查 pcap 中同一 SIP 消息是否同时包含多种接入类型（如 GERAN+WiFi） | 升级 ZTLIG 版本或调整解析策略 |

## pcap 分析要点

当需要从 pcap 中确认 VoWiFi 位置信息时，注意以下几点：

1. **bond1 接口可能混杂多号码流量** — 你的 pcap 中可能包含其他号码的 LTE 小区信息，不全是目标号码的
2. **VoWiFi PANI 是 IEEE-802.11** — 不含标准 `utran-cell-id-3gpp`，而是 `Wlan-ue-local-ip`（公网 WiFi IP）
3. **SBC 附加的 `last-utran-cell-id-3gpp`** — 这才是 OWLS Location 的原始来源，需在有 `sbc-domain` 参数的 PANI 中查找
4. **同一 Call-ID 可能多次 INVITE** — 前几次可能 IMS-only 无位置，最后一次接入面才有
5. **UE 信息可从 User-Agent 获取** — 例如 `User-Agent: iOS/26.5 iPhone` 确认终端类型

### pcap 分析速查

```bash
# 1. 查看所有 PANI 类型分布
tcpdump -r bond1.pcap -A 2>/dev/null |
  grep -oP 'P-Access-Network-Info: [^\n]+' | sort -u

# 2. 查找特定号码的 SIP 消息
tcpdump -r bond1.pcap -A 2>/dev/null | grep -B5 -A15 "From.*0415"

# 3. 提取完整 INVITE 消息
tcpdump -r bond1.pcap -A 2>/dev/null | grep -A30 "INVITE tel:0123406778" | head -50

# 4. 查找 Wlan-ue-local-ip 公网 IP
tcpdump -r bond1.pcap -A 2>/dev/null | grep -oP 'Wlan-ue-local-ip=[^";]+'

# 5. 查找 last-utran-cell-id-3gpp
tcpdump -r bond1.pcap -A 2>/dev/null | grep -oP 'last-utran-cell-id-3gpp=[^";\n]+'
```

### 完整 PANI 行提取技巧（tcpdump 截断处理）

`tcpdump -A` 输出中，长 PANI 行可能被截断跨多段。此时 `grep -oP` 无法匹配完整行。

**方法：用 `Wlan-ue-local-port` 作为标记锚点，配合 grep -A1 查看下一行是否还有参数：**

```bash
# 定位包含 WiFi 端口号的 PANI 行，并显示下一行
tcpdump -r bond1.pcap -A 2>/dev/null | grep -A1 "Wlan-ue-local-port=47746"
```

输出中的关键模式：
```
..."Wlan-ue-local-port=47746"                                         ← 截断无续行
P-Charging-Vector: ...
---
..."Wlan-ue-local-port=47746";"last-utran-cell-id-3gpp=6340704523F4C" ← 完整含 cell ID
P-Charging-Vector: ...
```

**原理：** 当 `Wlan-ue-local-port=47746` 后面跟随 `;` 分号而非换行时，说明 PANI 还有后续参数——`last-utran-cell-id-3gpp` 就在这个续段中。这是定位 VoWiFi cell ID 的核心技巧。

## Pcap vs 筛选日志对比验证方法论

这是排查位置不显示问题的**核心方法**：同时分析 pcap 抓包和 ZTLIG 筛选日志，对比 SIP PANI 中的原始位置信息和 OWLS TMC 消息中的提取结果。

### 数据链路各层验证

| 数据层 | 工具 | 确认项 |
|---|---|---|
| SIP 原始消息 | `tcpdump -r pcap -A` | PANI 中的 `last-utran-cell-id-3gpp` 或 `cgi-3gpp` |
| ZTLIG X2 日志 | 原始 ZTLIG `X2_HW_IMS_MsgProc` 日志 | 确认 From tag、Call-ID、CidNum 对应关系 |
| OWLS TMC Kafka | 筛选的 txt 文件（ZtligKafkaProduceMsgByKey） | `Location` + `LocationType` + `NetworkType` |
| Web 展示 | 客户反馈 | 界面上是否渲染位置 |

### 对比验证结论汇总（A1 项目实际案例）

| 呼叫 | 时间 | Pcap SIP PANI 位置 | OWLS TMC 提取结果 | 一致性判定 |
|---|---|---|---|---|
| 呼叫一 | 14:53:13~34 | `IEEE-802.11` + `last-utran-cell-id-3gpp=6340704523F4C` | `LocationType=1, Location=6340704523F4C, NetworkType=11` | ✅ **完全一致** |
| 呼叫二 | 14:59:42~51 | `3GPP-GERAN;cgi-3gpp=6340703FF64FD` + `IEEE-802.11` | **NetworkType=13, 无 Location** | ❌ **不一致** |

**发现 1（正向验证）：** `last-utran-cell-id-3gpp` 被 ZTLIG 正确解析为 `LocationType=1` + `Location=6340704523F4C` + `NetworkType=11`，说明 HW LI 对 VoWiFi 场景下 SBC 附加的 LTE 小区扩展参数具有解析能力。

**发现 2（负向验证）：** 当 SIP 消息同时携带 GERAN CGI 和 IEEE-802.11 两种接入类型时，ZTLIG 仅输出 NetworkType=13 的无位置记录，**混合接入类型导致位置解析失败**。

## 混合接入类型 PANI 导致位置丢失

### 现象

一条 SIP 消息同时包含两种 PANI 接入类型时（`3GPP-GERAN` + `IEEE-802.11`），ZTLIG 华为 LI 系统无法正确解析位置信息。

### 触发条件

- SIP 消息在核心网不同接口之间传递时被多次插入/替换 PANI
- UE 同时注册在 2G(GERAN) 和 WiFi 上
- SBC 或 P-CSCF 转发时添加了与 UE 原始 PANI 不同类型的接入信息
- 在 bond1 接口抓包中可见同一 SIP 消息携带多种接入类型

### pcap 排查命令

```bash
# 统计 pcap 中所有 PANI 接入类型分布
tcpdump -r bond1_wifi.pcap -A 2>/dev/null |
  grep -oP 'P-Access-Network-Info: ([^;]+)' | sort | uniq -c | sort -rn
```

如果目标号码的 SIP 消息同时包含 `3GPP-GERAN` 和 `IEEE-802.11`，则位置丢失风险高。

## 排查命令速查

```bash
# 筛选文件查找位置信息
grep -E "Location|LocationType" 120120415.txt | head -20

# 查找特定 CidNum 的完整时序
grep "atbpcscf01.19a.8315" 120120415.txt | grep -E "EventDetail|Location"

# 对比 pcap 和 日志中的 cell ID 是否一致
grep "6340704523F4C" 120120415.txt
tcpdump -r pcap -A | grep "6340704523F4C"

# 搜索从 UserPart 解析出的 IMSI/IMPI
grep "fromUserPart\[" 120120415.txt | head -10

# 查看所有 Call-ID 分布
grep "CidNum" 120120415.txt | grep -oP '"CidNum":"[^"]+"' | sort -u

# Kafka consumer
kafka-console-consumer --bootstrap-server localhost:9092 \
  --topic OWLS_TMC_REALTIME --from-beginning --max-messages 100

# ES 查询
curl -XGET 'http://localhost:9200/owls_tmc/_search?q=msisdn:249120120415&pretty'

# Greenplum 查询
psql -U daedb -d bigdata -c \
  "select capturetime, locationtype, location, networktype \
   from hts_lig_hi2 where msisdn='249120120415' order by capturetime;"
```
