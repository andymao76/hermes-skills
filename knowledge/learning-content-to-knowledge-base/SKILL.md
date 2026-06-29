---
name: learning-content-to-knowledge-base
title: 学习内容入库工作流
description: 用户分享学习材料（技术文档、规范、教程、报文等）时，解析、结构化摘要、逐段增量校对、最终写入知识库的标准化工作流。涵盖首次解析、入库创建、增量 patch 更新三个阶段。
category: knowledge
tags:
  - learning
  - knowledge-base
  - documentation
  - vendor-docs
  - bilingual
---

# 学习内容入库工作流

用户分享学习材料时，将其解析、结构化并写入知识库的标准化工作流。支持逐段增量校对模式（shared-edit-correction pattern）。

## 变体 A：用户分享内容入库（默认）

用户发送「学习 [topic]」+ 原始内容 → 结构化摘要 → 写入知识库（见下方三阶段工作流）。

## 变体 B：从已知文件路径提取知识点

当用户提供一个已知文件路径（如 `/tmp/some-book.txt`），要求从特定章节提取知识时，使用以下模式：

### 步骤

1. **定位结构标记**：使用 `search_files(context=1, output_mode=content)` 搜索章节标题模式（如 `Chapter 1[2]`、`\fChapter` 等）
2. **确定章节边界**：搜索目标章节的起始位置，同时搜索相邻下一章节的起始位置，确定完整范围
3. **分块读取**：按章节边界使用 `read_file(offset=X, limit=Y)` 分块读取。大文件单次读取会被截断（>100K 字符），需逐步翻页
4. **持续翻页**：当输出显示 `"truncated": true` 且有 `"Use offset=Z to continue reading"` 提示时，继续读取后续内容
5. **合成输出**：将各章节内容整合为结构化 Markdown，含实用速查表、对比表、编码公式等

### 注意

- 大型文本文件（如 1MB+ 的教材）每次 read_file 最多返回 ~1000 行。需多次读取才能覆盖完整章节
- 文件内可能含 `\f`（分页符），搜索时注意转义或使用宽松模式
- 教材的章节标题格式可能不统一，搜索时可用多个模式备选

## 触发条件

用户消息以「学习 [topic]」开头，并附带了文档/规范/报文/对比表等原始内容或目录路径。

## 前置工具检查

### 中文编码处理

用户分享的学习材料可能是 GBK/GB2312 编码的 `.txt` 文件或旧版 `.doc` 格式。在读取前先检测：

```bash
# 检查编码
file -bi file.txt          # 检查 MIME 类型和 charset
enca -L zh file.txt        # 检测中文编码（需安装 enca）

# 转码 GBK → UTF-8
iconv -f gbk -t utf-8 file.txt 2>/dev/null

# 提取旧版 .doc 内容
# 方式 A：catdoc（轻量，速度快）
catdoc file.doc 2>/dev/null
# 方式 B：libreoffice（可靠，支持 WPS .doc）
libreoffice --headless --convert-to txt:"Text" file.doc --outdir /tmp/
# 方式 C：antiword（备选）
antiword file.doc 2>/dev/null
```

`.doc` 文件的 magic bytes `d0cf11e0`（OLE2 格式）表明是旧版 Word 文档。python-docx 无法读取此类文件（它只支持 .docx）。LibreOffice 的 `--headless --convert-to txt` 是最可靠的提取方式，包括 WPS Office 创建的 .doc 文件（KSOProductBuildVer 标记）——提取时需注意 LibreOffice 可能报告 Java 依赖缺失警告（`failed to launch javaldx`），这不影响文本提取。提取后文件编码可能是 UTF-8，也可能需要后续 `iconv` 转码。

### 旧版 .doc 格式识别

用 python 检测文件格式：
```python
with open('file.doc', 'rb') as f:
    magic = f.read(8)
    print(magic.hex())
# d0cf11e0a1b11ae1 = 旧版 .doc (OLE2 Compound Document)
# 504b0304 = .docx (ZIP-based OOXML)
```

## 企业编码规范的结构化处理

当学习材料是**企业编码规范**（如 Sinovatio C 语言规范）时，注意其层次结构：

```
主规范（完整版，1500+ 行，11 章）
├── 简易精简版（~18 条核心规则，新人入职先看）
├── 注释专项规范（8 节）
└── 子集专项规范（如 C99 嵌入式特性使用规范，19 条规则）
    ├── 合规示范代码（*.c，编译通过）
    ├── 违规示范代码（*.c，编译预期报错）
    ├── Makefile（一键验证）
    ├── 工程建议代码（array_utils.h/c, my_msg.h/c）
    ├── 对比附录（C89 vs C99、嵌入式 vs 非嵌入式）
    └── 配套 .docx 工程建议文档
```

