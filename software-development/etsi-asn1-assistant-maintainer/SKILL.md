---
name: etsi-asn1-assistant-maintainer
description: "维护 ETSI-ASN1-Assistant V4 — 华为LI X2接口IRI解码Web工具的全生命周期操作: 加功能/修BUG/测试/文档/部署/GitHub推送"
version: 1.0.0
author: Hermes Agent
tags: [li, huawei, hi2, asn1, vowifi, ztlig]
---

# ETSI-ASN1-Assistant 维护指南

## 项目位置
- 源码: `~/projects/ETSI-ASN1-Assistant/`
- GitHub: `andymao76/ops-monitoring/etsi-asn1-assistant/`
- 测试数据: `~/PCAP/20260623-A1-VOWIFI/` (SSF/RVF/ZTLIG1/ZTLIG2/PCAP)

## 核心模块

```
src/
├── app_linux_v4.py              # Flask 主入口
├── asn_spec_v4.py               # ASN.1 规范加载(10套)
├── asn_decode_api_v4.py         # BER 解码引擎 + 14字节头解析
├── asn_decode_iri_report_v4.py  # 字段后处理 + Location BCD对齐
├── asn_decode_x3_v4.py          # X3 媒体面(RTP)解码
├── asn_decode_hi1_v4.py         # HI1/X1 管理接口解码
├── hw_header_decode_v4.py       # 华为私有X1/X3帧头库
├── kafka_consumer_v4.py         # Kafka实时消费
├── x_interface_decoder.py       # X接口日志分析(SSF/RVF/ZTLIG)
├── templates/                   # HTML模板(上传/结果/X接口)
├── asnfile/                     # 24个ASN.1规范文件
└── tests/test_all.py            # 38个单元测试
```

## 标准工作流

### 1. 加功能/修BUG
```
① 修改源码 (asn_decode_api_v4.py / app_linux_v4.py / x_interface_decoder.py 等)
② 同时修 asn_decode_api_v3.py (保持V3兼容)
③ 验证: ~/projects/ETSI-ASN1-Assistant/venv/bin/python3 src/app_linux_v4.py
④ 单元测试: pytest src/tests/test_all.py -v
⑤ 写测试报告: docs/tests/*.md
⑥ 写变更日志: docs/changelog/*.md
⑦ 写知识库: ~/knowledge/telecom/lawful_interception/*.md
⑧ 更新使用指南: docs/README.md
⑨ 推送: git add -A && git commit -m "主题" && git push origin V4
```

### 2. 解码流程
```
PCAP → TCP重组(必须) → 端口过滤8890(必须) → 14B帧头(0xAA)剥离 
→ BER解码(asn1tools) → iRI-Report-record → SIP提取 → PANI/CIN/LIID提取
```

### 3. 页面结构 (V4.0.1)
```
/              → HI2解码 (PCAP + IRI 两列布局)   [导航标签: 📡HI2解码]
/x-interface   → X接口日志分析 (双栏+过滤+统计)    [导航标签: 🔬X接口日志]
```
顶部导航标签在两个页面间切换。两个页面独立，各司其职。

