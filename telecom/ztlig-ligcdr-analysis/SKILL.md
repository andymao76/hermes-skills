---
name: ztlig-ligcdr-analysis
description: ZTLIG2 LigCdr 日志分析 — 全量扫描/过滤提取/深度分析/结构化报告输出。覆盖 LIID 维度、MSISDN 维度、呼叫时序、EventDetail 分布、网元分析。
absorbed_into: li-cdr-analysis
---

# ZTLIG2 LigCdr 日志分析

分析 ZTLIG2 系统输出的 HW LigCdr 日志，支持按 LIID、MSISDN、CIN、EventDetail、时间范围等维度提取和深度分析。

## 触发条件

用户要求分析某 LIID / MSISDN 在 ZTLIG 日志中的全部记录时触发。

## 工作流程

### 第一步：快速扫描定位

使用 grep 或 Python 扫描全部 txt 文件，定位目标出现在哪些文件中：

```python
# 快速定位含目标的文件
grep -l '<LIID|MSISDN>' *.txt
```

或写 Python 脚本逐文件遍历 LigCdr JSON，输出每文件记录数、时间范围、EventDetail 分布、CIN 数、MSISDN 数。

### 第二步：提取全部记录

使用 `extract_ligcdr.py` 提取：

```bash
python3 extract_ligcdr.py /tmp/ztlig_4files/ --liid <LIID> --unique -o /tmp/output
python3 extract_ligcdr.py /tmp/ztlig_4files/ --msisdn <MSISDN> --unique -o /tmp/output
```

**注意**: argparse 的 `path` 参数为 `nargs='?'`，不支持多文件传递。解决方案：
- 建临时软链接目录: `mkdir -p /tmp/ztlig_4files && ln -sf .../*.txt /tmp/ztlig_4files/`
- 传入目录路径

### 第三步：数据提取完整性检查

`--msisdn` 过滤器是精确匹配 MSISDN 字段。本地格式（如 0120120415）和国际格式（如 249120120415）是不同的值，需分开补扫：

```python
# 补扫本地格式的额外记录
python3 -c "
import json, re
# 遍历文件，筛 MSISDN=本地格式 且 去重
"
```

### 第四步：深度分析

写分析脚本，覆盖以下维度：

| 分析维度 | 内容 |
|---------|------|
| 号码角色 | 号码出现在 MSISDN/CallingNum/CalledNum 哪个字段（见下方角色分析） |
| LIID 维度 | 按 LIID 分组，每个 LIID 的目标MSISDN、对方号码、时间范围 |
| 呼叫时序 | 按 CIN 分组，统计 EventDetail 序列（常见模式: 10→11→13→14） |
| 时间分布 | 每日记录数热力图 |
| 方向 | MO(主叫) vs MT(被叫) 比例 |
| 网元 | NEID、Vendor、NetworkType 分布 |
| 关联号码 | 与被分析号码通话的对方号码列表 |

**MSISDN 号码角色分析（重要）**:

MSISDN 查询比 LIID 复杂，目标号码可能出现在三个不同字段，`--msisdn` 仅精确匹配 MSISDN 字段。要完整分析号码活动：
1. 先 `extract_ligcdr.py --msisdn <国际格式>` 提取作为 MSISDN 字段的记录
2. 再补扫本地格式（如 `0120120415` vs `249120120415`）
3. 最后写脚本分析 CallingNum/CalledNum 中出现的关联记录

```python
# 号码角色分析
role = Counter()
for obj in all_objs:
    msisdn = str(obj.get('MSISDN',''))
    calling = str(obj.get('CallingNum',''))
    called = str(obj.get('CalledNum',''))
    if '120120415' in msisdn: role['MSISDN(被监听目标)'] += 1
    elif '120120415' in calling: role['CallingNum(主叫)'] += 1
    elif '120120415' in called: role['CalledNum(被叫)'] += 1
```

### 第五步：非 JSON 日志行分析（V1.2）

`extract_ligcdr.py` V1.2 新增非 JSON 日志行文本匹配。当设置了过滤条件（LIID / MSISDN / CIN 等），无 JSON 结构的日志行若包含过滤值也会被捕获输出到 `raw_matches_filtered.txt`。

典型捕获内容：
- `TargetTblFindProcess: Target find [succ]!liid[14029]` — 目标匹配过程
- `X2_HW_IMS_MsgProc` — X2 接口 IMS 信令（SIP INVITE/183/200/BYE）
- `ProcSsfMsg` — SSF 呼叫报告
- `P-Charging-Vector: icid-value=<CIN>` — SIP 消息头

这些行对于信令级分析和 X2 接口故障排查极有价值。

### 第六步：输出结构化 TXT 报告

**报告格式必须为纯文本 (.txt)，不要用 Markdown (.md)。这是用户明确要求的输出格式偏好。**

报告章节（按顺序）：

```
标题行
=======
数据源 / 分析范围 / 工具 / 日期

一、总体概况
二、文件/数据分布
三、LIID 维度（或号码角色分析）
四、呼叫时序分析 / EventDetail 分布
五、网元与方向
六、时间分布
七、关联号码
八、关键发现
九、输出文件
```

格式要求：
- 章节编号使用 一、二、三...
- 分隔线使用 `-------` 或 `====`
- 表格使用空格对齐，不用 Markdown 表格语法
- 数据在前，结论在后

## Pitfalls

- **假 .gz 文件**: `A1-ztlig/` 目录下有文件名 `.gz` 但实际是纯文本的文件，`iter_lines_from` 按 `.gz` 后缀走 `gzip.open()` 会崩溃。解决方案：绕过，只指定 `.txt` 文件。
- **MSISDN 本地 vs 国际格式**: `--msisdn` 精确匹配，`0120120415` 和 `249120120415` 是两个不同值，需分别查询。
- **去重**: 同一 LigCdr 可能会被 ZTLIG 同时推往 OWLS_TMC_REALTIME 和 OWLS_TMC_OFFLINE 两个 topic，导致原始日志中出现两次。必须用 `--unique` 去重。
- **时间过滤**: `extract_ligcdr.py` 的 `--time-start/--time-end` 格式为 YYYYMMDDHHMMSS。
- **大文件**: 270MB+ 的 txt 文件单文件扫描需 30s+，建议用 `background=true` 或设置足够 timeout。

## 关联

- `extract_ligcdr.py` — 位于 `~/PCAP/20260623-A1-VOWIFI/extract_ligcdr.py`
- `ztlig-ligcdr-analysis/references/ligcdr-analysis-workflow.md` — 分析命令速查
- 知识库: `~/knowledge/li/ZTLIG/ztlig-ligcdr-extract-tool.md`