入库策略：
- **主规范**单独入库，作为根节点
- **子集专项规范**独立入库，关联主规范（通过 wikilink）
- **简易版/专项规范**作为独立笔记或附录（视长度而定）
- **配套代码**统一放 `references/` 子目录

## 培训材料目录入库模式

当用户指向一个**目录**（如 `/home/andymao/Documents/C/`）而非单个文件时：

1. 列出目录全部文件类型（.txt, .doc, .ppt, .pdf）
2. 识别各文件角色：规范/培训PPT/测试题/学习指导/参考书
3. 建立课程体系关系图
4. 优先入库可提取文本的文件（.txt, .doc）；.ppt 和 .pdf 视工具能力备选
5. 在主笔记中添加整个课程体系的目录索引

典型培训材料目录结构（包含规范层级）：
```
Documents/C/
├── 主规范 .doc                    ← 优先入库（根文档）
├── 简易规范 .txt                  ← 次要入库（子集，作为独立笔记 + 关联主规范）
├── 注释规范 .txt                  ← 次要入库（作为独立笔记 + 关联主规范）
├── 学习指导 .txt                  ← 记录于笔记元数据
├── 过关思考题 .doc                ← 视需要提取
├── 第1~6章培训PPT                 ← 有工具可提取时处理
├── GDB使用.ppt                    ← 有工具可提取时处理
└── C Primer Plus 教材.pdf        ← 标注为参考书来源
```

**主规范与子规范的层级关系处理**：当目录中包含一个主规范（如 1509 行、11 章的完整 C 语言编码规范）和多个子规范（如 C99 嵌入式专项规范、简易 18 条版、注释专项）时，入库策略如下：

1. **主规范单独一篇笔记**，作为根节点，存到知识库对应的分类目录（如 `program-info/编程规范/`）。包含完整的前言、原则、分类目录
2. **每个子规范独立一篇笔记**，通过 `frontmatter` 中的 `links:` 或正文末尾的 `关联知识` 章节添加 `[[]]` wikilink 指向主规范
3. **简易指南和学习指导**也作为独立笔记，侧重"快速入门"定位
4. **`_index.md` 作为目录索引**，用表格组织所有相关文档，标注每篇的角色（"主规范"、"特性专项"、"新人入门"、"注释专项"等）
5. 父目录的 `_index.md`（如 `program-info/_index.md`）同时更新文件计数，保持最外层导航准确

## 编译验证扩展

### 编译器强制检测标志组合

针对嵌入式 C89 严格模式，可以组合使用多个标志进行完整兼容性检查：

```bash
# 完整嵌入式 C89 兼容性基线
gcc -Wall -Werror=vla -Wdeclaration-after-statement \
    -Wtraditional -Wnested-externs -pedantic -std=c89 \
    -o test test.c
```

### 三模式对比验证表

对于同一组代码文件，在三个编译模式下对比编译结果，写入笔记可形成清晰的对比表：

```markdown
| 特性 | -std=c89 | -std=gnu89 | -std=c99 |
|------|----------|------------|----------|
| /* 块注释 */ | 通过 | 通过 | 通过 |
| // 单行注释 | ✗错误 | 通过 | 通过 |
| VLA | ✗错误 | 通过 | 通过 |
| static inline | ✗错误 | 通过 | 通过 |
| snprintf | ✗错误 | 多数通过 | 通过 |
```

## 工作流程

### 第 1 阶段：接收与解析

1. 用户发送「学习 [topic]」+ 原始内容
2. 首次回复：立即确认已收到，并提供结构化摘要（表格/列表/逐字节解析）
3. 摘要完成后，主动询问是否写入知识库

### 第 2 阶段：入库（用户确认后）

#### 2.1 定位存放位置

1. **探查知识库结构** — 先浏览目标目录树（`mcp_filesystem_directory_tree`），了解同类文档的组织方式
2. **搜索已有相关文件** — 用 `search_files(target="files")` 查找同主题已有文件，避免重复创建
3. **阅读重叠文件** — 对有重叠内容嫌疑的已有文件，用 `read_file` 快速浏览前几行和关键章节，确认内容互补性而非冗余
4. **确定目录** — 根据探查结果选择合适的目录层级

#### 2.2 创建笔记

