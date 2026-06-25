# VoWiFi ZTLIG 双网元处理机制 — SBC INVITE 分叉与双 NE 架构

## 概述

在 A1 项目（苏丹 Sudani 网络）的 VoWiFi 合法监听场景中，华为 ZTLIG 系统存在**双 ZTLIG 实例**同时拦截同一呼叫的架构。每个 VoWiFi 呼叫在 IMS 核心网中存在**两条 INVITE 信令路径**（SBC 分叉转发），导致两个 ZTLIG 实例看到的信令内容不同，进而产生不同的 Location 提取结果。

---

## 一、SBC INVITE 分叉机制（核心发现）

SBC `atbpcscf01` 每通 VoWiFi 呼叫发出 **两条 INVITE**：

### 两条 INVITE 对比

| 对比项 | INVITE #1（S-CSCF 路径） | INVITE #2（RN 路由路径） |
|--------|------------------------|------------------------|
| **Request-URI** | `tel:0123406778` | `tel:+249-123406778;rn=2491250814467` |
| **From header** | `sip:+249****0415@ims.mnc007.mcc634.3gppnetwork.org` | `tel:+249****0415` |
| **From-tag 模式** | 随机字母数字混合（如 `tV0Vbg11J2`） | 随机小写（如 `aseh2aeo`） |
| **P-Asserted-Identity** | 无 cpc 参数 | 带 `cpc=ordinary` |
| **P-Access-Network-Info** | ❌ 通常不携带或已剥离 | ✅ 携带完整 PANI + `last-utran-cell-id-3gpp` |
| **ZTLIG OWLS TMC 消息** | NetworkType=13 (IMS)，无 Location | NetworkType=11 (E-UTRAN)，有 Location |
| **消息长度** | 335 字节 | 379~403 字节（含 Location 时更长） |
| **hi2->type** | 00 (同呼叫同一类型) | 与 #1 一致 |
| **是否存在 Debug X2 日志** | 有，From 为 `sip:` 格式 | 有，From 为 `tel:` 格式 |

### 日志中的典型表现

```
# INVITE #1 (14:53:13) — 无位置
X2 sendLen=2809, INVITE tel:0123406778;phone-context=ims...
From: <sip:+249****0415@ims.mnc007.mcc634.3gppnetwork.org>;tag=tV0Vbg11J2
→ 输出 OWLS TMC: NetworkType=13, 无 Location

# INVITE #2 (14:53:16) — 有位置
X2 sendLen=2898, INVITE tel:+249-123406778;rn=2491250814467 SIP/2.0
From: <tel:+249****0415>;tag=aseh2aeo
P-Asserted-Identity: <sip:+249****0415@...;cpc=ordinary>,<tel:+249****0415;cpc=ordinary>
→ 输出 OWLS TMC: NetworkType=11, LocationType=1, Location=6340704523F4C
```

### 后续信令全成对出现

从 INVITE 之后的每条 SIP 响应都按两条 INVITE 各发一份：

```
183 Session Progress → From tag tV0Vbg11J2 + From tag aseh2aeo
180 Ringing           → 同上
200 OK (Connect)     → 同上
ACK                   → 同上
BYE                   → 同上
200 OK (BYE)         → 同上
```

ZTLIG 为每个 From-tag 独立生成 OWLS TMC 消息，因此在同一 CidNum 下可见相同 EventDetail 有 2 条记录。

---

## 二、双 ZTLIG 网元架构

### 两个实例的配置

| 对比项 | ztlig2:462 | ztlig2:465 |
|--------|-----------|-----------|
| **NEID** | `2491250814467` | `7022` |
| **VNEID** | 3 | 6 |
| **OperID** | 2048 | 123 |
| **进程 ID** | 462 | 465 |
| **拦截点** | 在 `rn=` 路由路径上 | 在 IMS Core 侧 |
| **能收到 INVITE #2 吗** | ✅ 能（带 rn 的 INVITE） | ❌ 不能 |
| **能提取 Location 吗** | ✅ 能（当 PANI 有 last-utran-cell-id-3gpp） | ❌ 不能（只看到 IMS 信令面） |

### 拦截示意图

