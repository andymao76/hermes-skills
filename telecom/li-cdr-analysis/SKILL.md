---
name: li-cdr-analysis
description: LI CDR 日志全量分析工作流 — 从 ZTLIG2/HW/ZTE 等系统中提取、过滤、分析 LigCdr 记录并输出结构化报告
---

# LI CDR 数据分析工作流

从 LI 系统日志（ZTLIG2、华为 IMS-LIG 等）中提取 LigCdr/CDR 记录，进行多维度分析并输出报告。

## 适用场景

- 特定 LIID 的全量呼叫行为分析
- 特定 MSISDN 的监听记录追溯（作为目标或通话对方）
- 多 LIID 跨站点的呼叫模式对比
- 时间范围内的 CDR 统计与趋势分析

## 工具

主工具: `~/PCAP/20260623-A1-VOWIFI/extract_ligcdr.py` (V1.2+)
GitHub: `github.com/andymao76/ops-monitoring/ztlig-tools/`

## 工作流

### 第一步：快速定位

扫描所有日志文件，找出目标 LIID 或 MSISDN 出现在哪些文件中：

```python
# 思路：对每个 txt 文件，用 grep 或 Python 逐行扫描
# 找到含目标值的文件后，统计条数、LIID数、CIN数、时间范围
```

关键点：
- 先用 `grep -l` 快速筛选含目标文本的文件（几秒出结果）
- 再用 Python 精确解析 JSON 提取统计信息
- 注意排除假 `.gz` 文件（实际是纯文本但后缀为 .gz 的文件导致 gzip.open 崩溃）

### 第二步：统计分布

对每个含目标记录的文件，统计：
- 记录数、唯一 CIN 数、唯一 MSISDN 数
- EventDetail 分布（Begin/Answer/Release/T38/SMS 等）
- 时间范围

### 第三步：深度分析

去重后对所有记录进行多维度分析：

| 维度 | 分析内容 |
|------|---------|
| MSISDN | 目标号码的各种格式（国际/本地/前缀）、记录数占比 |
| LIID | 每条 LIID 涉及的 MSISDN、CIN、时间范围 |
| CIN 分组 | 每通呼叫的事件序列、典型模式（如 10→11→13→14） |
| 时间线 | 每日/每小时的活动密度、活跃周期 |
| 方向 | MO vs MT 比例 |
| 网元 | NEID 分布、Vendor、NetworkType |
| 对方号码 | 通话对方的号码统计 |
| 呼叫时长 | CallDuration 统计 |

### 第四步：提取全量数据

用 extract_ligcdr.py 带过滤条件提取：

```bash
# 按 LIID 过滤
python3 extract_ligcdr.py <文件或目录> --liid <LIID> --unique -o <输出目录>

# 按 MSISDN 过滤
python3 extract_ligcdr.py <文件或目录> --msisdn <MSISDN> --unique -o <输出目录>
```

注意：`extract_ligcdr.py` 的 argparse `path` 参数是 `nargs='?'`，只接受单路径。
需要处理多个文件时，建软链接目录绕过此限制。

### 第五步：输出报告

报告包含以下章节（TXT 格式，避免 MD）：

1. 总体概况 —— 记录数、LIID数、CIN数、时间跨度
2. 文件分布 —— 每个文件的记录数、CIN数、时间范围
3. MSISDN 维度 —— 各种格式的出现次数
4. LIID 维度 —— 每个 LIID 的详细数据
5. 呼叫时序 —— EventDetail 分布、每通呼叫事件数分布、典型序列
6. 方向分析 —— MO/MT 比例
7. 时间分布 —— 日期维度活动量
8. 网元/厂商 —— NEID、Vendor、NetworkType
9. 对方号码 —— 通话对方号码统计
10. 关键发现 —— 模式总结
11. 输出文件清单

## EventDetail 编码

| Code | 含义 |
|------|------|
| 1 | Begin(Bearer) |
| 2 | Continue(Bearer) |
| 4 | Begin(SMS) |
| 10 | Begin（呼叫始发） |
| 11 | Answer（应答） |
| 12 | Redirection（呼叫转移） |
| 13 | Release（释放） |
| 14 | T38（传真） |
| 17 | Partial |
| 18 | CallRelease |