### 4. PCAP 使用要点（核心经验）
- **必须勾选「TCP 重组」** — TCP 分片不重组时每片单独解码全部失败
- **必须输入端口过滤** — 无端口过滤时全量网络包(7.6MB→34,047包)全部渲染为解码失败
- 华为IMS X2口=8890, CS X2口=9904/9905, 中兴EPC X2口=8890
- 正确配置后: 7.6MB → 61包 → 432KB页面 → 60条成功解码
- 端口过滤输入框使用蓝色边框(border-color:#2a5a8c)高亮引导
- 过滤条件卡片标题标红色「（必选）」提醒

### 5. X 接口日志分析要点
- 四种日志: ZTLIG1(X1管理) / ZTLIG2(X2信令) / SSF(SIP) / RVF(RTP)
- 接口类型只能手工选择（已移除Auto自动识别）
- 四种日志均支持综合分析报告（子模块/命令/LIID/故障/样本/每日统计/关键发现）
- 上传至主页面的「IRI报告文件」会尝试BER解码文本日志→全部失败
  → 文本日志必须在X接口日志页面(/x-interface)上传
- **分析流程**: 选择文件 → 点击分析 → ⏳进度步骤提示(文件读取/上传/处理/报告) → 报告展示
- **按钮状态**: 分析期间按钮文字变更为「⏳ 分析中...」→「📤 上传分析中...」, 处理期间禁用防重复点击
- **加载显示**: 页面中央显示文件名+大小+4步进度(大文件显示「仅读取前10MB」)
- **分析耗时**: 统计栏自动显示后端处理耗时(秒级)

### 6. 知识库存储
- LI经验文档: `~/knowledge/telecom/lawful_interception/`
- 使用指南+排障: `etsi-asn1-assistant-usage-guide.md`
- ZTLIG1日志分析: `ztlig1-x1-log-analysis.md`
- 索引: `kb-index index` (增量更新)

### 7. 生成DOCX报告
```python
# 用 gen_v4_report.py 模板 (方法写进报告)
# 依赖: docx (python-docx)
# 调用: decode_pcap_v4(pcap, 'hw_ims') → generate_report()
```

### 8. 文件命名规范
- 文档: 中文命名 (README.md / 系统设计文档.md / 测试报告.md)
- 源码: 英文 + _v4.py
- 变更日志: YYYY-MM-DD-主题.md

## 已知陷阱

### BER截断修复 (V4.0.1)
- 场景: TCP包<BER声明长度时(如包1460B但BER声明1802B)
- 根因: pre_decode_split_report 因长度超限直接break
- 修复: 超出时取剩余全部数据而非跳过

### TCP重组 (PCAP解码关键 ⭐)
- 场景: 7.6MB PCAP不设过滤→34,047包全部失败, 页面57MB浏览器卡死
- 根因: TCP分片(BER长度3300B在3个MSS=1460B的包里) 不重组每片解码失败
- 修复: parse_pcap(reassemble=True) + TCPStreamReassembler + 端口过滤8890
- 自动检测: app_linux_v4.py 检查前50个包中0xAA≥3个则提示
- 前端提示: 选择PCAP文件时弹出蓝色提示条引导勾选TCP重组+输入端口

### X1 ZTLIG1 日志解析 (V4.0.1 新增)
- 日志三种格式:
  - 格式A: `[时间][LEVEL][ztlig1:port][INFORM/ERROR][子模块][函数]:body`
  - 格式B: `[时间][LEVEL][ztlig1:port][子模块]:body`
  - 格式C: `[时间][LEVEL][ztlig1:port]:body`
- ZTLIG1_CMD_RE 从7种扩展为14种(覆盖率0.15%→78%)
- LIID格式兼容: `liid=XXX` 和 `liid[XXX]` 双格式
- 子模块提取: function为日志级别时(body中取[xxx]), 否则直接复用function
- 子模块清单: ztlig-1_web(73%) / ztlig-1_hwne(20%) / ztlig1-db(5%) / ztlig-1(2%) / ztlig-1_etsi(0.7%)

### JS花括号不匹配 → 整个页面按钮无反应 (V4.1 排障)
- **现象**: 点击按钮完全无反应, 控制台无报错, 服务器无API请求
- **根因**: `<script>` 内花括号 `{`/`}` 不匹配 → JS引擎拒绝加载整个脚本
  - `{` 116个, `}` 117个 → 语法错误 → 所有函数未定义
  - **次要根因**: `showLoading` 中 `el.querySelector('.card')` 不存在(emptyState无.card子元素) → TypeError, 但该错误只有在JS加载后才出现, 优先级低于花括号问题
- **排查方法**:
  ```bash
  python3 -c "
  import re
  s = open('x_interface.html').read()
  scripts = re.findall(r'<script[^>]*>(.*?)</script>', s, re.DOTALL)
  print('平衡:', scripts[0].count('{') == scripts[0].count('}'))
  "```
- **常见诱因**: 删除 `if/else` 块后未清理残留的闭合花括号
- **JS引擎特性**: 脚本内任何语法错误 → **整个脚本被拒绝**（非错误行之后）
- **预防**: 每次修改JS后运行括号匹配校验
- **参考**: `~/knowledge/01_PROJECTS/ETSI-ASN1-Assistant/x-interface-js-debug-20260628.md`

### 大文件处理策略 (V4.1 升级)
- V4.0 行为: 前端 file.slice(0, 5MB) + 后端 content[:5MB] → 521MB 日志丢失 97%
- V4.1 行为:
  - 前端: 读取前 10MB (大文件不阻塞浏览器, 改用 FileReader 兼容性更好)
  - 后端: 全量处理（无 size 限制）
  - 响应: >5MB 仅返回「综合分析报告 + 5000条摘要 + 1000行预览」
  - 右栏预览 + ⚠️大文件提示
- 分析耗时显示在统计栏卡片中
- **导出文件名**: `{原始文件名去后缀}-分析报告-{YYYYMMDD-HHMMSS}.md`
  通过后端返回 `_filename` 字段传递原始文件名

### X接口分析报告 (V4.1 新增)
- 四种日志均有独立报告: ZTLIG1/ZTLIG2/SSF/RVF
- 报告包含: 概览标签 / 子模块分布 / 操作统计 / LIID Top / 设控停控 / 网元故障 / 关键样本 / 🔍关键发现
- **每日统计**: 超过1天数据自动按天汇总行数/ERROR/LIID/ZTLIG1额外含设控/停控/连接失败/链路ERR/无响应
- 导出: 仅 Markdown 格式, 文件名=`{原始文件名去后缀}-分析报告-{YYYYMMDD-HHMMSS}.md`
- 前端自适应: ZTLIG1显示独有章节, 其他类型显示对应指标
- SSF报告: SIP方法占比列 / 活跃LIID分析 / 401认证拒绝率检测
- 左栏「解析摘要」按命令分组（不渲染逐行）

### extract_key_info None key
- 场景: ASN.1解码结果中含None key
- 修复: `if k is None or (isinstance(k, str) and k.startswith('_')): continue`

### PCAP 端口过滤脚本 (dpkt)
当需要输出过滤后的PCAP文件时:
```python
import dpkt
def filter_pcap_by_port(in_path, out_path, target_port):
    with open(in_path, 'rb') as f:
        reader = dpkt.pcap.Reader(f)
        writer = dpkt.pcap.Writer(open(out_path, 'wb'))
        for ts, buf in reader:
            eth = dpkt.ethernet.Ethernet(buf)
            if not isinstance(eth.data, dpkt.ip.IP): continue
            ip = eth.data
            if not isinstance(ip.data, dpkt.tcp.TCP): continue
            tcp = ip.data
            if tcp.sport == target_port or tcp.dport == target_port:
                writer.writepkt(buf, ts)
```
效果: 7.6MB→96KB(压缩98.8%)，上传解码从34,047包降至61包。