1. 创建 Markdown 文件，包含 YAML frontmatter、结构化内容、双语并存
2. 使用 SOP 风格格式化（当内容为部署/配置/运维经验类文档时优先采用）：
   - 顶栏卡片元数据（版本、适用环境、关联文档）
   - 目录（TOC）
   - 分节编号标题
   - 表格对比（问题/原因/修复三列）
   - 配置代码块
   - 验证清单
3. 写入适当目录：`~/knowledge/hi2/厂商对接/`、`~/knowledge/telecom/lawful_interception/`、`~/knowledge/ops/` 等

#### 2.3 建立双向交叉链接

1. 在新建文件的 frontmatter 或顶栏中通过 `关联文档: [[existing-doc|显示名称]]` 指向相关已有文件
2. **更新已有文件** — 在相关已有文件的元数据区添加回链，确保双向链接：新文档 → 旧文档 / 旧文档 → 新文档
3. 更新已有文件的 `最后更新` 日期
4. 尝试 enzyme refresh

### 第 3 阶段：增量校对

用户可能逐段分享 Description → Syntax → Arguments → Status → Output → Examples，需逐段更新：

1. patch 前先 read_file 确认上下文，避免多处匹配
2. 保留原文措辞，不简化为替代描述
3. 用户逐字键入时耐心等待完整内容

## 输出格式

- 参数表：`| 参数 | M/O | 说明 |`（英文原文 + 中文）
- 元数据：来源、入库时间、分类、数据级别

## 注意事项

- patch 冲突时，用节标题 + 相邻行唯一上下文定位
- 标准接口文档标记 LEVEL 3

### 变体 D：正式设计文档入库

当用户直接粘贴完整的**正式技术文档**（详细设计、概要设计、需求规格说明书等）到聊天中要求"学习"时，使用本变体。

### 识别信号

- 用户消息中包含完整的文档封面/标题页（`技术文件名称`、`文件编号`、`版本`、`拟制/审核`）
- 包含正式目录（`目 录` + 章节编号）
- 包含完整的术语表、数据结构定义、接口说明
- 用户消息较长且结构完整，非碎片化

### 工作流

```
1. 文档类型识别
   ├── 详细设计文档 → 核心产出：数据架构 + 状态机 + 接口定义
   ├── 概要设计文档 → 核心产出：系统架构 + 模块划分 + 数据流
   └── 需求规格文档 → 核心产出：功能列表 + 用例 + 约束条件

2. 分层提取
   ├── 第1层：元数据（系统名称 + 版本 + 模块名 + 所属产品线）
   ├── 第2层：架构与数据流（模块位置图 + 输入/输出 + 上下游依赖）
   ├── 第3层：核心数据结构（C struct / 类定义 + 字段说明 + 枚举值）
   ├── 第4层：设计决策（约定 + 限制 + 边界条件 + 异常处理策略）
   ├── 第5层：接口与函数（入口函数 + 回调 + 返回值定义 + 参数说明）
   └── 第6层：配置项（配置文件格式 + 初始化参数 + 默认值）

3. 结构化入库
   ├── 创建笔记到 `01_PROJECTS/<Project>/`
   ├── YAML frontmatter 含 tags/aliases/created
   ├── 正文按 系统定位 → 核心数据结构 → 设计决策 → 处理流程 → 接口说明 → 参考资料 组织
   └── 数据结构定义保留 C/Python 等代码块格式，字段加注释说明

4. 索引更新
   └── enzyme refresh / kb-index
```

### 注意

- **嵌入式图形数据**：文档中可能包含 draw.io / ProcessOn 等工具的 mxGraph XML/URL 编码数据（`%3CmxGraphModel%3E` 等），这些是 SVG 渲染的中间格式，**不需要解析**，直接丢弃
- **C 结构体格式保留**：正式设计文档中的 C struct 定义是核心资产。保留代码块格式，在字段后加注释说明其作用。用 Markdown 表格形式同时呈现字段名/类型/说明
- **枚举和宏定义**：`#define` 和 `enum` 是文档的配置结论，提取到 `### 配置参数` 或 `### 关键定义` 章节
- **状态机**：跨包状态机（两级/三级状态迁移图）用 ASCII 图或缩进列表模拟，不用画正式流程图
- **返回值速查表**：函数返回值（如 `H2_AGAIN` / `H2_DONE` / `H2_OK`）编为速查表，标注每个值的触发条件
- **目录中无关章节**：设计文档模板中的"修改记录"页面（拟制人/版本号/更改理由）通常为空，无需处理

### 设计文档入库模板

