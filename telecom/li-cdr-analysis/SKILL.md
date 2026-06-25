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

## 引用

- 知识库: `~/knowledge/li/ZTLIG/ztlig-ligcdr-extract-tool.md`
- GitHub: `github.com/andymao76/ops-monitoring/ztlig-tools/`

## 参考案例

- `references/liid14029-analysis.txt` — LIID 14029 全量分析（5029条，4个文件，双站点）
- `references/msisdn-120120415-analysis.txt` — MSISDN 120120415 分析（号码同时作为目标和对方）