### CIN 命名空间解读

CIN（CidNum）包含站点和网络信息：

| 格式 | 含义 |
|------|------|
| `psdpcscf0X.XXX.XXXX.2026MMDDHHMMSS` | PSD 站（苏丹港）的呼叫 |
| `atbpcscf01.XXX.XXXX.2026MMDDHHMMSS` | ATB 站（阿特巴拉）的呼叫 |
| `A3769567...` (纯 Hex) | 华为内部格式 CIN |

同一 LIID 的 CIN 出现在不同站点前缀时，说明用户在两站之间移动（漫游）。

### NetworkType 语义

| 值 | 含义 | 说明 |
|----|------|------|
| 11 | VoWiFi | Wi-Fi 呼叫，常见于早期记录 |
| 13 | IMS | IMS 域呼叫，主流模式 |

同一个 LIID 可能在早期是 VoWiFi，后期切换为 IMS。分析时注意 NetworkType 的时间演变。

### 呼叫时序深度分析

按 CIN 分组后，分析每通呼叫的 EventDetail 序列：

```python
# 统计每通呼叫的事件数分布
for cin, objs in cin_groups.items():
    eds = sorted([o.get('EventDetail') for o in objs])
    call_events_dist[len(eds)] += 1

# 统计典型 EventDetail 序列
seq = tuple(sorted([o.get('EventDetail') for o in objs]))
seq_count[seq] += 1
```

典型序列模式（以 HW IMS 为例）：

| 序列 | 解读 |
|------|------|
| 10→11→13→14 | 完整语音通话（最典型，占 ~45%） |
| 10→14 | 仅有始发+传真（未应答） |
| 10→13→14 | 呼叫释放+传真跟踪 |
| 10→13 | 呼叫始发即释放（未接通） |

## 常见陷阱

1. **假 `.gz` 文件**: `A1-ztlig/` 目录下存在 `.gz` 后缀但实际是纯文本的文件（如 `ztlig2.460.gz`）。`list_input_files` 会扫到它，`iter_lines_from` 按后缀走 `gzip.open()` 导致 `BadGzipFile`。解决方案：用 `find ... -name '*.txt'` 只选 `.txt` 文件。

2. **同一号码多种格式**: 同一个 MSISDN 可能同时出现 `249xxxxxxxxx`（国际）、`012xxxxxxx`（本地）、`00249xxxxxxxxx`（国际前缀）三种形式。过滤时需要用 `--msisdn` 分别查，或用文本搜索（V1.2 非 JSON 行匹配）。

3. **号码不一定是目标**: `--msisdn` 过滤只匹配 JSON 的 MSISDN 字段（被监听目标），不匹配 CallingNum/CalledNum。要查作为对方号码出现的情况，需要用文本搜索或自定义脚本。

4. **文件可能不含 LigCdr**: 部分日志文件（如 ztlig2.464.txt）是纯模块启动日志，不含 LigCdr JSON。先用快速扫描确认。

## PCAP 与 ZTLIG Log 交叉验证

当同时拥有 ZTLIG 日志和对应的 PCAP 抓包时，可对两者进行交叉验证以确认数据完整性。

### 适用场景

- ZTLIG log 中有 LigCdr 产生，需确认 PCAP 是否覆盖了对应信令
- PCAP 中有 X2 IRI 数据，需确认 ZTLIG 是否完整处理了每一个消息
- 排查是否丢包、丢数据（如 Mavenir 双 li-tid 只处理了其中一个）

### 验证步骤

**第一步：提取 PCAP 中的关键标识**

用 tcpdump 从 PCAP 中提取 Call-ID 列表：

```bash
tcpdump -r capture.pcap -A | grep -oa 'Call-ID:\s*\S*' | sort -u
```

**第二步：提取 ZTLIG Log 中的 Call-ID**

ZTLIG log 在 ssf 模块下输出每个 callId（注意是 callId 而非 correlationID）：