```
SBC atbpcscf01
  │
  ├── INVITE #1 (tel:0123406778) ──→ S-CSCF ──→ ...
  │                                    │
  │                                ztlig2:465 (NEID=7022)
  │                                仅看到 IMS 面信令
  │                                始终 NetworkType=13, 无 Location
  │
  └── INVITE #2 (tel:...;rn=2491250814467) ──→ 通过 RN 路由
                                       │
                                   ztlig2:462 (NEID=2491250814467)
                                   能看到完整 PANI
                                   可提取 NetworkType=11 + Location
```

### NEID 与 RN 的关系

注意 INVITE #2 中的 `rn=2491250814467` — 这个路由号码（Routing Number）**等于 ztlig2:462 的 NEID**。这说明 ZTLIG 实例的 NEID 可能直接关联到 SBC 发出的路由参数，ztlig2:462 被部署在 RN 路由路径上从而能截获带 PANI 位置的 INVITE。

---

## 三、CidNum 命名规律

格式：`{sbc主机名}.{分支标识}.{相关值}.{时间戳}`

```
atbpcscf01.19a .8315 .20260616125313    ← 呼叫一（10秒通话）
atbpcscf01.19b .885f .20260616125229    ← 被立即 CANCEL 的呼叫
atbpcscf01.195 .fefe .20260616125942    ← 呼叫二（11秒通话，混合PANI）
atbpcscf01.195 .1123 .20260616131918    ← 呼叫三（打给0123499990）
```

| 段 | 含义 | 示例 |
|----|------|------|
| SBC 主机名 | P-CSCF/SBC | `atbpcscf01` |
| 分支标识 | SBC 的业务分支/trunk | `19a`, `19b`, `195` |
| 相关值 | 随机/递增相关码 | `8315`, `885f`, `fefe`, `1123` |
| 时间戳 | YYYYMMDDHHmmss | `20260616125313` |

同一通呼叫的不同事件共享相同 CidNum（含相同分支+相关值+时间戳前缀）。

---

## 四、SBC 预探测模式（Canceled Call Ahead）

每通成功的 VoWiFi 呼叫之前，SBC 通常先发出一条 **被立即 CANCEL 的测试 INVITE**，然后再发起真正的呼叫。

### 日志中的典型时序

```
14:52:29  INVITE #1 (CidNum: atbpcscf01.19b.885f.20260616125229)
           From: <sip:+249****0415@ims...>;tag=l5td22CiNu
14:52:30  CANCEL （立即取消，~1秒后）
14:52:34  SIP MESSAGE（配置信息下发）→ 200 OK
14:52:37  SIP MESSAGE（配置信息下发）→ 200 OK
14:52:37  → SIP 200 OK（对 MESSAGE 的响应）

14:53:13  真正的呼叫开始 (CidNum: atbpcscf01.19a.8315.20260616125313)
           INVITE #1 + INVITE #2 → 完整呼叫流程
```

### 该模式的意义

| 观察 | 说明 |
|------|------|
| **CidNum 分支不同** | 预探测用 `19b`，正式呼叫用 `19a`，SBC 按不同分支标识区分 |
| **间隔约 44 秒** | 预探测 INVITE 到正式呼叫之间约 44 秒，期间有 MESSAGE 交互（配置下发） |
| **SIP MESSAGE 内容** | `MESSAGE sip:+249****0415@ims...` 和 `200 OK`，可能是 ePDG/IMS 侧的配置推送 |
| **CDR 去重影响** | 预探测的 CidNum 不同（`19b.885f` vs `19a.8315`），不会与被正式呼叫混淆 |
| **只出现在 ztlig2:462** | 预探测的 INVITE 仅被 ztlig2:462 捕获（462 在 RN 路由上能看到完整信令） |

> **注意**：此模式仅看到一次日志，不能确定是 SBC 的固定行为还是特殊情况。如果未来多例验证为固定流程，需纳入 ZTLIG 去重和 CDR 归并逻辑的考量。

## 五、ZTLIG 日志信号模式速查

### EventDetail 映射

| EventDetail | SIP 事件 | sipCallReportType | hi2->type |
|------------|---------|------------------|-----------|
| 10 | INVITE（呼叫开始） | a1 | 00 |
| 12 | 呼叫转移/呼转 | — | — |
| 14 | 180 Ringing（振铃） | a2 | 02 |
| 11 | 200 OK（接通） | a3 | 03 |
| 13 | BYE（释放） | a4 | 01 |

### 关键日志入口

