# ETSI-ASN1-Assistant 工具参考

## 项目位置

- **源代码**: `~/projects/ETSI-ASN1-Assistant/`
- **GitHub**: `andymao76/ops-monitoring/etsi-asn1-assistant/` (branch: V4)
- **当前版本**: V4.0.1 (2026-06-27)
- **启动方式**: `venv/bin/python3 src/app_linux_v4.py` (端口 5000)
- **文档**: `docs/README.md`（含完整使用指南）

## V4.0 模块架构

```
app_linux_v4.py (Flask Web)
  ├── asn_decode_iri_report_v4.py   # IRI 后处理 + Location BCD 对齐
  ├── asn_decode_api_v4.py           # BER 解码引擎 + 14字节头增强
  ├── asn_decode_x3_v4.py            # X3 媒体面 (RTP/IP) — 新建
  ├── asn_decode_hi1_v4.py           # HI1 管理接口 — 新建
  ├── hw_header_decode_v4.py         # 华为私有帧头库 — 新建
  ├── kafka_consumer_v4.py           # Kafka 实时消费 — 新建
  ├── x_interface_decoder.py         # X 接口日志分析 (SSF/RVF/ZTLIG) — 新建
  └── asn_spec_v4.py                 # ASN.1 规范管理 (10套)
```

## 12 种解码模式

hw-cs / hw-ims / zte-cs / mavenir / g2k / utimaco-volte /
hw-5gc / hw-sae / nsn-cs / zte-epc / x3 / hi1

## V4.0.1 改进

### 1. BER 解码容错 (asn_decode_api_v3/v4)
`pre_decode_split_report()`: BER 声明长度超出可用数据时取剩余全部数据，避免截断 TCP 片段导致后续全部 BER 消息解码失败。

### 2. 0xAA 帧头自动检测 + TCP 重组提示 (app_linux_v4.py)
上传 PCAP 时自动扫描前 50 包，检测 ≥3 个 0xAA 华为帧头且 TCP 重组未开启时，结果页面顶部显示红色 warning 提示条。

### 3. 结果页面 warning 提示条 (templates/result.html)
条件渲染红色边框卡片，用于展示 0xAA 帧头检测、解码降级等非致命警告。

### 4. X 接口日志 — ZTLIG1 解码器大幅增强 (x_interface_decoder.py)
- 命令识别 7种 → **14种**，覆盖率 0.15% → 78%
- 新增: kafka_add_target / kafka_del_target / x1_send_cmd / hi1_queue / link_check / link_error / ne_no_response / location_report / etsi_liid_check / db_query / redis_sync / list_target_rsp
- LIID `liid=XXX` / `liid[XXX]` 双格式兼容，实测提取 133 个 LIID
- 子模块提取 A/B/C 三种日志格式（INFORM+子模块 / 直接子模块 / 裸 body），覆盖率 99%
- 新增字段: sub_module / vneid / account / reason

### 5. X 接口日志集成到主页面
不再需要访问独立 `/x-interface` 路由。主页面上传区改为三列布局。`/x-interface` 路由保留向后兼容。

## 使用指南

详见 `docs/README.md` 的 `📖 使用指南` 章节。

### PCAP 文件解码正确步骤

1. **必须勾选「TCP 重组」** — 将 TCP 分片重组为完整 HI2 消息
2. **必须输入端口过滤** — 只解码 X2 口数据
   - 华为 IMS X2 口：8890
   - 华为 CS X2 口：9904 / 9905
3. 选择对应解码模式（默认 hw-ims）
4. 点击「上传并解析」

**典型效果对比（7.6MB PCAP）：**

| 配置 | 数据包数 | 页面大小 | 成功解码 |
|------|---------|---------|---------|
| 无过滤+无重组 | 34,047 | 57MB | 0 ❌ |
| 端口8890+TCP重组 | 61 | 432KB | 60 ✅ |

**常见错误：**
- 大量「报文格式错误」⚠️ → 未端口过滤，非 X2 口包被尝试解码
- 大量「解码失败」❌ → 未开启 TCP 重组，分片被独立解码
- 页面卡死 → 无过滤时 8MB PCAP 生成 57MB+ HTML