```markdown
---
title: <项目名> V<版本> <模块名> <文档类型>
tags: [<项目>, <技术域>, <模块>]
created: YYYY-MM-DD
aliases: [<项目名>, <模块名>]
---

# <项目名> <模块名> <文档类型>

## 系统定位

[模块在系统中的位置，简要说明输入/输出和上下游依赖]

## 核心数据结构

### [结构体名称]

```c
// 保留原始 C/Python 定义
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `field1` | uint32_t | 字段作用 |

## 关键设计决策

| 决策 | 选择 | 原因 |
|------|------|------|
| [决策项] | [选择方案] | [技术原因] |

## 处理流程

[用 ASCII 流程图或缩进列表描述]

## 接口说明

[入口函数 + 参数 + 返回值]

## 参考资料

- [RFC/规范编号]
- [设计文档名称]
```

### 变体 F：铁律入库（Iron Rule Ingestion）

当用户说「学习 [path] 作为铁律」或「作为铁律，学习 [path]」时，内容不仅仅是知识沉淀——它是**行为约束规则**，需要同时写入 Memory（确保每轮都加载）和知识库（完整参考）。

#### 与普通学习变体的关键区别

| 维度 | 普通学习 | 铁律学习 |
|------|---------|---------|
| 行为约束力 | 参考知识 | **必须遵守，不可变更** |
| 存储目标 | 知识库 | Memory + 知识库（双写） |
| Memory 内容 | 不写 | 浓缩核心规则（1-3 行） |
| KB 内容 | 结构化摘要 | 完整原文 + 格式化表格 + 分类元数据 |

#### 执行流程

1. **读取源文件** → `read_file` 获取完整内容
2. **提取铁律 essence** → 从文档中提炼最核心的规则摘要（1-3 句），聚焦"谁做什么"的分配关系，去掉背景描述和架构图等细节
3. **Memory 批量写入** → 用 `memory(action='operations', target='memory')` 批处理：
   - 先清理旧的、被取代的 memory 条目（`remove`）
   - 缩短 verbose 条目（`replace`）释放空间
   - 添加铁律条目，确保总字符数 ≤ 2200
   - 铁律格式：`【铁律】<规则名> <版本>: <核心分配表>; <禁止项/特殊约束>`
4. **知识库写入** → 创建完整 Markdown 文件到对应 KB 目录：
   - frontmatter 含 `tags: [铁律, <分类>]` 和 `aliases`
   - 用表格呈现模型/场景分配关系（比散列表格更可读）
   - 保留完整的架构图（ASCII/文本）
   - 保留 Fallback 链、禁止项等细节
   - 在末尾加 `关联笔记` wikilinks 和标签
5. **验证** → 确认 Memory 写入成功 + KB 文件存在

#### 注意

- Memory 空间紧张（`~/.hermes/memory` 约 2200 char 上限），铁律必须先移除旧/冗余条目再写入
- 知识库文件放在分类目录下（如 `knowledge/hermes/`），不要放根目录
- 铁律在 Memory 中要足够简洁，让助手每次对话都能看到并遵守；完整内容在知识库中提供参考

### 变体 E：PCAP 信令抓包文件入库

当用户分享 **PCAP 抓包文件** 并要求「学习」时，使用本变体。PCAP 文件含原始信令数据，需先用 scapy 或 tshark 分析提取结构化信息，再写入知识库。

> 配套参考：该变体的完整分析示例如 `knowledge/telecom/pcap-analysis/` 目录下的 PCAP 分析笔记，以及 `knowledge/telecom/pcap-analysis/tshark-command-reference.md`（tshark CLI 命令速查手册）。

> **SOP/部署经验文档入库**的可复用示例详见本 skill 的 `references/sop-deployment-experience-example.md`。

### 识别信号

- 用户消息包含 `pcap` / `pcapng` 文件路径
- 文件名含协议缩写（NGAP、S1AP、GTP、SIP、Diameter 等）
- 用户说「学习 [文件名]」或「分析这份抓包」

### 前置条件

优先使用 tshark（更快、协议层支持完整），退而用 scapy：

```bash
# 首选：tshark（需安装）
tshark -r file.pcap -z io,phs -q        # 协议层次统计（最优先）
tshark -r file.pcap -z conv,ip -q        # IP 会话统计
tshark -r file.pcap -z conv,tcp -q       # TCP 会话统计
tshark -r file.pcap -T fields -e frame.number -e ip.src -e ip.dst  # 批量字段提取

# 备选：scapy（无需安装 tshark）
python3 -c "from scapy.all import *"
```

### 工作流

```
1. 文件探查
   ├── file 命令检查 pcap 格式 + 时间戳精度
   ├── stat 检查文件大小（大文件需分块或采样）
   └── 判断协议类型（SCTP? TCP? UDP? 端口号？）

