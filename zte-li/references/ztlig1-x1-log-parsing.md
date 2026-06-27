# ZTLIG1 X1 日志解析参考

此文件记录 ZTLIG1 X1 日志解析的核心知识，供 ETSI-ASN1-Assistant 解码器开发和排障使用。

## 日志格式（A/B/C 三种变体）

参见 SKILL.md 中「ZTLIG1 日志三种格式」表格，三种格式由 LOG_HEADER_RE 的第5组值区分。

## 命令分类（14种）

参见 SKILL.md 中「ZTLIG1 X1 操作命令分类」表格。

## LIID 提取

两种格式：`liid[12345]` 和 `liid=12345`。正则：`r'liid(?:\\[|=)(\\d+)\\]?'`

## 子模块提取逻辑

```python
LOG_LEVEL_TAGS = {"INFORM", "ERROR", "WARNING", "DEBUG", "ALARM", "INFO", "TRACE"}
fn = result.get("function", "")
if fn in LOG_LEVEL_TAGS:
    # 格式A: body 开头 [ztlig-1_hwne] 才是子模块
    m_sub = re.search(r'^\\[([^\\]]+)\\]', body)
    if m_sub: result["sub_module"] = m_sub.group(1)
elif fn and not fn.startswith("process:"):
    # 格式B: function 已是子模块名
    result["sub_module"] = fn
```

## 综合分析报告（四类日志）

### 报告分发

后端统一通过 `generate_report(subtype, parsed_lines)` 分发到各类型的专用报告函数。API 在 subtype 匹配时返回 `report` 字段。

```python
# x_interface_decoder.py
def generate_report(subtype: str, parsed_lines: list) -> dict:
    if subtype == "ztlig1": return generate_ztlig1_report(parsed_lines)
    elif subtype == "ztlig2": return generate_ztlig2_report(parsed_lines)
    elif subtype == "ssf": return generate_ssf_report(parsed_lines)
    elif subtype == "rvf": return generate_rvf_report(parsed_lines)
    return None
```

### ZTLIG2 报告 (`generate_ztlig2_report`)

```python
# 关键统计
liid_dist = Counter()      # LIID 分布
event_detail = Counter()   # EventDetail (10=呼叫发起, 13=释放等)
network_type = Counter()   # 网络类型
ligcdr_count = 0           # LigCdr JSON 行数
```

返回字段：`title` / `time_range` / `total_lines` / `errors` / `liid_count` / `top_liids` / `event_detail` / `network_type` / `ligcdr_count` / `samples`

### SSF 报告 (`generate_ssf_report`)

```python
liid_dist = Counter()     # LIID 分布
sip_methods = Counter()   # SIP 方法 (INVITE/BYE/REGISTER等)
call_ids = set()          # 唯一 CallID 数
```

返回字段：`title` / `time_range` / `total_lines` / `errors` / `liid_count` / `top_liids` / `sip_methods` / `call_id_count` / `samples`

### RVF 报告 (`generate_rvf_report`)

```python
liid_dist = Counter()      # LIID 分布
corr_ids = set()           # 唯一 CorrelationID 数
rtp_sessions = set()       # 唯一 RTP 会话数
media_types = Counter()    # 媒体控制类型分布
```

返回字段：`title` / `time_range` / `total_lines` / `errors` / `liid_count` / `top_liids` / `correlation_id_count` / `rtp_session_count` / `media_types` / `samples`

### 前端自适应展示

`buildReportHTML(report)` 根据报告中的字段动态渲染：

```javascript
// 概览 badges: 根据字段存在与否决定显示哪些
// 基础: time_range, total_lines, errors, liid_count
// 可选: call_id_count, correlation_id_count, rtp_session_count, ligcdr_count

// 操作统计: 自适应命令/方法/事件类型
const cmdList = r.commands || r.sip_methods || r.event_detail || null;
const cmdLabel = r.commands ? 'X1 操作统计' : (r.sip_methods ? 'SIP 方法分布' : 'EventDetail 分布');

// 独有章节: 仅在对应字段存在时显示
if (r.sub_modules) { /* ZTLIG1 子模块 */ }
if (r.set_target_count !== undefined) { /* ZTLIG1 设控停控 */ }
if (r.ne_faults) { /* ZTLIG1 网元故障 */ }
```

