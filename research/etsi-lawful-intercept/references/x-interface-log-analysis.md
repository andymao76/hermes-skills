# X 接口日志分析参考

## 日志格式与提取字段

四种 LI 系统日志的格式和关键字段提取模式：

### SSF (SIP 信令日志) — X2 信令面

```
[2026-06-23 10:57:19][DEBUG][ssf:1300][sipAddControlMsg] add ControlMsg success, LIID[8628] CIN[95119960] callid[qz2qsjzzlu6lz7hjq2py7ph2puqzoylp@10.18.5.64]
```

提取字段: timestamp, level(DEBUG), module(ssf), port(1300), function(sipAddControlMsg), LIID, CIN, callId, sipMethod(INVITE/BYE/200 等)

### RVF (RTP 媒体日志) — X3 媒体面

```
[2024-08-01 10:48:52][INFO ][rvf:1420][rvfFindMavenirSessionId]:find session success!, liid[10078], correlationID[2200034c0-3-429566ab3ee3]
```

提取字段: timestamp, level(INFO), module(rvf), port(1420), function, LIID, correlationID, rtpSessionId, mediaCtrlType

### ZTLIG1 (X1 管理日志) — X1 管理面

```
[2025-12-22 08:01:23][ERROR][ztlig1:300]startup ZTLIG-1 error[reason:failed to get license,name=eric_lis_v2dot4]
[2025-12-22 08:01:26][DEBUG][ztlig1:300][INFORM][ztlig1-db][ztlig_module_neid_add]:add succeeded [seq=473,type=32,tneID=32]
```

提取字段: timestamp, level(ERROR/DEBUG), module(ztlig1), port(300), command(recv start init req/add succeeded/failed to get license), neid, result(success/failed/error), ip

### ZTLIG2 (IRI/CDR 日志) — X2 信令面

```
[2025-12-22 08:01:27][INFO ][ztlig2:461]ztlig2 module is starting...
[2026-06-23 ...][DEBUG][ztlig2:460] { "CdrType": "LigCdr", "LIID": "12345", "CidNum": "67890", ... }
```

提取字段: timestamp, level, module(ztlig2), port, LIID(从内嵌 JSON 提取), CIN, EventDetail, hasLigCdr

## 解析坑点

1. **LOG_HEADER_RE 尾随空格**: `[INFO ]` (有空格) vs `[INFO]` (无空格)，正则必须写 `(\w+)\s*` 不能只写 `(\w+)`
2. **ztlig2 .txt 可能是 gzip**: `file` 命令检测到 `gzip compressed data` 则 `.txt` 实际是压缩文件，读取时需处理
3. **SSF callid 大小写不定**: log 中可能写 `callId` 或 `callid`，正则需 `[Ii][Dd]` 忽略大小写
4. **大量行数限制**: 日志文件可能几百万行，解析时需限制前 N 行（默认 500000）

## 实测验证数据

使用真实日志文件的测试结果（ETSI-ASN1-Assistant V4.0 x_interface_decoder）：

| 日志类型 | 文件 | 解析行数 | 提取LIID | ERROR数 | 时间跨度 |
|---------|------|---------|---------|--------|---------|
| SSF | ssf.1300.txt | 535 | 33 | 0 | ~1分钟 |
| SSF (大文件) | ssf.1300.txt (200KB) | 1070 | 52 | 0 | 10:57~10:58 |
| ZTLIG2 | ztlig2.461.txt | 682 | 1 | 0 | 启动日志 |
| ZTLIG1 | ztlig1.300.txt | 1363 | 0 | 6 | license失败 |
| RVF | rvf.1420.txt | 1050 | 1 | 0 | 媒体会话 |

LLM 解析准确率: 100% (4种格式全部正确提取 LIID/接口分布/ERROR数)

## API 接口

```
POST /x-interface-analyze
  Body: { "content": "log text", "subtype": "ssf|rvf|ztlig1|ztlig2|auto", "filename": "ssf.1300.txt" }
  Return: { "parsed": [...], "raw": [...], "stats": {...} }
```

子类型自动检测规则: 根据 filename 中是否包含 ztlig1/ztlig2/ssf/rvf 前缀识别。

## 前端分栏布局

双栏展示:
- **左栏**: 解析结果 — 时间/级别/模块:端口/LIID/CIN/callId等关键字段
- **右栏**: 原始日志文本
- **过滤**: LIID / CIN / 关键词 / ERROR级别实时过滤
- **统计**: 总行数 / 解析行 / ERROR数 / LIID数 / 时间范围