```bash
grep -oP 'callId\[\K[^\]]+' ztlig.log | sort -u
```

**第三步：按 Call-ID 逐流比对**

每个 Call-ID 在两种数据源中必须出现：
- ZTLIG log: 有 `ssf_deal_sip_msg: begin deal ... msg` 和 `complete`
- PCAP: 有对应的 XML hi2-uag block 包含该 callId/session-id

**第四步：比对 Correlation-id**

ZTLIG log 中 correlationID 格式如 `a000b012e30300005980a`，PCAP XML 中 `<Correlation-id>` 字段应与之一致。

```bash
# 从 PCAP 提取 correlation-id
tcpdump -r capture.pcap -A | grep -oa '<Correlation-id>[^<]*</Correlation-id>' | sort -u

# 从 ZTLIG log 提取
grep -oP 'correlationID\[\K[^\]]+' ztlig.log | sort -u
```

### 特殊模式识别

**Mavenir XML PCAP 的典型特征（区别于华为 ASN.1 BER）：**

| 特征 | 说明 |
|:----|:-----|
| SIP 封装方式 | CDATA 明文 或 Base64 编码，非 ASN.1 BER |
| 根元素 | `<hi2-uag>`（X2）、`<hi3-uag>`（X3） |
| 消息复制 | 同一条 SIP 消息可能出现 2 次，分属不同 li-tid（双监听目标） |
| 返回码 | `<Return-code>0</Return-code>` 表示 ZTLIG 处理成功 |

**双 li-tid 现象（Mavenir 特有）：**

Mavenir UAG 可能对同一条 SIP 信令同时发送给两个不同的 LIID。PCAP 中会出现两条几乎一样的 XML，仅 `<li-tid>` 不同：
```
<li-tid>10078</li-tid>  → ZTLIG 处理并产生 LigCdr
<li-tid>10073</li-tid>  → 可能被忽略或不产生 LigCdr
```

ZTLIG log 中 `MatchUsrinfo find success` 出现两次也印证了这一点。

**PCAP 时间戳校准：**

| 时间来源 | 含义 | 典型差异 |
|:---------|:-----|:---------|
| PCAP 包时间 (capinfos) | 抓包服务器系统时钟 | 可能偏差数小时 |
| XML `<stamp>` | Mavenir UAG 本地时间 | ZTLIG log 比此值晚约 4~5 分钟（处理延迟） |
| ZTLIG log 时间 | ztlig2 模块处理完成时间 | 最晚，含队列积压 |

验证时优先使用 Call-ID、Correlation-id 等应用层标识，不要依赖时间戳做精确匹配。

### SMS 检测方法

SMS 在 Mavenir X2 接口中通过 SIP MESSAGE 方法承载：

```bash
# 在 PCAP 中检测 SMS
tcpdump -r capture.pcap -A | grep -a 'Content-Type: application/vnd.3gpp.sms'

# 在 ZTLIG log 中检测 SMS MESSAGE 处理
grep -E 'ssf_deal_sip_msg.*MESSAGE|EventDetail.*4|sm-submit-report' ztlig.log

# 提取 SMS 内容（3GPP SMS payload 中的文本）
tcpdump -r capture.pcap -A | grep -oaP 'test.*?202[0-9]{6}'
```

SMS 的 EventDetail 编码为 `4`（Begin(SMS)），MESSAGE 方法属于即时消息（不建立独立媒体通道），区别于常规语音通话的 10→11→13→14 序列。

## 引用

- 知识库: `~/knowledge/li/ZTLIG/ztlig-ligcdr-extract-tool.md`
- 知识库: `~/knowledge/li/Mavenir/Mavenir_IMS_LI_接口包_X1_X2_X3.md`
- GitHub: `github.com/andymao76/ops-monitoring/ztlig-tools/`

## 工具位置

| 工具 | 路径 |
|------|------|
| LigCdr 提取 CLI | `~/PCAP/20260623-A1-VOWIFI/extract_ligcdr.py` |
| X 接口日志 Web 分析 | `http://localhost:5000/x-interface` |
| X 接口解析器源码 | `~/projects/ETSI-ASN1-Assistant/src/x_interface_decoder.py` |

