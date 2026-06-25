# ZTLIG2 LigCdr JSON 提取工具（extract_ligcdr.py）V1.2

## 位置
`~/PCAP/20260623-A1-VOWIFI/extract_ligcdr.py`

## 功能
从 ZTLIG2 日志文件（.txt/.log/.gz/.tar.gz/.zip）中批量提取 LigCdr JSON 记录。
V1.2 新增：
- **非 JSON 日志行文本匹配** — 不含 JSON 的日志行（如 `P-Charging-Vector`、SIP 消息头等）若包含过滤条件值，输出到 `raw_matches_filtered.txt`
- **EventDetail / Vendor / Neid 过滤实际生效** — 之前 argparser 定义了但未实现匹配逻辑，现已补齐
- **时间输入标准化** — 同时接受 `YYYYMMDDHHMMSS` 和 `YYYY-MM-DD HH:MM:SS` 格式

## 运行方式

### 交互模式（推荐，无参数运行）

```bash
cd ~/PCAP/20260623-A1-VOWIFI
python3 extract_ligcdr.py
```

交互式引导流程：

1. **选择输入源** — 扫描目录或指定单个文件
2. **快速预览** — 自动扫描文件头 50000 条，展示 LIID / MSISDN / CIN / 日期分布
3. **设置过滤条件** — 时间范围 / LIID / MSISDN / CIN / EventDetail / Vendor / Neid，留空跳过
4. **输出设置** — 输出目录、去重、条数限制
5. **确认并执行** — 按 `LIID_CIN_时间` 命名输出 .txt + .json 文件对
6. **非 JSON 行自动筛选** — 无 JSON 结构的日志行若包含过滤条件值，追加到 `raw_matches_filtered.txt`
7. **可选 JSON Crack 可视化** — 自动复制前 5 个文件到 HTTP server

### 命令行模式（兼容 V1.0 参数）

```bash
# 统计
python3 extract_ligcdr.py A1-ztlig/ztlig2.460 --liid 10331 --stats

# 过滤输出（按 LIID+CIN+时间命名文件对到目录）
python3 extract_ligcdr.py A1-ztlig/ztlig2.460 --liid 10331 --unique --limit 50 -o /tmp/output

# 按时间范围 + MSISDN 过滤
python3 extract_ligcdr.py A1-ztlig/ztlig2.460 \
  --time-start 20251222000000 --time-end 20251222235959 \
  --msisdn 249123022580 -o /tmp/output

# 按 CIN 过滤（自动捕获 P-Charging-Vector 等非 JSON 关联行）
python3 extract_ligcdr.py A1-ztlig/ztlig2.460 --cin 95138331 -o /tmp/output

# V1.2: 按 EventDetail 过滤 (Begin/Answer/Release)
python3 extract_ligcdr.py A1-ztlig/ztlig2.460 -e 10,11,13 --liid 10331 -u -L 100 -o /tmp/output

# V1.2: 按 Vendor + Neid 过滤
python3 extract_ligcdr.py A1-ztlig/ztlig2.460 -V hw -n 7024 -L 50 -o /tmp/output

# V1.2: 时间支持 YYYY-MM-DD HH:MM:SS 格式
python3 extract_ligcdr.py A1-ztlig/ztlig2.460 \
  --time-start "2025-12-22 00:00:00" --time-end "2025-12-22 23:59:59" \
  --liid 10331 -o /tmp/output
```

## 过滤规则

| 字段 | JSON 结构匹配 | 非 JSON 行匹配 |
|------|-------------|---------------|
| LIID | 精确匹配 JSON 字段 | 文本子串搜索（`LIID` 值出现在行中） |
| MSISDN | 精确匹配 JSON 字段 | 文本子串搜索 |
| CIN (CidNum) | 精确匹配 JSON 字段 | 文本子串搜索 |
| EventDetail | JSON 字段 in list (`-e 10,11,13`) | 数字文本片段匹配 |
| Vendor | 精确匹配（不区分大小写） | 不区分大小写子串 |
| Neid | 精确匹配 JSON 字段 | 文本子串搜索 |
| 时间范围 | JSON CaptureTime 字段 | `[YYYY-MM-DD HH:MM:SS]` 或 `YYYYMMDDHHMMSS` |

非 JSON 行匹配仅在**设置了过滤条件时**激活。无条件时只走 JSON 提取路径。

