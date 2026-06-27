# ETSI-ASN1-Assistant V4 X接口日志分析工具

Web 版 LI 日志分析工具，支持 SSF/RVF/ZTLIG1/ZTLIG2 四种日志的分栏解析。

## 访问方式

- 主页 → 点击「🔬 X 接口日志 →」
- 或直接访问 `http://localhost:5000/x-interface`

## 支持的日志类型

| 日志 | 接口 | 识别特征 | 提取字段 |
|------|------|---------|---------|
| SSF | X2 (SIP信令) | `[ssf:NNNN]` | LIID, CIN, callId, SIP方法 |
| RVF | X3 (RTP媒体) | `[rvf:NNNN]` | liid, correlationID, rtpSessionId |
| ZTLIG1 | X1 (管理面) | `[ztlig1:NNN]` | 命令, NEID, ERROR/结果 |
| ZTLIG2 | X2 (IRI) | `[ztlig2:NNN]` | LIID, CIN, LigCdr JSON |

## 解析器源码

`~/projects/ETSI-ASN1-Assistant/src/x_interface_decoder.py`

## 已知陷阱

1. **callId大小写**: SSF日志中可能是 `callid[...]`（全小写d），正则 `call[Ii][Dd]` 解决
2. **Level尾部空格**: RVF日志 `[INFO ]` 尾部空格，正则 `(\w+)\s*\]` 解决
3. **大文件**: 浏览器端只读前5MB，超量用 CLI 工具
4. **假 .gz**: A1-ztlig 目录下 `.gz` 文件可能是纯文本