### ZTLIG1 报告 (`generate_ztlig1_report`)

含之前的完整内容：sub_modules / commands / liid_count / top_liids / set/del_target_count / ne_faults / samples / error_samples
- sub_modules: 子模块名/条数/占比
- commands: 命令名/次数
- liid_count + top_liids: LIID 总数 + Top15
- set/del_target_count + liid_count: 设控停控统计
- ne_faults: link_check/link_error/no_response + 故障 NE Top
- samples: 8 类关键日志原文
- error_samples: ERROR 级别原文

前端 `buildReportHTML(report)` 渲染在 stats 栏下方，左栏自动切换为 `buildParsedSummary(parsed, report)` 摘要模式。

## 左栏摘要模式

当报告存在时，左栏从逐行显示切换为按命令类型分组的摘要卡片，按 🔴网元故障 / 📋设控停控 / ⚙️其他 三个区段排列。每个命令卡片显示：次数、涉及的 LIID/NE 列表、前 3 条 body 样本。

## 输出报告按钮

分析完成后，导出按钮栏显示「📥 输出 Markdown 报告」按钮。Markdown 格式为纯文本表格，可直接存入知识库或 Obsidian。HTML 导出已移除。

导出报告包含全部章节：概览 / 子模块分布 / X1 操作统计 / LIID 统计 / 设控停控 / 网元通信故障（红色高亮）/ 关键样本（8类）。

## PCAP TCP 重组原理（核心经验）

### 为什么要 TCP 重组？

TCP 会把大消息切成小片发送。以太网 MSS（最大段大小）通常为 1460 字节，而华为 X2 口的 HI2 消息通常几百到几千字节，因此一个完整的 HI2 消息会被 TCP 切成多个 TCP Segment：

```
TCP 分片示例（单个 HI2 消息 3300 字节）：
  [包1] TCP Seq=1000, Len=1460   ← HI2 消息前 1460 字节
  [包2] TCP Seq=2460, Len=1460   ← 中间 1460 字节
  [包3] TCP Seq=3920, Len=380    ← 最后 380 字节
```

不重组时：
- 包1 → BER 声明长度 2000 > 仅 1460 字节 → 报文格式错误
- 包2 → 起始字节不是 BER TAG → 解码失败
- 包3 → 起始字节不是 BER TAG → 解码失败

重组后：3 个分片拼回 3300 字节完整消息 → BER 解码成功。

### 实测数据对比

| 配置 | a8b0f01b (7.6MB) | c8381c8b (11.5MB) |
|------|-------------------|-------------------|
| 无重组 + 无端口过滤 | 34,047 包, 全部失败 | 52,098 包, 全部失败 |
| 页面大小 | 57MB（浏览器卡死）| 89MB（浏览器卡死）|
| TCP重组 + 端口8890 | **61 包, 60 成功** | **62 包, 61 成功** |
| 页面大小 | **432KB** | **407KB** |

### 使用要点

- PCAP 上传时必须勾选「TCP 重组」并输入端口过滤（华为 IMS X2 口 8890）
- 端口过滤可大幅减少非 X2 口报文的解码失败
- 过滤后 PCAP 可用 `dpkt` 脚本预处理（示例见知识库经验文档）

## 验证方法

参见 SKILL.md 中「ZTLIG1 解析器验证方法论」。

验证脚本 `scripts/verify-ztlig1-parser.py` 支持：
- `--unit-only` 仅运行 13 个单行测试
- 传日志路径参数运行大文件 5MB 实测
- 新增 `test_report_generation()` 测试 generate_ztlig1_report 报告生成（参数完整性检查）