2. 协议层级分析（最优先）
   ├── tshark -z io,phs -q（首选）或 scapy 按 IP proto 计数
   ├── 识别主导协议（SCTP? HTTP? SIP? GTP?）
   ├── 识别关键端口（38412=NGAP, 36412=S1AP, 5060=SIP 等）
   └── 输出：协议分布表格 + 各协议包数占比

3. 网络拓扑重构
   ├── IP 对统计（tshark conv 或 scapy Counter）
   ├── 识别中心节点（包量最大的 IP = AMF/MME/SBC 等）
   ├── 识别边缘节点（包量较小的 IP = gNB/eNB/UE 侧）
   └── 输出：IP ↔ 角色映射表 + Top N 活跃节点

4. 深入协议分析
   ├── SCTP 会话：源/目的端口分布（多路关联识别）
   ├── NGAP/S1AP：提取 ProcedureCode + PDU 类型分布
   │   └── scapy 解析 SCTP DATA chunk → PPID=60(NGAP) → 首字节判定
   ├── SIP：方法 / 状态码计数
   ├── Diameter：cmd.code 分布
   ├── HTTP2：stream_id 分布
   └── 输出：ProcedureCode 排名表 + PDU 类型统计

5. 信令特征归纳
   ├── 主导流程（什么消息最多？）→ 注册/切换/会话管理？
   ├── 异常比例（failure / error 占比）
   ├── 时间跨度（整个抓包覆盖多长窗口）
   └── 输出：信令流程特征文字描述

6. 结构化入库
   ├── 写入 knowledge/telecom/pcap-analysis/（电信协议）
   │   或 knowledge/01_PROJECTS/<项目>/（项目专用）
   ├── YAML frontmatter 含 tags/aliases/created
   ├── 正文结构：文件信息 → 网络拓扑 → 协议分析 → 信令特征 → 关联项目
   ├── 关联现有知识（[[wikilink]] 指向已有笔记）
   └── enzyme refresh / kb-index
```

### PCAP 笔记模板

```markdown
---
title: <运营商> <网络制式> <接口> <协议> PCAP 分析
tags: [5GC, NGAP, S1AP, PCAP分析, 信令, <运营商>]
created: YYYY-MM-DD
aliases: [<文件名>, <网络/协议描述>]
---

# <标题>

## 文件信息

| 文件名 | 大小 | 包数 | 协议分布 | 时间跨度 |
|--------|------|------|----------|----------|

数据来源：[说明分析工具]

## 网络拓扑

### 运营商识别

- IP 段分析 + 归属地判断
- 核心网元 IP ↔ 角色映射表

### 接入网节点

| IP | 包量 | 角色 |
|----|------|------|

## 协议分析

### 协议层次分布

[tshark io,phs 或 scapy 统计]

### 关键过程码分布

| 代码 | 名称 | 数量 | 含义 |
|------|------|------|------|

### PDU 类型分布

[initiating / successful / failure 比例]

## 信令特征

[流程描述 + 发现的规律/异常]

## 关联知识

- [[相关笔记1]]
- [[相关笔记2]]
```

### 常用抓包分析代码片段

```python
# === IP 协议分布 ===
from scapy.all import rdpcap, IP
from collections import Counter
pkts = rdpcap("file.pcap")
proto_counter = Counter()
for p in pkts:
    if IP in p:
        proto_counter[p[IP].proto] += 1
proto_map = {6:'TCP', 17:'UDP', 132:'SCTP', 1:'ICMP'}
for pnum, cnt in proto_counter.most_common():
    print(f"  {proto_map.get(pnum, 'proto-'+str(pnum))}: {cnt}")

# === IP 对 Top N ===
ip_pairs = Counter()
for p in pkts:
    if IP in p:
        ip_pairs[(p[IP].src, p[IP].dst)] += 1
for (src, dst), cnt in ip_pairs.most_common(10):
    print(f"  {src:20s} -> {dst:20s}  [{cnt:5d}]")

# === SCTP DATA chunk 提取（NGAP/S1AP PPID=60/18）===
import struct
for p in pkts:
    if IP not in p or p[IP].proto != 132:
        continue
    raw = bytes(p[IP].payload)
    offset = 12
    while offset + 8 <= len(raw):
        chunk_type = raw[offset]
        chunk_len = ((raw[offset+2] << 8) | raw[offset+3])
        if chunk_len < 4 or offset + chunk_len > len(raw):
            break
        if chunk_type == 0:  # DATA
            ppid = struct.unpack('>I', raw[offset+4+8:offset+4+12])[0]
            data_start = offset + 4 + 12
            data_len = chunk_len - 16
            if data_len > 0 and ppid == 60:  # NGAP
                ngap_msgs.append(raw[data_start:data_start+data_len])
        offset += chunk_len