```log
# 呼叫事件入口（IPDR 生成）
[ZtligKafkaProduceMsgByKey] topic[OWLS_TMC_REALTIME] leaid[1] msg[{...}]

# 收到 SIP 消息的 DEBUG 入口
[ProcSsfMsg] sipCallMsg fromUserPart[+249****0415] ,toUserPart[0123406778], sipCallReportType[a1], liid[17746]

# 从 hash 表获取目标
[ProcSsfCallReport]:get target_id[+249****0415] from hash table! liid[17746]
[ProcSsfCallReport] callingNUM[+249****0415], calledNum[0123406778], hi2->type[00]!

# SIP 消息体（X2 子模块透传）
X2 submodule:[X2_HW_IMS_MsgProc]sendLen = 2809, liid = [17746] target[+249****0415] sip msg[INVITE ...]
```

### 从日志识别双 INVITE

查看 `X2_HW_IMS_MsgProc` 中的 INVITE From-tag：

- **From `sip:` 格式**（如 `tag=tV0Vbg11J2`）→ INVITE #1，无 Location
- **From `tel:` 格式**（如 `tag=aseh2aeo`）→ INVITE #2，可能有 Location
- 若同一时间出现两条 INVITE（msg长度分别 ~2808 和 ~2898），即为分叉

---

## 五、ZTLIG 日志信号模式速查

### EventDetail 映射

| EventDetail | SIP 事件 | sipCallReportType | hi2->type |
|------------|---------|------------------|-----------|
| 10 | INVITE（呼叫开始） | a1 | 00 |
| 12 | 呼叫转移/呼转 | -- | -- |
| 14 | 180 Ringing（振铃） | a2 | 02 |
| 11 | 200 OK（接通） | a3 | 03 |
| 13 | BYE（释放） | a4 | 01 |

### 关键日志入口

```log
[ZtligKafkaProduceMsgByKey] topic[OWLS_TMC_REALTIME] leaid[1] msg[{...}]
[ProcSsfMsg] sipCallMsg fromUserPart[+xxx] ,toUserPart[xxx], sipCallReportType[a1], liid[xxx]
[ProcSsfCallReport]:get target_id[+xxx] from hash table! liid[xxx]
ProcSsfCallReport] callingNUM[+xxx], calledNum[xxx], hi2->type[00]!
X2 submodule:[X2_HW_IMS_MsgProc]sendLen = 2809, liid = [xxx] target[+xxx] sip msg[INVITE ...]
```

### 从日志识别双 INVITE

查看 `X2_HW_IMS_MsgProc` 中的 INVITE From-tag：
- From `sip:` 格式（如 `tag=tV0Vbg11J2`）→ INVITE #1，无 Location
- From `tel:` 格式（如 `tag=aseh2aeo`）→ INVITE #2，可能有 Location
- 同一时间两条 INVITE（长度 ~2808 和 ~2898），即为分叉

## 六、Location 提取的条件分析

### 成功提取 Location 需同时满足

1. **ZTLIG 实例位于 RN 路由路径上**（能收到 INVITE #2）
2. **SIP PANI 中包含 `last-utran-cell-id-3gpp`** 参数（SBC 附加的 LTE 小区 ID）
3. **PANI 未被其他网络节点修改**（不引入其他接入类型混淆）

### Location 提取失败场景

| 场景 | 原因 | 日志表现 |
|------|------|---------|
| ZTLIG 在 IMS 侧（ztlig2:465） | 看不到 RN 路由的 INVITE #2 | 全部 NetworkType=13，无 Location |
| PANI 中无 `last-utran-cell-id-3gpp` | SBC 未附加此非标准参数 | 仅有 INVITE #2 但 NetworkType=13 |
| **混合接入类型 PANI** | PANI 同时包含 GERAN + WiFi 两种接入类型 | 仅有 NetworkType=13 无 Location |
| UE 只上报了 `cgi-3gpp`（2G CGI） | ZTLIG 不解析 `cgi-3gpp` | 见上，pcap 有位置但日志无 |

### 混合接入类型 PANI 示例（呼叫二失败案例）

pcap 中 PANI 内容：
```
P-Access-Network-Info: 3GPP-GERAN;cgi-3gpp=6340703FF64FD
  AND
P-Access-Network-Info: IEEE-802.11;...Wlan-ue-local-ip=196.202.142.135
```

ZTLIG 输出：全部为 `NetworkType=13`，无 Location 字段。

---

## 七、双网元上报对位置保留逻辑的影响

当同一 LIID+CidNum 的两路 OWLS TMC 消息同时到达下游时，R&D 在确认的**位置保留逻辑**涉及：

