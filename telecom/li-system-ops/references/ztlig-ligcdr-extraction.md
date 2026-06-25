# ZTLIG2 LigCdr 日志提取与分析参考

> 工具: `~/PCAP/20260623-A1-VOWIFI/extract_ligcdr.py` (V1.2)
> 用于从 ZTLIG2 日志中提取 LigCdr CDR 记录并做关联分析

## 功能概述

| 模式 | 说明 |
|------|------|
| JSON 提取 | 从日志行正则匹配 `\{...\}` 结构，过滤 CdrType=LigCdr |
| 非JSON行筛选 | V1.2 新增 — 不含 JSON 的日志行也按过滤条件做文本子串匹配 |
| 交互菜单 | 无参运行进入交互式引导（推荐新手） |
| 命令行 | 支持 `--liid` / `--msisdn` / `--cin` / `--event-detail` / `--vendor` / `--neid` / `--time-start` / `--time-end` |

## 快速命令

```bash
cd ~/PCAP/20260623-A1-VOWIFI

# 单个文件按 LIID 过滤 + 去重 + 限制输出
python3 extract_ligcdr.py A1-ztlig/ztlig2.467.txt --liid 14029 --unique --limit 20 -o /tmp/out

# 统计模式
python3 extract_ligcdr.py A1-ztlig/ztlig2.467.txt --liid 14029 --stats

# EventDetail 过滤（10=Begin, 11=Answer, 13=Release, 14=T38）
python3 extract_ligcdr.py A1-ztlig/ztlig2.467.txt --event-detail 10,11,13 --liid 14029 -o /tmp/out

# CIN 过滤 — 自动捕获 P-Charging-Vector 等非JSON关联行
python3 extract_ligcdr.py A1-ztlig/ztlig2.467.txt --cin "psdpcscf02.194.6cbd.20260607125301" -o /tmp/out
```

## 多文件处理

脚本 argparse 仅支持单个 path 参数。要处理多个文件：
```bash
# 创建 symlink 目录
mkdir -p /tmp/ztlig_input
ln -sf /path/to/ztlig2.465.txt /tmp/ztlig_input/
ln -sf /path/to/ztlig2.466.txt /tmp/ztlig_input/
python3 extract_ligcdr.py /tmp/ztlig_input/ --liid 14029 --unique -o /tmp/out
```

## 输出结构

```
/tmp/out/
├── LIID_CIN_CaptureTime.txt      # 按唯一键分组的原始日志行
├── LIID_CIN_CaptureTime.json      # 结构化 JSON array
└── raw_matches_filtered.txt       # V1.2: 非JSON行的文本匹配结果
```

## 过滤字段匹配规则

| 字段 | JSON 匹配 | 非JSON文本行匹配 |
|------|-----------|------------------|
| LIID | 精确匹配 JSON 字段 | `fliid in line` 子串 |
| MSISDN | 精确匹配 | 子串搜索 |
| CIN (CidNum) | 精确匹配 | 子串搜索 |
| EventDetail | `str(ed) in list` | 数字文本片段 |
| Vendor | 精确(不区分大小写) | 不区分大小写子串 |
| Neid | 精确匹配 | 子串搜索 |
| 时间 | CaptureTime 字段 | 行中提取 `[YYYY-MM-DD HH:MM:SS]` 或 `YYYYMMDDHHMMSS` |

## 跨文件 LIID/MSISDN 综合分析工作流

当需要全面分析某个 LIID 或 MSISDN 在所有日志中的行为，按 5 步执行：

### Step 1 — 文件定位

扫描所有 txt 文件定位包含目标的文件。注意：
- `list_input_files()` 会扫到 `.gz` 假文件（实际是纯文本）导致 `BadGzipFile`
- 解决方案：指定 `.txt` 文件列表，或创建仅含 `.txt` 的 symlink 目录

### Step 2 — 快速统计

每个文件分别跑 `--stats`，获取：
- 每文件的 LIID/MSISDN 记录数
- EventDetail 分布
- CIN 数（唯一通话标识）
- 时间范围（最小/最大 CaptureTime）
- MSISDN 去重列表

### Step 3 — 深度分析（专用分析脚本）

用 Python 脚本做如下分析（参考 `/tmp/analyze_msisdn.py` 模式）：

**MSISDN 角色分析**
同一号码可能在日志中以三种角色出现：
- MSISDN（被监听目标）— 用 `--msisdn` 过滤
- CallingNum（主叫对方）— 需要额外的文本搜索
- CalledNum（被叫对方）— 需要额外的文本搜索