# === NGAP ProcedureCode 提取 ===
ngap_procs = {0:"AMFConfigurationUpdate", 14:"HandoverPreparation", ...}
for payload in ngap_msgs:
    if len(payload) >= 2:
        pdu_choice = payload[0] >> 6
        pc = payload[1]
        proc_codes[ngap_procs.get(pc, f'proc_{pc}')] += 1
```

### 对应协议 PPID 速查

| 协议 | PPID (十进制) | SCTP 标准端口 |
|------|---------------|---------------|
| NGAP (5G N2) | 60 | 38412 |
| S1AP (LTE S1-MME) | 18 | 36412 |
| XnAP (5G Xn) | 61 | 38422 |
| X2AP (LTE X2) | 27 | 36422 |
| HNBAP | 24 | — |

## 变体 C：内容已存在，仅交叉链接

当用户分享的学习材料在知识库中已有完整记录时：

1. **确认覆盖** — 快速搜索 KB 确认已有文件覆盖了用户分享的全部知识点
2. **系统对比** — 对来源内容与已有知识进行逐项对比，列出「已覆盖」和「新发现」清单。新发现可能包括：
   - 现有知识中缺失的细节（XSD 格式约束、DTD 引用、版本注释等）
   - 更深入的示例数据（Base64 解码完整内容、错误码细节等）
   - 元信息（开发工具、作者、项目背景）
3. **补充交叉链接** — 在已有文件的 frontmatter 中添加 `links:` 指向配套资料，在相关手册中添加回链。确保双向链接：实践文档 → 协议字典 / 协议字典 → 实践文档
4. **增量更新已有文件** — 将「新发现」的内容通过 `patch` 添加到已有文件的对应章节
5. **仅做链接和补缺** — 不重复写入已有内容，不创建新文件
6. **记录更新版本** — 在已有文件的 frontmatter 中添加 `updated:` 字段（含版本说明）

对比结果输出格式：
```
| # | 知识点 | 来源文件 | 状态 |
|:-:|:-------|:--------|:----:|
| 1 | 已有内容 | KB 文件 | ✅ 已覆盖 |
| 2 | 新发现 | 来源文件 | ⬆️ 待补充 |
```

## 配套代码文件处理

当学习内容包含可编译的代码示例（`.c`、`.py`、`.sh` 等源文件）时：

### 1. 编译验证

在入库前对代码文件进行编译/语法检查，确保其可运行：

```bash
# C 代码 — 用 -std=c89 验证兼容性（嵌入式标准）
gcc -Wall -std=c89 file.c -o /tmp/test && /tmp/test

# 如需 C99 特性（如 complex.h），用 -std=c99 或 -std=gnu89
gcc -Wall -std=c99 file.c -o /tmp/test -lm && /tmp/test

# 三模式对比验证（嵌入式编码规范常见需求）
for mode in c89 gnu89 c99; do
  gcc -Wall -std=$mode file.c -o /tmp/test 2>&1 && echo "$mode: PASS" || echo "$mode: FAIL"
done
```

##### 编译器强制检测标志

针对特定 C99 违规特性，使用编译器标志将其从警告提升为编译错误：

| 标志 | 检测目标 | 对应规则 |
|------|---------|----------|
| `-Wvla` | VLA 使用警告 | 规则 2 |
| `-Werror=vla` | 将 VLA 警告提升为错误，禁止编译 | 规则 2 |
| `-Wdeclaration-after-statement` | 混合声明与代码（C89 下默认报错，C99 下可选） | 规则 17 |
| `-pedantic -std=c89` | 完整 C89 标准兼容性检查 | 全规则基线 |
| `-Wtraditional` | C89/K&R 与传统 C 特性差异警告 | 全规则 |
| `-Wnested-externs` | 嵌套 extern 声明 | MISRA 相关 |

组合使用示例（嵌入式 C89 严格模式）：
```bash
gcc -Wall -Werror=vla -Wdeclaration-after-statement -Wtraditional -pedantic -std=c89 -o test test.c
```

记录编译结果（错误数、警告数）并在后续笔记中标注。对已知违规示例（如 `rule_violations.c`），编译验证的价值在于精准展示每条规则被哪些编译错误拦截。

### 2. 合规/违规成对文件的教学模式

当学习材料包含**成对**的源代码文件（一个合规、一个违规）时，这是高效的嵌入式编码规范教学方法：

- **合规文件**（如 `*_compliance.c`）— 展示正确写法，应能编译通过并正确运行
- **违规文件**（如 `*_violations.c`）— 故意引入禁用特性，编译报错展示每条规则为何存在
- 编译验证时分别用 `-std=c89`（违规文件预期报错，用 `|| true` 不阻断 make）和 `-std=gnu89`（合规文件预期通过）
- 这种成对文件适合用于代码审查培训、新人 onboarding

对于多个相关文件，创建 **Makefile** 实现一键验证：

```makefile
CC      := gcc
CFLAGS  := -Wall
LDLIBS  := -lm