1. **按 VNEID 优先级选取** — ztlig2:462(VNEID=3) 有位置，ztlig2:465(VNEID=6) 无位置
2. **按是否有 Location 字段覆盖** — 有位置的覆盖无位置的
3. **按时间戳更新覆盖** — 后到达的覆盖先到达的（需注意 INVITE #1 常先到，INVITE #2 后到但带位置）
4. **按 NetworkType 优先级** — NetworkType=11（接入面）覆盖 NetworkType=13（IMS 信令面）

---

## 八、IMS 架构全貌与 ATS 位置生命周期（VOWIFI经过网元情况.png 分析）

### 架构图全景（逻辑视图）

项目目录中的 `VOWIFI经过网元情况.png` 展示了完整的 **IMS 呼叫路由与位置管理架构**，包含 MO 侧（主叫）和 MT 侧（被叫）两大区域：

**网元布局：**
- MO 侧：HSS → ATS → SCSCF → A-SBC → VOWI Users
- MT 侧：HSS → ATS → SCSCF → ICSCF → SCSCF → A-SBC → VoLTE Users，另 ATS → mAGCF → 2/3G Users
- 右上角标注 `"the NEs which are connected with LIG"`（与监听网关连接的网元），但未具体画出是哪些

**黄色 Calling Flow（呼叫路径）:**
```
VOWI Users → A-SBC(MO) → SCSCF(MO) → ATS(MO) → HSS(MO)
  → SCSCF(MT) → ICSCF(MT) → SCSCF(MT) → ATS(MT) → mAGCF(MT) → 2/3G Users
```

### 网元角色速查

| 网元 | 角色 | 与 VoWiFi 位置关系 |
|------|------|------------------|
| **HSS** | 用户数据存储（鉴权/签约/位置） | 存储用户的 `last-utran-cell-id-3gpp`（最后注册的小区） |
| **ATS** (Application Triggering Server) | 应用触发服务器 | MO 侧：从 HSS 获取位置；MT 侧：删除位置 |
| **S-CSCF** | IMS 核心控制节点 | 会话控制，转发 SIP 信令 |
| **I-CSCF** | 查询 CSCF | 被叫路由查询 |
| **A-SBC** (Access SBC) | 接入边界控制器（`atbpcscf01`） | 将 `last-utran-cell-id-3gpp` 附加到 SIP PANI 头 |
| **mAGCF** (media AGCF) | 媒体接入网关 | 被叫侧 2G/3G CS 域互联 |

### `last-utran-cell-id-3gpp` 生命周期（两视角对比）

```
                   架构逻辑层（ATS）               信令实际层（SIP Pcap）
存储:  HSS 保存用户最后 LTE 小区
获取:  ATS(MO) 通过 Sh/Cx 从 HSS 获取           SBC 将值附加到 PANI 头
                                                 仅在 INVITE #2 (rn路由) 中携带
传递:  通过 SCSCF 转发                           ZTLIG ztlig2:462 从 PANI 提取
                                                 → OWLS TMC: LocationType=1, Location=6340704523F4C
删除:  ATS(MT) 删除该记录                        ATS 清理位置信息（完成生命周期）
```

**核心理解**：架构图中 ATS 是位置信息的逻辑管理者（从 HSS 读、传递、删除），但实际 SIP 信令中值是通过 SBC 附加到 PANI 头到达 ZTLIG 的。两者不矛盾 — ATS 通过 Sh 接口查询 HSS 后将值传给 SBC，再由 SBC 填入 SIP 消息的 `P-Access-Network-Info` 头域。

### 架构图元素与日志对应关系

| 架构图元素 | 日志/Pcap 对应 |
|-----------|---------------|
| A-SBC (`atbpcscf01`) | SBC 域名 `atbpcscf01.ims.mnc007.mcc634.3gppnetwork.org` |
| SCSCF (`psdscscf01`) | P-Charging-Vector 中 `psdscscf01` |
| `last-utran-cell-id` from HSS | 实际值 `6340704523F4C`（图中示例 `6340704525FB0`） |
| Calling Flow | INVITE #2 (rn 路由) 进入 ztlig2:462 |
| LIG 连接网元 | ztlig2:462 (rn路径) + ztlig2:465 (IMS Core侧) |

### 图中未覆盖的内容