注意：`--msisdn` 参数只精确匹配 JSON 中的 MSISDN 字段，不匹配 CallingNum/CalledNum。
要完整分析某号码的关联记录，须用 Python 脚本同时检查三个字段。

**号码格式陷阱：**
同一号码可能以多种格式出现在日志中：
- 国际格式: `249120120415`
- 本地格式: `0120120415`
- 国际前缀格式: `00249123634828`

`--msisdn` 做精确匹配，不同格式视为不同值。分析时必须分别搜所有格式，或改用文本子串搜索 `120120415`。调用分析脚本时注意双遍扫描：先用 `--msisdn 249120120415` 提取 MSISDN字段匹配的，再用文本搜索补 `0120120415` 本地格式的。

**多 LIID 关系分析**
一个号码可能跨多个 LIID，每个 LIID 代表不同的监听场景：
- 场景A：号码作为目标（MSISDN=该号码）
- 场景B：号码作为对方出现在其他目标的呼叫中（CallingNum/CalledNum=该号码）

**呼叫时序分析**
- 按 CIN（CidNum）分组，统计每通呼叫的 EventDetail 序列
- 典型完整呼叫: 10(Begin) → 11(Answer) → 13(Release) → 14(T38)
- 不完整呼叫: 仅 10(Begin) 或 10→13（未接通）

**其他分析维度**
- 时间分布：按日统计呼叫量，发现活跃周期
- 站点评判：CIN 前缀 `psdpcscf*`=PSD站, `atbpcscf*`=ATB站, `A3769567*`=华为内部格式
- NetworkType：13=IMS, 11=VoWiFi — 区分目标的活动域
- 方向统计：MO(主叫)/MT(被叫) 比率
- 关联号码分析：通话对方号码列表及频次
- 呼叫时长：min/max/avg

### Step 4 — 去重提取

```bash
# symlink 目录绕过多文件限制
mkdir -p /tmp/ztlig_input
for f in ztlig2.465.txt ztlig2.466.txt ztlig2.467.txt; do
    ln -sf /path/to/A1-ztlig/$f /tmp/ztlig_input/
done
python3 extract_ligcdr.py /tmp/ztlig_input/ --liid <LIID> --unique -o /tmp/report
```

### Step 5 — TXT 报告生成

报告用纯文本格式（TXT），不用 Markdown。结构如下：

```
标题
==============================
数据源: ...
分析范围: ...
工具: ...
日期: ...


一、总体概况
------------------------------

  指标            数值
  ----            ----
  ...


二、号码角色分析
------------------------------
...

三、涉及 LIID 及触发场景
------------------------------
...
...

四、通话方向
------------------------------
...

五、时间分布
------------------------------
...

六、EventDetail 分布
------------------------------
...

七、网元与厂商
------------------------------
...

八、关联号码（通话对方）
------------------------------
...

九、关键发现
------------------------------
  1. ...
  2. ...

十、输出文件
------------------------------
...
```

### 典型分析结果示例

**单 LIID 分析（LIID=14029）**
- 4 个文件，5029 条去重记录，1168 个 CIN
- 目标 MSISDN: 249123634828（Sudatel）
- 覆盖 26 天，PSD+ATB 双站
- 44.8% 完整呼叫（10→11→13→14）
- 52967 行非JSON关联日志

**单号码分析（MSISDN=120120415）**
- 5 个 LIID，56 条去重记录，16 个 CIN
- 36 条作为目标（4 个 LIID），20 条作为对方（1 个 LIID）
- 24 天跨度，VoWiFi+IMS 双域
- 关联对方：249916617777, 0123406778, 0123123638 等 8 个号码
- `TargetTblFindProcess` — 目标匹配确认
- `X2_HW_IMS_MsgProc` — X2 接口 SIP 信令消息（INVITE/183/200/ACK/BYE）
- `ProcSsfMsg` — SSF 呼叫报告
- `P-Charging-Vector` — SIP 计费向量（含 CIN 引用）

## 已知限制

- `--limit` 参数仅限制 JSON 输出条数，不限制非JSON行
- 无过滤条件时，非JSON行筛选自动关闭（仅输出JSON）
- argparse `path` 参数为 `nargs='?'`，只能接受一个路径；需处理多文件时用 symlink 目录技巧
- 目录扫描时如果混有 `.gz` 扩展名但实际是纯文本的文件会导致 `BadGzipFile` 错误

## 关联参考

- `<参考:/home/andymao/.hermes/skills/telecom/li-system-ops/SKILL.md>` — LI 系统全栈运维（ZTLIG 调试、配置对比、二进制分析、综合分析工作流）
- `knowledge/li/ZTLIG/ztlig-ligcdr-extract-tool.md` — 知识库文档版本