all: compliance violations

compliance: TestCompliance
TestCompliance: compliance.c
	$(CC) $(CFLAGS) -std=gnu89 $< -o $@ $(LDLIBS)
	./$@

violations: TestViolations
TestViolations: violations.c
	-$(CC) $(CFLAGS) -std=c89 $< -o $@ $(LDLIBS) 2>&1 || true
	@echo "==> 预期：N 个编译错误"

clean:
	rm -f TestCompliance TestViolations
```

Makefile 中 violations 目标用 `-` 前缀和 `|| true` 确保编译报错不中断 `make`。

#### 4.1. `array_destroy` cleanup 函数的常见错误与修复

`__attribute__((cleanup))` 是一个方便的自动释放机制，但实现时需要区分一维和二维数组：

**常见错误**：用一个 `array_destroy(void *p)` 同时处理 1D 和 2D，在函数中用 `*ptr` 区分数据块是否已分配：

```c
/* 错误实现 — 对 1D 数组有数据时崩溃 */
void array_destroy(void *p) {
    void **ptr = *(void ***)p;
    if (ptr && *ptr) {
        free(*ptr);   /* 1D 数组元素非 0 时，*ptr 不是指针，crash! */
    }
    free(ptr);
}
```

**正确方案**：用两个单独的 cleanup 函数，通过不同的宏（`array_autofree` vs `array_autofree_2d`）区分：

```c
/* 1D — 直接 free 指针本体 */
static inline void array_free_1d(void *p) {
    free(*(void **)p);
}

/* 2D — 先释放行指针[0]指向的连续数据块，再释放行指针数组 */
static inline void array_free_2d(void *p) {
    void **row_ptrs = *(void ***)p;
    if (row_ptrs) {
        free(row_ptrs[0]);  /* 连续数据块 */
        free(row_ptrs);     /* 行指针数组 */
    }
}

#define array_autofree   __attribute__((cleanup(array_free_1d)))
#define array_autofree_2d __attribute__((cleanup(array_free_2d)))
```

关键区分：`array_autofree` 用于 `array_create(type, n)` 返回的 1D 指针；`array_autofree_2d` 用于 `array_create_2d(type, r, c)` 返回的 2D 指针。两者不可混用。

对于需要验证内存安全的代码（如 array_create 封装），在 Makefile 中添加 ASan 调试目标：

```makefile
# ASan 调试构建
asan: TestAsan
TestAsan: test.c
	$(CC) -g -fsanitize=address $(CFLAGS) -std=c99 $^ -o $@
	./$@
```

### 3. 补充工程建议代码（规则实现示例）

当学习内容是**编码规范**时，除了验证配套代码文件外，还需为禁用规则提供**工程建议代码**——即安全的替代实现：

- 规则禁止 VLA → 提供 `array_create` 封装（类型安全 + calloc + 文件名/行号调试 + array_autofree）
- 规则限制 FAM → 提供 `_msg_create` / `_msg_destroy` 工厂函数封装
- 规则禁止 sprintf → 提供 `snprintf` 返回值检查模板

工程建议代码文件命名建议：
```
array_utils.h        # 头文件：宏定义 + inline cleanup 函数
array_utils.c        # 实现：calloc + 调试信息 + 2D支持
my_msg.h             # FAM 结构体 + create/destroy 声明
my_msg.c             # 工厂函数实现
test_array.c         # 一维/二维使用示例
test_msg.c           # 消息使用示例
```

将这些实现文件保存到 `references/` 目录，并在主笔记中添加引用行。如果规范文档的工程建议部分原本指向外部文档（如《规则2规则3工程建议2.docx》），现在补充了代码实现，应在引用表中标注。

### 4. 创建交叉引用附录

当学习内容与已有知识有明显对比关系时（如 C89 vs C99、嵌入式 vs 非嵌入式），主动创建**对比附录**追加到主笔记末尾（在配套参考文件之前）：

```markdown
## 嵌入式 vs 非嵌入式对比