- 图中未画出 SBC 分叉发出两条 INVITE 的机制（仅显示单条路由）
- 图中未区分双 ZTLIG 实例的部署差异
- `last-utran-cell-id` 的实际值是 SBC 在 SIP 层附加的，而非 ATS 在架构图层面显示的信号流
- 实际场景中位置提取失败的原因（混合 PANI 类型、缺少 `last-utran-cell-id` 参数）均在架构图中未体现

### Pcap vs ZTLIG 日志对比分析

`~/projects/A1/202606/120120415_pcap_vs_log_对比分析报告.md` 中对比了两通 VoWiFi 呼叫：

**呼叫一（14:53:13 — 10秒通话）— ✅ 完全一致**
```
pcap SIP INVITE P-Access-Network-Info:
  IEEE-802.11; ue-ip=10.200.212.64;
  Wlan-ue-local-ip=196.202.142.135;
  Wlan-ue-local-port=47746;
  last-utran-cell-id-3gpp=6340704523F4C
                              ↓ ZTLIG 正确解析
ZTLIG OWLS TMC:
  NetworkType=11,
  LocationType=1,
  Location=6340704523F4C
```
SBC 为 `last-utran-cell-id-3gpp` 填充了 LTE 小区 ID，ZTLIG 正确识别并生成位置记录。

**呼叫二（14:59:42 — 11秒通话）— ❌ 不一致**
```
pcap SIP 183 Session Progress P-Access-Network-Info:
  3GPP-GERAN;cgi-3gpp=6340703FF64FD    ← UE 上报的 2G CGI
  + IEEE-802.11;...Wlan-ue-local-ip=196.202.142.135  ← WiFi 信息
                              ↓ ZTLIG 未解析
ZTLIG OWLS TMC:
  NetworkType=13（仅有 IMS 面）
  无 Location 字段
```

**呼叫二位置丢失根因分析：**

| 可能原因 | 说明 |
|---------|------|
| **ZTLIG PANI 解析规则** | 当 SIP PANI 同时包含 `3GPP-GERAN` 和 `IEEE-802.11` 两种接入类型时，ZTLIG 可能未正确解析或优先级处理不当 |
| **NetworkType 映射问题** | pcap 中该呼叫同时有 GERAN(2G) 和 WiFi 两种接入信息，ZTLIG 无法确定以哪个为准，最终丢弃了位置 |
| **SBC 未附加 last-utran-cell-id** | 缺少 `last-utran-cell-id-3gpp` 参数，只有 UE 原始上报的 GERAN CGI + WiFi，ZTLIG 对 `cgi-3gpp`（2G CGI）的解析逻辑可能不完整 |

**WiFi 公网 IP（两条呼叫相同）：** `196.202.142.135:47746`，UE 处于同一 WiFi 环境下。

### 可视化版本

重构的暗色主题 SVG 位于项目目录：`~/projects/A1/202606/VOWIFI-architecture.svg`（对应 HTML 源文件 `VOWIFI-architecture.html`）。

与原图相比，该 SVG 增加了：
- 图例（各网元颜色编码）
- 底部信息卡片（MO 侧/MT 侧/ZTLIG 监听网关三点摘要）
- SBC 分叉两条 INVITE 的标注框
- 双 ZTLIG 实例信息
- 实际 pcap 中的 WiFi IP 和位置值

打开方式：`/snap/bin/chromium --no-sandbox file:///home/andymao/projects/A1/202606/VOWIFI-architecture.html`

---

## 九、排查命令速查

```bash
# 识别双网元上报 — 统计同一 CidNum 的不同 NEID
grep "CidNum.*atbpcscf01.19a.8315" 120120415.txt | grep -oP '"Neid":"[^"]+"' | sort -u

# 对比两个 NE 的消息长度（有位置 > 无位置）
grep -E "ztlig2:462|ztlig2:465" 120120415.txt | grep -oP 'len\[1-\d+\]' | sort -u

# 查看双 INVITE 的 From-tag
grep "X2_HW_IMS_MsgProc.*INVITE" 120120415.txt | grep -oP 'tag=[^ ]+' | sort -u

# 统计 sipCallReportType 分布
grep "sipCallReportType" 120120415.txt | grep -oP 'sipCallReportType\[\w+\]' | sort | uniq -c

# 查看特定 CidNum 在不同 NE 上的完整时序
grep "atbpcscf01.19a.8315" 120120415.txt | grep -oP 'ztlig2:\d+|EventDetail":\d+|NetworkType":\d+|Location[^}]*' | head -40
```
