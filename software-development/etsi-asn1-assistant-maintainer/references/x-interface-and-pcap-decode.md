# X 接口日志分析 & PCAP 解码参考 (V4.1)

## ZTLIG2 JSON 栈匹配 (V4.1)

V4.0 使用正则 `\{[^{}]*"CdrType"[^{}]*\}` 只能匹配无嵌套的 JSON。V4.1 改用 `_extract_json_with_cdrtype()` 栈匹配:

```python
def _extract_json_with_cdrtype(body: str):
    idx = body.find('"CdrType"')
    if idx == -1: return None
    start = body.rfind('{', 0, idx)
    if start == -1: return None
    depth = 0
    for i in range(start, len(body)):
        if body[i] == '{': depth += 1
        elif body[i] == '}':
            depth -= 1
            if depth == 0:
                import re
                return re.match(re.escape(body[start:i+1]), body)
    return None
```

支持嵌套 JSON 如:
```
{ "CdrType": "LigCdr", "EventDetail": { "EventType": "CallStart", "Direction": "MO" } }
```

## 验证清单 (V4.1)

| 测试项 | 命令 | 预期 |
|--------|------|------|
| 单元测试 | `venv/bin/python3 -m pytest src/tests/test_all.py -v` | 38 passed |
| HW-CS PCAP | curl -F "pcap_file=@file.pcap" -F "decode_type=hw-cs" localhost:5000/ | HTTP 200, LIID解码 |
| X3 RTP | curl -F "pcap_file=@file.pcap" -F "decode_type=x3" localhost:5000/ | HTTP 200, RTP/PCMA解码 |
| ZTLIG1日志 | curl -X POST -H "Content-Type: application/json" -d '{"content":"...","subtype":"ztlig1"}' localhost:5000/x-interface-analyze | 行数/ERROR/LIID统计 |
| ZTLIG2嵌套JSON | 同上, subtype=ztlig2 | 嵌套EventDetail正确解析 |
| 大文件上传 | dd if=/dev/zero of=/tmp/test_200m.bin bs=1M count=200; curl -F "pcap_file=@/tmp/test_200m.bin" ... | HTTP 200（已实测200MB） |
| 导航完整性 | curl -s localhost:5000/ | grep -oP '/x-interface' | 必须包含X接口日志链接 |
| 版本统一 | grep -rn "V4\.[0-9]" --include="*.py" --include="*.html" --include="*.md" src/ templates/ docs/ README.md | grep -v "venv\|__pycache__\|import\|asn1tools" | 全部一致 |
| 测试报告 | 写入 `docs/测试验证报告_V4.1.md` | 覆盖所有变更项 |

## 大文件处理策略

| 文件大小 | 浏览器加载 | 后端处理 | 返回内容 |
|---------|-----------|---------|---------|
| ≤5MB | 全量读取 | 全量解析 | 报告+逐行解析(10000行)+全量原始 |
| >5MB | 读取前10MB | 全量处理 | 报告+摘要(5000条)+原始预览(1000行) |

大文件右栏显示「⚠️ 文件过大 (NNMB)，右栏仅显示前 1000 行预览」

## 综合分析报告

四种日志的报告对比:

| 维度 | ZTLIG1 | ZTLIG2 | SSF | RVF |
|------|--------|--------|-----|-----|
| 概览标签 | ✅ | ✅ | ✅ | ✅ |
| 子模块分布 | ✅ | - | - | - |
| 操作统计 | 14种命令 | EventDetail | SIP方法 | 媒体类型 |
| LIID Top | ✅ | ✅ | ✅ | ✅ |
| 设控/停控 | ✅ | - | - | - |
| 网元通信故障 | ✅ | - | - | - |
| 关键样本 | 8类命名 | 通用3条 | 通用3条 | 通用3条 |
| 关键发现 | ✅ | ✅ | ✅ | ✅ |

## JS 排障: 花括号不匹配

当点击"分析"按钮无任何反应时，第一检查点:

```bash
# 检查花括号平衡
python3 -c "
import re
s = open('src/templates/x_interface.html').read()
scripts = re.findall(r'<script[^>]*>(.*?)</script>', s, re.DOTALL)
print('{' 数:', scripts[0].count('{'))
print('}' 数:', scripts[0].count('}'))
print('平衡:', scripts[0].count('{') == scripts[0].count('}'))
"
```

常见诱因: 删除 HTML 导出按钮时残留的 else 块闭合括号 `}`。

## 导出文件名格式

```
{原始文件名去后缀}-分析报告-{YYYYMMDD-HHMMSS}.md
```

示例: `ssf.1301-分析报告-20260628-235959.md`