同样的 C99 特性，在嵌入式环境与非嵌入式中的处理规则不同。
下表对比展示了 19 条规则在两种场景下的差异及原因。

| 规则 | 特性 | 嵌入式 | 非嵌入式 | 原因说明 |
|------|------|--------|---------|----------|
| 1 | // 注释 | 禁用 | 可用 | C99+ 编译器普遍支持 |
```

对比表应有明确的列头说明上下文，并在表下加注「企业具体规则以正式规范文本为准」。

### 5. 保存为配套引用文件

源文件保存到知识库中与主笔记 **同目录下一级 `references/` 子目录**中（比平铺存放更整洁，便于多个附件的组织）：

```
knowledge/program-info/编程规范/
├── 中新赛克C99嵌入式开发规范.md   # 主笔记
├── _index.md                      # 目录索引
└── references/
    ├── kw_c99rule_compliance.c
    ├── kw_c99rule_violations.c
    ├── kw_complex_calc.c
    └── Makefile                   # 可选：一键编译验证
```

为什么用 `references/` 子目录：主笔记目录下可能有大量不同种类文件，子目录分类可避免平铺混乱。特别是当同目录下还有 `_index.md` 和其他同类笔记时。

### 6. 在主笔记中添加文件引用

在主笔记的末尾或 `关联知识` 章节添加指向源文件的引用表格：

```markdown
## 配套参考文件

| 文件 | 说明 | 编译验证 |
|------|------|----------|
| `references/Makefile` | 一键验证，`make [compliance|violations|all]` | `make all` |
| `references/compliance.c` | 合规写法示例 | `gcc -std=gnu89 ... -lm` 通过 |
| `references/violations.c` | 违规示例，C89 报错 | `gcc -std=c89 ...` 预期失败 |
```

## 索引表更新与重定向模式

### 更新父目录 _index.md

当在已有分类目录下新增笔记时，同步更新该目录的 `_index.md`（若有）以维护目录索引的可发现性。

使用 `mcp_filesystem_edit_file` 在索引表中插入新行，保持表格格式一致。行序建议按重要性或字母序。

### 创建旧路径重定向

当知识库笔记从旧位置迁移到新位置时（如 `~/knowledge/编程规范/` → `~/knowledge/program-info/编程规范/`），在旧路径创建重定向笔记：

```markdown
> **此文档已迁移至 [[program-info/编程规范/中新赛克C99嵌入式开发规范]]**
>
> 新路径: `~/knowledge/program-info/编程规范/中新赛克C99嵌入式开发规范.md`
```

确保重定向中包含 `[[wikilink]]` 和目标文件的绝对路径，方便 Obsidian 图谱跳转。两条信息都提供是因为 Obsidian 图谱用 wikilink 可视跳转，而 kb-search 用绝对路径直接读取。

## Patch 操作进阶技巧

### 1. 唯一上下文匹配策略

当同一知识库笔记包含多个相同结构（如多个命令的状态码表都有 `| 0 | 成功 |`），`patch` 会报 `Found N matches` 错误。解决方法：

- 使用该状态码表所在章节的完整头作为上下文前缀，例如：
  ```
  #### 状态码\n\n| 码 | 含义 |
  ```
  而不是只匹配表内行。

### 2. Patch 意外吞噬章节标题的恢复

当 patch 的 `old_string` 过于宽泛时，可能意外替换掉相邻章节的标题行（例如 `#### lealist — 显示 LEA` 被吞掉变成裸文本）。恢复步骤：

1. 立即用 `read_file` 查看受影响区域
2. 找到丢失的标题出现的精确位置和周围文本
3. 用一个新的 patch（old_string 为被吞标题下方的文本，new_string 为重新插入的标题 + 该文本）修复
4. 只修复丢失的局部，不要尝试整体重构

典型场景：在一个 `### 7.9` 段落之后插入内容，patch 的 old_string 无意中匹配到 `### 7.8` 或 `### 8.0` 的标题行。

### 3. 长会话中 read_file 警告的处理

经过多次 patch 后，文件写入时可能提示：
```
was last read with offset/limit pagination (partial view). Re-read the whole file before overwriting it.
```

这只是一个警告，patch 仍然生效。在后续 patch 前用 `read_file path=... offset=1 limit=1000` 刷新文件缓存即可消除警告。

### 4. 结构修复后的后续操作

如果因为前面的 patch 不慎导致部分内容错位（如参数表或状态码表被截断），不要尝试用单个大 patch 一次修复。应：

1. 用 `read_file` 确认受影响的具体范围
2. 用多个小 patch 逐个修复，每次只修复一个小块
3. 修复完成后用 `read_file` 整体验证结构正确