### X 接口日志分析

| 日志类型 | 接口 | 文件名特征 | 说明 |
|---------|------|-----------|------|
| ZTLIG1 | X1 管理面 | ztlig1*.txt | 设控/停控/网元通信日志 |
| ZTLIG2 | X2 信令面 | ztlig2*.txt | IRI CDR JSON 日志 |
| SSF | X2 SIP 信令 | ssf*.txt | SIP 会话管理日志 |
| RVF | X3 RTP 媒体 | rvf*.txt | RTP 媒体流日志 |

大文件自动截断前 5MB（521MB 的 ztlig1.300.txt 约覆盖 3 天）。
ZTLIG1 日志需文件名含 `ztlig1` 自动识别。

### IRI 报告文件
上传纯十六进制文本文件（BER 编码的 IRI 报告）。**不适合上传文本日志文件。**

## X 接口日志分析

集成在主页面三列布局最右侧。四种日志类型解析：

| 日志 | 接口 | 提取字段 |
|------|------|---------|
| SSF | X2 (SIP 信令) | LIID/CIN/callId/SIP 方法 |
| RVF | X3 (RTP 媒体) | liid/correlationID/rtpSessionId |
| ZTLIG1 | X1 (管理面) | 14种命令/LIID/NEID/子模块/ERROR |
| ZTLIG2 | X2 (IRI/CDR) | LIID/CIN/EventDetail + 内嵌 LigCdr JSON |

双栏分栏展示，支持 LIID/CIN/关键词/ERROR 级别实时过滤。

## 常见坑

### 1. BER 长度截断 (V4.0.1 fix)
`pre_decode_split_report()` 中 BER TLV 声明长度超出可用数据时取剩余全部数据：
```python
if offset + header_len + single_len > total_len:
    message = data[offset:]
    report.append(message)
    break
```

### 2. TCP 重组必须启用
华为 X2 帧可能 >1460B 跨 TCP 段。检测到 ≥3 个 0xAA 帧头但重组未开时显示红色 warning。

### 3. 大文件 Chrome SIGILL
前端 `file.slice(0, 5MB)` + 后端 `content[:5MB]` 双重截断。

### 4. LOG_HEADER 尾随空格
LEVEL 字段可能有尾随空格（`[INFO ]`），正则必须写 `(\\w+)\\s*`。

### 5. ztlig2 可能是 gzip 伪装
`ztlig2.*.txt` 可能是 gzip 压缩，用 `errors='replace'` 处理。

### 6. extract_key_info None key 崩溃
修复：`if k is None or (isinstance(k, str) and k.startswith('_'))`。

### 7. HI1 ASN.1 编译链
`HI1NotificationOperations,ver7.asn` 不能独立编译，需链式包含。

### 8. ZTLIG1 日志三种格式（V4.0.1）
```
格式 A: [时间][LEVEL][ztlig1:port][INFORM/ERROR][子模块名][函数名]:body
格式 B: [时间][LEVEL][ztlig1:port][子模块名]:body
格式 C: [时间][LEVEL][ztlig1:port]:body
```
子模块提取：若 function 是日志级别标签 → 从 body 提取 `[xxx]`；否则直接用 function 值。

## 版本升级检查清单

- [ ] 所有源文件重命名 v3→v4（含 PDF/PNG 等二进制文件）
- [ ] 旧文件名同时保留 V3 备份
- [ ] 版本号更新: PY 文件头 / logger / Flask banner
- [ ] 模板版本号: upload/result/result1 中所有 Vx.x
- [ ] VERSION_HISTORY.md 新增条目
- [ ] README 更新为当前版本
- [ ] 系统设计文档: 修订记录 + frontmatter + H1 标题
- [ ] 架构文档: 新增章节 + 功能定位更新
- [ ] 架构图: HTML / SVG / PDF / PNG 全部重建
- [ ] GitHub 推送前检查 `.gitignore`
- [ ] 使用指南同步到 docs/README.md