## 输出文件

按 `LIID_CIN_CaptureTime.txt` / `.json` 格式命名：

- **`.txt`** — 原始日志行（保留完整上下文：时间戳、ztlig2模块名、Kafka topic等）
- **`.json`** — 结构化 JSON array（可直接用 JSON Crack 或 jq 处理）
- **`raw_matches_filtered.txt`** — **V1.2 新增** 非 JSON 日志行，每行带 `[source]` 前缀

```text
/tmp/output/
├── 10331_95138331_20251222115837.txt        # 原始日志行
├── 10331_95138331_20251222115837.json        # 结构化 JSON
├── 10331_95138331_20251222115926.txt
├── 10331_95138331_20251222115926.json
├── raw_matches_filtered.txt                  # V1.2 — 非 JSON 行
└── ...
```

### 原始日志行示例（.txt）
```text
[2025-12-22 11:58:37][INFO ][ztlig2:461][ZtligKafkaProduceMsgByKey]
topic[OWLS_TMC_REALTIME] leaid[1]
msg[{"CdrType":"LigCdr","LIID":"10331","CidNum":"95138331",...}]
len[1-331] totalLen[331]
```

### 非 JSON 行示例（raw_matches_filtered.txt）
```text
[cid-100827-target.txt] ztlig2.467.txt:P-Charging-Vector: icid-value="psdpcscf02.191.36d4.20260623100827"
[cid-100827-target.txt] ztlig2.467.txt:P-Charging-Vector: icid-value="psdpcscf02.191.36d4.20260623100827"
```

## 可视化工作流

```bash
# 1. 交互模式提取时选 JSON Crack → 自动复制到 ~/.hermes/sessions/
# 2. 打开 URL：http://localhost:3001/editor?http://localhost:8888/<文件名>.json
```

或手动：
```bash
# 直接用 ijq 交互查看
python3 extract_ligcdr.py --liid 10331 --unique -o /tmp/sample.jsonl
ijq -C /tmp/sample.jsonl

# 或输出 JSON array 给 JSON Crack
python3 -c "
import json
objs = [json.loads(l) for l in open('/tmp/sample.jsonl')]
json.dump(objs, open('/tmp/sample.json', 'w'), indent=2, ensure_ascii=False)
"
cp /tmp/sample.json ~/.hermes/sessions/
# http://localhost:3001/editor?http://localhost:8888/sample.json
```

## 命令行参数

| 参数 | 别名 | 说明 |
|------|------|------|
| `--interactive` | `-i` | 交互模式（默认无参时进入） |
| `--time-start` | - | 起始时间 (YYYYMMDDHHMMSS 或 YYYY-MM-DD HH:MM:SS) |
| `--time-end` | - | 结束时间 (同上) |
| `--liid` | `-l` | 过滤 LIID |
| `--msisdn` | `-m` | 过滤 MSISDN |
| `--cin` | `-c` | 过滤 CidNum (CIN) |
| `--event-detail` | `-e` | 过滤 EventDetail (逗号分隔，如 10,11,13) |
| `--vendor` | `-V` | 过滤 Vendor（如 hw） |
| `--neid` | `-n` | 过滤 Neid |
| `--stats` | `-s` | 显示统计信息 |
| `--output` | `-o` | 输出目录（默认 /tmp/ztlig_output） |
| `--unique` | `-u` | 去重 |
| `--limit` | `-L` | 最大输出条数 |

## 文件格式支持

- `.txt` / `.log` — 普通文本
- `.gz` — 自动 gzip 解压
- `.tar.gz` / `.tgz` — 自动解压 tar 内所有文件
- `.zip` — 自动解压 zip 内所有文件
- 使用 8MB 分块流式解析，适合数 GB 大文件
- 自动跳过 tar 中的隐藏文件（`.` 开头）和目录项

## 历史

- **V1.0** — 2025-06-25: 基础 CLI 版，支持 JSONL 输出、过滤、去重、统计、ijq/jsoncrack
- **V1.1** — 2025-06-25: 交互菜单、.tar.gz/.zip 支持、时间/CIN 过滤、原始日志+JSON双输出
- **V1.2** — 2026-06-25: 非 JSON 日志行文本匹配筛选、EventDetail/Vendor/Neid 过滤生效、时间输入标准化
