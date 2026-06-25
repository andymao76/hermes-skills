# ZTLIG LigCdr 日志深度分析参考

> A1 项目 ZTLIG2 日志分析模式与方法
> 适用场景: LIID 维度分析、MSISDN 关联分析、跨文件呼叫追踪

## 分析工作流

```
扫描分布 → 按LIID/MSISDN提取 → 去重 → 统计分布 → 深度分析 → 报告
```

### Step 1: 快速定位

```bash
# 找出含目标 LIID/MSISDN 的文件
grep -l 'LIID.:.14029' A1-ztlig/*.txt
grep -l '120120415' A1-ztlig/*.txt
```

### Step 2: 提取与去重

```bash
python3 extract_ligcdr.py A1-ztlig/ztlig2.462.txt A1-ztlig/ztlig2.465.txt ... \
    --liid 14029 --unique -o /tmp/output
```

**注意**: `list_input_files()` 会扫描目录下所有文件，包括 `.gz`。如果目录下有非真正 gzip 的 `.gz` 文件（实际是纯文本），`iter_lines_from()` 走到 `gzip.open()` 会崩溃 (`Not a gzipped file`)。解决方案：
1. 只传明确需要的 `.txt` 文件
2. 或建软链接目录排除 `.gz`
3. 或用 `find` 只选 `.txt` + `-size +1M`

### Step 3: 非 JSON 行自动捕获

V1.2 新增：设置了过滤条件后，不含 JSON 结构的日志行也会做文本子串匹配，输出到 `raw_matches_filtered.txt`。

典型捕获内容：
- SIP 消息头 (`P-Charging-Vector`、`INVITE`)
- 调试日志 (`Target find [succ]!liid[14029]`)
- SSF 呼叫报告

**行数预估**: 每 1 条 JSON LigCdr 平均捕获 10~20 行非JSON关联日志。

### Step 4: EventDetail 呼叫序列分析

典型完整呼叫: Begin(10) → Answer(11) → Release(13) → T38(14)

| 事件数 | 含义 | 占比参考 |
|--------|------|---------|
| 4事件 (10→11→13→14) | 完整语音通话 | ~45% |
| 2事件 (10→14 或 10→13) | 未接通/短暂 | ~28% |
| 3事件 (10→13→14) | 无应答释放 | ~15% |
| 1事件 (10) | SMS/Bearer | ~7% |

### Step 5: CIN 命名空间识别

A1 项目的 CIN 有三种格式：
- `psdpcscf0X.XXX.XXXX.2026MMDDHHMMSS` — PSD 站 (苏丹港)
- `atbpcscf01.XXX.XXXX.2026MMDDHHMMSS` — ATB 站 (阿特巴拉)
- `A3769567...` — 华为内部 Hex 格式

CIN 前缀决定站点归属，后缀时间戳决定呼叫起始时间。

### Step 6: MSISDN 多格式聚合

同一号码在日志中可能以多种格式出现：
- 国际格式: 249XXXXXXXXX (E.164)
- 本地格式: 0XXXXXXXXX (国内前缀)
- 国际前缀: 00249XXXXXXXXX

`extract_ligcdr.py --msisdn` 是精确匹配，需分别过滤再合并统计。

### Step 7: 跨 LIID 关联分析

同一 MSISDN 可能出现在多个 LIID 中：
- 作为目标: MSISDN 字段匹配
- 作为对方: CallingNum/CalledNum 字段匹配

## 典型分析结果参考

### LIID 14029 (2026-05-29 ~ 2026-06-23)
- 4 个 ZTLIG 实例, 5029 条去重记录, 1168 个唯一 CIN
- 目标 MSISDN: 249123634828 (Sudatel)
- 网络类型: IMS(13) 为主, 少量 VoWiFi(11)
- 双站点漫游: PSD + ATB
- 52,967 行非JSON关联日志

### MSISDN 120120415 (2026-05-17 ~ 2026-06-23)
- 5 个 LIID, 56 条去重记录, 16 个 CIN
- 作为目标 36 条, 作为对方 20 条

## 陷阱

- `.gz` 假文件导致崩溃: list_input_files 不区分 .txt 和 .gz
- `--msisdn` 是精确匹配，不聚合本地/国际格式
- 交互模式扫描预览只扫前 50000 行
- raw_matches_filtered.txt 只输出 1 个文件（不分 CIN 分组）
- 大文件扫描慢: 344MB 单文件需 3~5 分钟
