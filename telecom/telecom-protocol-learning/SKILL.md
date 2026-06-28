---
name: telecom-protocol-learning
description: 电信协议学习与知识库归档工作流 — PCAP分析/ASN.1规范/技术文档学习后，结构化入库到knowledge/telecom/，补充worklog+日报
triggers:
  - 学习PCAP文件/协议规范
  - 分析信令抓包
  - 解压学习文档(zip/chm)
  - 学习协议ASN.1定义
  - 学习命令行工具手册
  - 搜索5GC/3GPP技术资料
  - 研究OpenAPI/正则模式
tags: [telecom, pcap, learning, kb-archiving, 5GC]
---

# 电信协议学习与知识库归档工作流

## 流程概述

```
源材料 → 分析/学习 → 结构化Markdown → KB入库 → 刷新语义索引 → worklog → 日报
```

适用场景：学习 PCAP 抓包文件、ASN.1 协议规范、技术文档、工具手册等，将知识沉淀到本地知识库。

---

## 阶段一：源材料接收

### 源材料类型

| 类型 | 示例 | 分析工具 |
|------|------|----------|
| PCAP抓包 | `*.pcap` / `*.pcapng` | Scapy / tshark |
| 技术文档 | `.docx` / `.chm` / `.zip` / `.pdf` | 7z解压 / libreoffice / pandoc |
| ASN.1规范 | `.asn1` / `.txt` | 阅读+归纳 |
| 命令手册 | man page / help输出 | 整理结构化速查表 |
| 在线搜索 | GitHub / Google / 3GPP规范 | web_search_plus / web_extract_plus |
| OpenAPI规范 | `.yaml` / `.json` | 提取正则pattern / 服务URI结构 |

### 处理方式（补充）

- **在线搜索**：先用 `web_search_plus` 搜索关键技术点，再用 `web_extract_plus` 提取实际源码/规范文件
- **OpenAPI YAML**：直接从 3GPP Forge 或 GitHub raw 源下载，提取 `pattern:` 字段和 URI 模板
- **开源项目源码**：从 GitHub raw 源下载关键源码文件，保存到 `projects/STCS/references/free5gc/` 作为参考
- **GitHub 仓库浏览**：使用 browser 工具查看仓库目录结构找到正确的文件名（如 `nf_discovery.go` 而非 `discovery.go`），避免 404 错误
- **源码分类组织**：处理器代码放 `free5gc/`，API客户端放 `free5gc/nrf_api/`，模型定义放 `free5gc/models/`
- **源文件下载方式**：使用 `curl -sL --max-time 20 -o <file> <raw_url>` 下载，检查返回大小（14B=404错误）
- **报告发送**：学习完成后整理 TXT 报告发送到飞书个人 Bot 会话

### 处理方式

- PCAP：先用 `tshark -z io,phs -q` 快速看协议层次，再用 Scapy 深度分析
- CHM：`7z x file.chm` 解压后阅读 HTML
- 文档：解压后直接阅读关键章节

---

## 阶段二：分析/学习

### PCAP 分析必须覆盖的维度

1. **文件基本信息**：文件名、大小、包数、时间跨度
2. **网络拓扑**：
   - IP对分布、端口分布
   - 识别网元角色（AMF/SMF/gNB/MME/eNB 等）
   - 运营商识别（IP段→国家/运营商）
3. **协议分布**：各层协议（SCTP/UDP/TCP）、应用层协议（NGAP/S1AP/HTTP2 等）
4. **关键信令统计**：
   - ProcedureCode 分布（Top 20+）
   - PDU 类型分布（initiating/successfulOutcome/failure）
   - 关键数量特征
5. **信令特征分析**：主导流程、异常比例、网络行为解释

### 非PCAP材料学习要点

- 提取核心概念、数据结构、关键设计决策
- 对比分析（如 S1AP → NGAP 的协议演进）
- 与 STCS 项目的关联分析

---

## 阶段三：结构化 Markdown 入库

### 文件位置

```
knowledge/telecom/
  ├── pcap-analysis/           ← PCAP分析 + 工具手册 + 协议定义 + 正则模式
  │   ├── tshark-command-reference.md
  │   ├── tunisie-telecom-5g-ngap-n2-pcap-analysis.md
  │   ├── s1ap-asn1-ie-definitions.md
  │   ├── deelx-regex-library.md
  │   └── 5gc-regex-patterns.md       ← 5GC正则 + 3GPP OpenAPI pattern
  ├── ima-articles/            ← 已整理的5G/IMS技术文章
  ├── lawful_interception/     ← LI相关（本地）
  └── ...
knowledge/01_PROJECTS/STCS/   ← STCS项目专用
  └── stcs-v2-http2-submodule-design.md
```

### Markdown 模板要求

```markdown
---
title: <文章标题>
tags: [标签1, 标签2, ...]
created: <YYYY-MM-DD>
aliases: [别名1, 别名2]
---

# <标题>

## 关键信息

内容...

## 参考资料

- [[关联笔记1]] — 使用 wikilink 交叉引用
- [[关联笔记2]]
```

### 必须包含的内容

1. **Frontmatter**：`title`, `tags`, `created`, `aliases`
2. **结构化章节**：按逻辑分段（概述→核心内容→分析→关联）
3. **Wikilink**：使用 `[[关联笔记名]]` 建立双向链接
4. **数据来源标注**：说明数据来自文件/网络/Scapy分析等

---

### GitHub Raw URL 404 检测