## 六、X 接口日志文本分析 (V4 补充)

除 LigCdr JSON 外，LI 系统中还有三种文本日志携带关键拦截信息，可通过 ETSI-ASN1-Assistant V4 的 X 接口分析页解析：

| 日志类型 | 模块 | 接口 | 内容 |
|---------|------|------|------|
| SSF | `ssf:NNNN` | X2 (信令面-SIP) | SIP 呼叫信令，LIID/CIN/callId |
| RVF | `rvf:NNNN` | X3 (媒体面-RTP) | RTP 会话，correlationID/rtpSession |
| ZTLIG1 | `ztlig1:NNN` | X1 (管理面) | 设控/去控/NE 初始化/license 状态 |
| ZTLIG2 | `ztlig2:NNN` | X2 (信令面-IRI) | 同 LigCdr JSON + 模块日志 |

### 日志行格式

通用结构: `[timestamp][LEVEL][module:port][function] body`

```
[2026-06-23 10:57:19][DEBUG][ssf:1300][sipAddControlMsg] LIID[8628] CIN[95119960]
[2024-08-01 10:48:52][INFO ][rvf:1420] liid[10078], correlationID[2200034c0-3-xxx]
[2025-12-22 08:01:23][ERROR][ztlig1:300]startup error
[2025-12-22 08:01:29][INFO ][ztlig2:461]ztlig2 module is starting
```

### 使用方式

- 在 ETSI-ASN1-Assistant V4 首页点击「🔬 X 接口日志 →」
- 或直接访问 `http://localhost:5000/x-interface`
- 选择接口类型（X1/X2/X3/Auto）+ 子类型
- 上传日志文件，自动分栏展示：左栏=解析结果，右栏=原始日志
- 支持 LIID/CIN/关键词/ERROR 级别实时过滤

### CDR 与文本日志交叉验证

LigCdr JSON 和 X 接口文本日志互补使用：

| 场景 | 用 CDR | 用文本日志 |
|------|--------|-----------|
| 呼叫统计 | EventDetail 分布/时长 | — |
| 信令排查 | — | SSF 显示 SIP 方法/状态码 |
| 媒体验证 | — | RVF 显示 RTP 会话/关联 |
| 系统状态 | — | ZTLIG1 显示 license/NE/错误 |
| 全量分析 | CDR → 文本行, 用 CIN 关联 |

### 文件存储

测试日志位于:
- `~/PCAP/20260623-A1-VOWIFI/ssf_*/` — SSF 日志（SIP 信令）
- `~/PCAP/20260623-A1-VOWIFI/A1-ztlig/ztlig2.*.txt` — ZTLIG2 日志（含 LigCdr）
- `~/PCAP/20260623-A1-VOWIFI/ztlig120260624_060817/ztlig1.300.txt` — ZTLIG1 日志
- `~/PCAP/Mavenir-IMS-LI/call-test/rvf.*.txt` — RVF 日志

### 注意事项

- ZTLIG2 的 `.txt` 文件可能实际为 gzip 压缩格式，需用 `file` 命令检测
- SSF 日志的 `callid` 字段可能为全小写（`callid[...]`），非驼峰 `callId[...]`
- RVF 日志的 level 字段可能有尾部空格 `[INFO ]`，解析时需容错
- **大文件限制**: Web 工具只读取文件前 5MB（约 3-5 万行日志），超过此量级用 CLI 工具 `extract_ligcdr.py` 或直接 grep 分析
- **521MB 陷阱**: ztlig1.300.txt（521MB/473万行）直接上传浏览器会导致 Chrome SIGILL 崩溃，必须分段或使用 CLI 分析

## 参考案例

- `references/liid14029-analysis.txt` — LIID 14029 全量分析（5029条，4个文件，双站点）
- `references/msisdn-120120415-analysis.txt` — MSISDN 120120415 分析（号码同时作为目标和对方）
- `references/mavenir-pcap-log-crossvalidation.txt` — Mavenir PCAP 与 ZTLIG log 交叉验证示例
