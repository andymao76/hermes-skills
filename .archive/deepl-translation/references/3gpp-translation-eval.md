# 3GPP TS 25.331 翻译评测 — 2025-06-08

## 测试参数

| 指标 | 值 |
|------|-----|
| 文档 | 3GPP TS 25.331 V6.7.0 RRC Protocol Specification (节选) |
| 源语言 | 英语 (自动检测: EN ✅) |
| 目标语言 | 中文 (ZH) |
| 原文长度 | 5,347 字符 |
| 译文长度 | 2,228 字符 |
| 压缩比 | 2.4:1 (英文更冗长) |

## 评测结果

### 术语保留：★★★★★

以下电信术语全部正确保留或翻译：

| 原文 | 译文 | 评价 |
|------|------|------|
| Radio Resource Control (RRC) | 无线资源控制（RRC） | ✅ 中英双语保留 |
| UE / UTRAN | UE / UTRAN | ✅ 不翻译，正确 |
| Signalling Radio Bearers (SRBs) | 信令无线承载（SRB） | ✅ 完美 |
| RLC acknowledged mode (AM) | RLC确认模式（AM） | ✅ 完美 |
| IMSI / TMSI / P-TMSI | IMSI / TMSI / P-TMSI | ✅ 正确保留 |
| U-RNTI / C-RNTI | U-RNTI / C-RNTI | ✅ 正确保留 |
| CELL_DCH / CELL_FACH / CELL_PCH / URA_PCH | CELL_DCH / CELL_FACH / CELL_PCH / URA_PCH | ✅ 状态名不翻译 |

### 规范用语：★★★★★

| 原文 | 译文 | 评价 |
|------|------|------|
| "shall perform the procedures" | "应执行...程序" | ✅ RFC-style "shall" → "应" |
| "may initiate" | "可启动" | ✅ "may" → "可" |
| "is classified as irrecoverable" | "被归类为不可恢复" | ✅ 准确 |
| "The present document specifies" | "本文件规定了" | ✅ 规范文档格式 |
| "subclause 8.1.2" | "8.1.2子条款" | ✅ 技术引用保留 |

### 协议消息名：★★★★☆

| 原文 | 译文 | 评价 |
|------|------|------|
| RRC CONNECTION REQUEST message | RRC CONNECTION REQUEST 消息 | ✅ |
| RRC CONNECTION SETUP message | RRC连接建立消息 | ⚠️ 丢失英文原名 (5.2) |
| RRC CONNECTION SETUP COMPLETE message | RRC连接建立完成消息 | ⚠️ 丢失英文原名 (5.3) |
| Establishment cause | 建立原因 | ✅ |
| Protocol error indicator | 协议错误指示符 | ⚠️ 3GPP规范用"指示"非"指示符" |

### 轻微瑕疵

1. **"协议错误指示符"** → 3GPP规范中 Standard phrase 为"协议错误指示"，"指示符"略显生硬
2. **5.2/5.3节消息名丢失英文原名** → 建议在技术文档中保留英文消息名作为对照

### 状态机翻译

RRC_IDLE / RRC_CONNECTED 两句连在一起时出现了一段轻微重叠/冗余译文，但不影响理解。单独翻译状态描述时表现完美。

## 结论

DeepL 翻译 3GPP 技术规范质量**完全可用**。术语保留、规范用语、流程描述三大核心维度均达到出版级水平。轻微瑕疵（1-2处用词偏差）在技术文档中可忽略，不影响阅读理解和专业准确性。

建议：
- 整本翻译：DeepL 文档翻译功能（上传PDF）
- 关键段落：DeepL 初译 + 人工校对 IE 字段名
- 日常查阅：CLI 脚本秒译