```bash
# raw.githubusercontent.com 返回 14 字节 = 404（文件不存在/路径错误）
sz=$(curl -sL --max-time 10 -o /dev/null -w "%{size_download}" \
  "https://raw.githubusercontent.com/...")
if [ "$sz" -gt 50 ]; then echo "OK"; else echo "404"; fi

# 文件不存在时，用 browser 访问 GitHub 仓库确认正确路径
# 浏览 https://github.com/<org>/<repo>/tree/<branch>/<path>
# 或使用 File Finder: github.com/<org>/<repo>/find/<branch>
```

### 源码文件组织规范

下载开源项目参考源码时，统一按以下结构组织：

```
projects/STCS/references/
├── 3gpp-openapi/
│   └── TS29571_CommonData.yaml       # 3GPP OpenAPI 规范
└── free5gc/
    ├── access_token.go                # 处理器代码（顶层）
    ├── nf_management.go
    ├── nrf_api/                       # API 客户端代码
    │   ├── nrf_NFManagement_*.go
    │   ├── nrf_NFDiscovery_*.go
    │   └── nrf_AccessToken_*.go
    └── models/                        # 数据模型代码
        ├── model_nrf_nf_management_nf_profile.go
        └── model_nrf_*

curl -sL --max-time 20 -o <file> <raw_url>   # 单文件下载
```

---

## 阶段四：刷新语义索引

```bash
cd ~/knowledge && python3 ~/.local/bin/kb-index
```

确认新文件出现在 `[UPD]` 列表中。

---

## 阶段五：补充 worklog

### 日志格式

```
YYYYMMDD|项目名|Xh|工作内容描述（动词+对象+结果）
```

### 需要记录的内容

- 学习的文件名/协议名
- 分析的工具和方法
- 知识库入库路径
- 工时（按实际估算）

---

## 阶段六：生成日报

### 日报中知识库条目模板

```
  项目名 - 协议/工具学习（N项）
  ──────────────────────────────────────
  1  <学习内容1> → 入库: knowledge/.../xxx.md
  2  <学习内容2> → 入库: knowledge/.../yyy.md
```

### 日报 TXT 输出

- 放 `/tmp/日报-YYYY-MM-DD.txt`
- 格式：中文章节编号、===/--- 分隔线
- 含"今日完成"、"异常情况"、"明日计划"三个章节

---

## 常用工具命令速查

```bash
# tshark 快速看协议层次
tshark -r file.pcap -z io,phs -q

# 字段提取 CSV
tshark -r file.pcap -T fields -E separator=, -e frame.number -e ip.src -e ip.dst -e _ws.col.Protocol

# Scapy 统计 IP 对
python3 -c "
from scapy.all import rdpcap, IP
from collections import Counter
pkts = rdpcap('file.pcap')
pairs = Counter()
for p in pkts:
    if IP in p:
        pairs[(p[IP].src, p[IP].dst)] += 1
for (s,d),c in pairs.most_common(10): print(f'{s:20s} -> {d:20s} [{c}]')
"

# CHM 解压
7z x file.chm -o/tmp/extract/

# KB 索引更新
cd ~/knowledge && python3 ~/.local/bin/kb-index
```

---

## 阶段七：知识库备份到 GitHub

学习完成后，将新增的知识文件提交到 GitHub 仓库：

```bash
cd ~/knowledge
# 确认无涉密文件混入
git status --short | grep -iE "(li/|a1|ztlig|sinovatio|lawful)" && echo "WARNING: sensitive files!" || echo "clean"

# 提交
git add -A
git commit -m "知识库同步: <主要内容概述>"

# 推送（走代理）
HTTPS_PROXY=http://127.0.0.1:7897 git push origin main
```

### 提交规范

- commit message 格式：`知识库同步: <关键内容1>+<关键内容2>+...`
- 提交前用 git status 检查涉密文件
- 推送走 HTTP 代理 127.0.0.1:7897

---

## 阶段八：报告发送（可选）

学习完成后，可选择将汇总报告发送到飞书个人 Bot：

```python
import json, urllib.request

# 获取 token
token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
req = urllib.request.Request(token_url, json.dumps({"app_id": app_id, "app_secret": app_secret}).encode(),
    headers={"Content-Type": "application/json"})
resp = json.loads(urllib.request.urlopen(req).read())
token = resp["tenant_access_token"]

# 发送消息
send_url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id"
data = json.dumps({"receive_id": "ou_a74c0eb0ff0f216d5036c2300a213d22", "msg_type": "text",
    "content": json.dumps({"text": report_text})}).encode()
req2 = urllib.request.Request(send_url, data=data,
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
resp2 = json.loads(urllib.request.urlopen(req2).read())
```

- 用户 open_id: `ou_a74c0eb0ff0f216d5036c2300a213d22`
- Token 有效期 7200 秒
- 报告放 `/tmp/日报-YYYY-MM-DD.txt`

---

## 参考资料

- [[tshark-command-reference]] — TShark 命令参考
- [[deelx-regex-library]] — DEELX 正则库（用于 HTTP/2 Path 匹配）
- [[s1ap-asn1-ie-definitions]] — S1AP IE 定义
- [[tunisie-telecom-5g-ngap-n2-pcap-analysis]] — NGAP PCAP 分析范例
- [[5gc-regex-patterns]] — 5GC 正则模式与 3GPP OpenAPI 校验
- [[STCS V2.0 HTTP2 子模块详细设计]] — STCS 项目设计文档
