---
name: li-doc-ingestion
description: 将厂商LI技术文档/协议规范处理为结构化知识库条目的标准工作流。支持逐段增量更新，自动交叉链接。
category: telecom
---

# LI 文档知识库入库工作流

当用户发送 "学习" + 厂商LI文档内容时触发。涵盖文档分析→结构化总结→交叉链接→知识入库→增量更新的完整流程。

## 一、触发条件

- 用户以「学习」关键字开头发送文档内容
- 用户以「学习 /path/to/dir/」形式给出本地目录路径（agent 需自行发现目录下的文件并读取处理）
- 用户分享LI相关文档/报文/协议规范（HW/ ZTE/ Ericsson/ NSN/ Utimaco 等）
- 用户逐段发送命令参数/状态码/示例等碎片化内容

## 二、目录定位规则

### 2.1 三层知识库架构

LI 知识库采用三层结构：

| 层 | 目录 | 角色 | 内容特征 |
|---|------|------|---------|
| 结构化 KB | `knowledge/telecom/lawful_interception/` | 精炼的结构化笔记，含双向链接 | 参数表完整，wikilinks 交叉引用 |
| 协议参考 | `knowledge/hi2/` | HI2 接口专项（厂商协议+状态码+ETSI标准） | 按主题分目录（厂商对接/厂商状态码/华为LI协议） |
| 原始资料库（批量） | `knowledge/li/<vendor>/` | 原始厂商文档、导入的 CHM/PDF、运维文章 | 按厂商名分目录，保留原始文件名 |

**关系**：结构化 KB 和协议参考中的文档是 `li/<vendor>/` 中原始文档的 **精炼版本**。从 `li/` 到 `telecom/`/`hi2/` 是 **复制**（非移动），原始文件保留在原位。

### 2.2 `knowledge/li/` 下厂商目录结构

| 目录 | 内容 |
|------|------|
| `li/HW/` | 华为 CS/IMS/5GC LI 产品线。按 `SBC/` `IMS-VoLTE/` `CS-Core/` `5GC-EPC/` `HSS/` `ME60/` `LI-Protocol/` `ZTLIG-Integration/` `Tools/` `Archives/` 十个子目录归类 |
| `li/Ericsson/` | SOAP API WSDL 包、1 口对接、curl 实操、状态码、踩坑记录、埃塞现场经验、产品文档包（`.alx` 格式，见 `documentation/` 子目录） |
| `li/ZTE/` | CS LI HI1/HI2/HI3 规范、ReturnCode、ZXR10 命令参考 |
| `li/Utimaco/` | LIMS RAI v16.1 协议规范、RAI 状态码 |
| `li/ZTLIG/` | ZTLIG 运维手册、目标同步逻辑、Target 字段、TMC 工勘、NISS 运维文章 |
| `li/Sinovatio/DFX/` | DFX DPI 串接阻断 — 协议识别方法、PCAP 报文分析、培训文档 |
| `li/NSN/` | NSN PS LIC 错误码 |
| `li/Mavenir/` | Mavenir CM LI ADD/DEL 返回状态码 |
| `li/OpenLI/` | 开源 ETSI 合规 LI 系统（v1.1.19, GPL-3.0）。源码 `~/projects/openli/`，知识库 `openli-intro.md` |
| `li/OWLS/` | OWLS Operation Manual、TMC 数据处理、目标管理 API、SECPASS 启动 |
| `li/projects/` | 项目运维手册（如 a1-project/ 含 HDFS/HBase/Hive/YARN/Flink 等） |
| `li/SORM/` | 俄罗斯 SORM-1 标准（华为 SoftX3000 实现） |
| `li/tools-and-standards/` | 工具/通用标准（HI2 标准、ETSI 3GPP、Kafka/Zabbix/XSD/ASN1、WEB-UI 调试） |
| `li/international_project/` | 国际项目经验（工勘/LI 组网/抓包/打分） |

### 2.3 新文档归类

#### ⚠️ ZTLIG 多厂商文档分类陷阱

ZTLIG (Sinovatio/中新赛克) 是中间件 LI 网关，对接多厂商 LI 系统（Ericsson / Zeel / Utimaco 等）。当文档描述 ZTLIG 与某特定 LI 侧系统的对接工作流时，**分类取决于文档聚焦的 LI 侧协议**：

- 聚焦 ZTLIG 如何对接 **Ericsson LI-IMS**（soap/ericlis24）→ `li/Ericsson/`
- 聚焦 ZTLIG 如何对接 Zeel/Utimaco → 对应厂商目录
- 聚焦 ZTLIG 自身进程管理（无特定 LI 侧焦点）→ `li/ZTLIG/`
- 聚焦项目现场运维（多个 LI 侧混用）→ `li/projects/<project-name>/`

**判断方法**：看文档中的 debug 命令、日志样例、故障排查步骤指向哪个 LI 侧系统。如 `debug ztlig1 300 ericlis24 on` + `eric_lis_add` 日志 → Ericsson 场景。

新文档（原始导入/学习新内容 → 写入 KB）：

| 文档类型 | 目标目录（KB 写入位置） | 对应 li/ vendor 目录 |
|---------|------------------------|----------------------|
| 厂商LI接口规范（HI1/HI2/HI3/RAI/X1/X2/X3）| `knowledge/hi2/厂商对接/` | `li/<vendor>/` |
| 厂商状态码 | `knowledge/hi2/厂商状态码/` | `li/<vendor>/` |
| LI标准/演进/架构 | `knowledge/telecom/lawful_interception/` | `li/tools-and-standards/` |
| 爱立信 External API (SOAP/WSDL) | `knowledge/telecom/lawful_interception/` | `li/Ericsson/` |
| 非 ETSI 国家 LI 标准（俄罗斯 SORM 等）| `knowledge/telecom/lawful_interception/` | `li/SORM/` |
| 报文解析/运维经验 | `knowledge/hi2/` 子目录 | `li/<vendor>/articles/` |
| LIMS 系统工作流/运维手册 | `knowledge/li/Ericsson/`（爱立信LI-IMS场景）或 `knowledge/li/projects/a1-project/`（通用项目运维） | `li/Ericsson/` 或 `li/projects/a1-project/` |

### 2.4 首次目录组织（li/ vendor 重组）

> **⚠️ 入库后的副本同步（易遗漏步骤）**：结构化笔记写入 `telecom/` 或 `hi2/` 后，必须将生成的 `.md` 文件 **复制一份** 到对应的 `li/<vendor>/` 目录下（如 `li/Ericsson/`），使原始资料库和结构化 KB 保持同步。此步骤不要求修改文件内容，仅 `cp` 操作。如果不执行此步，后续 `li/` 下的文档搜索将遗漏已入库的精炼笔记。

当 `knowledge/li/` 下的厂商文档散落在历史目录中需要首次归类时：

当 `knowledge/li/` 下的厂商文档散落在历史目录中需要首次归类时：

1. **识别厂商归属** — 根据文件名前缀判断：华为*/hw-*/HW_* → 华为/；爱立信*/Ericsson* → Ericsson/；ZTE*/ZXR10* → ZTE/；Utimaco*/utimaco-* → Utimaco/；ZTLIG*/TMC* → ZTLIG/；NSN_* → NSN/；Mavenir_* → Mavenir/；OWLS*/A1项目OWLS* → OWLS/；A1项目* → projects/a1-project/
2. **创建目录**：`mkdir -p li/{华为,Ericsson,ZTE,Utimaco,ZTLIG,NSN,Mavenir,OWLS,projects,SORM,tools-and-standards}`
3. **移动文件**：用 `mv` 将文件从散乱目录移到对应厂商目录，保留原始文件名
4. **更新 README**：写入 `li/README.md` 反映新结构
5. **同时复制到结构化 KB**：精炼的结构化笔记写入 `telecom/`/`hi2/` 的同时复制副本到 `li/<vendor>/`

## 三、文档分析步骤

### 3.1 首轮完整文档

用户发完整文档时：

1. **识别文档类型** — 区分三类协议风格：
   - **二进制 PDU 协议**（如 Utimaco RAI）：需记录 PDU Type 表、各字段 Offset/Size、hex dump 示例
   - **CLI 命令集**（如 ZTE CS HI1）：需记录命令语法、参数表（M/O/C）、状态码、输出格式、示例
   - **SOAP/WSDL 接口**（如 Ericsson External API）：需记录 WSDL→XSD→Properties 追溯链、命名空间映射、请求结构树
2. **提取关键信息** — 协议类型、OID、接口定义、命令集、数据结构
3. **产出结构化摘要** — 表格+要点，避免大段原文
4. **检查已有知识** — 搜索 `~/knowledge/hi2/` 和 `~/knowledge/telecom/lawful_interception/` 中已有相关文档
5. **建立交叉链接** — 在摘要中标注 `[[已有文档名]]` 以供后续知识库写入

### 3.2 本地目录学习模式（user: "学习 /path/to/dir/"）

当用户给出本地目录路径而非粘贴文档内容时：

1. **探索目录结构** — 用 `find /path -type f | sort` 列出目录下所有文件，识别主要内容文件（\*.md、\*.txt、\*.html）和辅助文件（图片、VSX 流程图等）
2. **区分有效内容与噪声**：
   - Markdown 文档 → 直接读取
   - HTML 页面存档（Wikipedia 等）→ 提取正文内容或从 TOC 获取结构参照
   - `.alx` 文件（Ericsson 文档包）→ **特殊处理**：本质是 ZIP 压缩包，内含 HTML + PDF + GIF。先用 `file` 确认格式，再用 `unzip -l` 列出内容。用 `python3 -c "import zipfile"` 读取 HTML 标题和正文。编码可能为 UTF-8 或 GBK。部分 `.alx` 是拼接式 ZIP（多个 PK headers），需用 `ZipFile` 或二进制扫描提取。解压后用 `index.html` 或 `alexmain.html` 获取完整导航树。统计 HTML/PDF/GIF 数量反映文档规模
   - 图片文件（\*.png/\\*.jpg）→ 不处理，仅标注存在
   - Visio/VSX 流程图 → 不处理，仅标注存在
   - HTML 缓存文件（*_files/ 目录下的 css/js/php）→ 跳过
3. **定位核心文档** — 通常最有价值的是一份主要的 markdown 文件；如没有则从 HTML 提取正文
4. **提取并结构化** — 按参数表、命令集、状态码、示例码流等维度组织；注意文档格式可能严重破损（Windows 路径占位图、OCR 错位、表格渲染异常）
5. **归类到知识库目录**（见第二节的分类规则表），写入结构化笔记
6. **更新 references/knowledge-base-index.md** 做索引记录

### 3.3 已入库目录的新增内容学习模式（user: "学习 /path/to/已整理目录/新增加"）

当用户指向一个已经过首次整理的厂商目录，但表达有「新增加」内容时：

1. **识别新增项** — 用 `ls -lt --time=mtime` 按修改时间排序，最近添加的文件即为"新增加"内容
2. **判断新增项类型** — 区分三类新增内容：
   - **协议/标准文档**（.md）→ 按常规模式读取并结构化
   - **配置导出/备份**（ALLME 等 *.txt, *.tar）→ 提取关键元数据（时间戳、ME 类型、版本、站点名称），标注为运维参考数据而非协议文档
   - **工具包**（LI_SelfChkTool 等 *.tar）→ 列出目录结构和组件清单，标注用途和适用平台
3. **不处理非文档类资产** — 对于配置导出（ALLME 等）和工具包，仅做元数据摘要（时间、站点、版本、组件清单），不进行全量解析
4. **注意目录重命名** — 用户可能已重命名目录（如 `华为` → `HW`），需检查新旧目录名一致性，以最新名称为准
5. **更新目录描述** — 如需更新 skill 中的目录说明

### 3.4 Tar 包版本比较模式（user: "学习 *.tar" 且存在两个版本）

当用户学习一个 tar 包，且系统中存在同一发布的多个版本（如 R4A 和 R6A）时：

1. **找到所有副本** — `find /home -name "*<basename>*" 2>/dev/null`
2. **对比文件数** — `tar tvf <file> | wc -l` 比较两包的文件总数
3. **对比版本目录** — 列出每个包的顶层子目录名，找出差异
4. **对比核心文件** — 提取最新的共享版本目录（如 16A），`wc -c` 比较核心 WSDL/XSD 是否字节级一致
5. **报告版本差异** — 必须**明确区分**两个版本间实际协议差异（如有）和仅文件结构差异（如无）。以显式结论输出，如："R4A 与 R6A 在共享版本目录的 WSDL/XSD 字节级一致，协议层无差异。R6A 仅增加了 2dot4 目录。"
6. **产出版本演进表** — 按版本号顺序列出所有版本的 WSDL 数、FD 变体数、关键变化
7. **产出服务覆盖矩阵** — 列出所有服务在每版本中的可用性（✓ 或空白）
8. **生成部署对照** — 按实际 LIIMS 版本给出推荐参考目录

### 3.8 Tar 包/压缩包学习模式（user: "学习 *.tar / *.tar.gz / *.7z"）

当用户指向一个 tar、tar.gz 或 7z 文件时：

1. **定位文件** — 搜索系统中所有副本（`find /home -name "*.tar" -o -name "*.tar.gz" -o -name "*.7z"`），选择最新或最完整的
2. **列出内容结构** — `tar tvf <file>`（tar）或 `7z l <file>`（7z）查看目录层次和文件数量
3. **提取到临时目录** — `7z x <file> -o/tmp/<topic> -y`（7z）或 `tar xf <file> -C /tmp/<topic>`（tar）
4. **分析版本/目录结构** — 列出顶层子目录，识别版本演进和接口分类（如 X1/COD、X2/POD、X3/IWD）
5. **读取所有 markdown 文档** — 按接口类型分组读取，产出结构摘要
6. **资源归档** — 将压缩包留在原位。将提取内容以 `cp -a` 追加到 `li/<vendor>/<archive_basename>/` 目录。注意检查路径重叠避免覆盖已有文件
7. **更新已有结构化 KB 笔记** — 如果新提取的文档是已入库目录的补充内容（如新增 X1/X3 子目录），patch 更新已有结构化 KB 笔记，追加新章节覆盖全文档集全貌。而非创建独立的新笔记
8. **清理临时目录** — `rm -rf /tmp/<topic>`

### 3.5 已入库内容的学习模式（user: "学习 ~/knowledge/li/<vendor>/"）

> 也适用于 "学习 <vendor>/<archive_basename>.7z" 且该压缩包新增子目录内容到已处理目录的场景

当用户学习的是已经过知识库处理的目录（非原始文档导入）：

1. **枚举目录下所有文件** — `find <dir> -type f | sort`
2. **批量读取所有 markdown 文件** — 并发读取全部非 articles/ 子目录的文档
3. **按优先级处理**：核心协议规范 > 调试手册 > 踩坑记录 > 运维经验文章
4. **产出结构化总览** — 对每个文档给出：文档定位、关键参数表、核心数据结构、关联知识
5. **标注数据来源** — 区分来自原始 tar/文档的知识 vs 来自实操经验的现场知识
6. **询问是否入库** — 提问是否将新发现写入 KB（如果发现缺失的协议细节）
7. **归档新增子目录后的KB笔记更新** — 如果内容来自压缩包且已入库目录有新增子目录（如 MSS17A.7z 新增 COD(X1)/IWD(X3) 子目录到已有 POD(X2) 目录），则需 patch 更新已有结构化 KB 笔记：追加总览章节（含架构图/命令表/文档索引），而非创建新的独立笔记。保持原有笔记为核心入口，新增内容以章节追加

#### 目录分类补充：非 ETSI 国家 LI 标准

| 文档类型 | 目标目录 | 示例 |
|---------|---------|------|
| 非 ETSI 国家 LI 标准（俄罗斯 SORM 等） | `knowledge/telecom/lawful_interception/` | SORM-1 SOSM + 华为 SoftX3000 |
| 上述协议的接口规范（X1/X2/X3 等） | `knowledge/telecom/lawful_interception/` | 与 ETSI X 接口对照表一并写入 |

### 3.9 SOAP 样本学习模式（user: 提供原始 SOAP XML 请求/响应样本）

当用户提供一个 SOAP XML 样本（如爱立信 LI login/createWarrant 请求）时，采用以下专门流程：

1. **识别命名空间和版本** — 从 `<soapenv:Envelope>` 的子 namespace（如 `xmlns:ses="http://session.bind.external.ws2dot1.ims.epa.ericsson.se/"`）提取：
   - 服务类型：session/warrant/ne 等
   - API 版本：ws2dot1/ws12a/ws16a 等
   - 所属 WSDL/XSD 文件

2. **映射消息结构** — 从最外层向下逐层解析请求 XML，对照 WSDL 和 XSD 确认每个元素对应的类型：
   - `login → arg0 (sessionRequest)` → `userName (limitedStringType) + password`
   - `createWarrant → arg0 (warrantCreateRequest)` → `header (requestHeader) + item (warrantItem) + dtlWarrants`
   - 标注字段规范类型（xs:string/xs:int/xs:short/limitedStringType）

3. **比对 XSD 校验元数据** — 关键核对点：
   - `warrantID` 创建时固定为 -1（XSD 定义 xs:int）
   - `supplementaryInfo` 为位掩码（XSD 定义 xs:short）
   - `positioningPeriod` 有限制枚举值（-1/5/15/30/45/60）
   - `isDataMonitoringOnly` 有限制枚举值（0/1/2/3...256）
   - `activationTime=0` 表示立即激活（xs:long）
   - `terminationTime` 为毫秒级 Unix 时间戳
   - `type.__value=1` 表示操作类型为 Create

4. **检查已有知识库文档** — 搜索 `li/<vendor>/` 中以下关联文档：
   - 登录返回状态码文档（匹配 status.__value）
   - curl 对接文档（匹配 curl 调用方式）
   - External API 概览文档（匹配服务矩阵和版本演进）
   - WSDL/XSD schema 文件（匹配精确的类型定义）
   - HI1 字段详解文档（匹配 supplementaryInfo/targetTypeID/MCNB 等字段的取值说明）

5. **输出结构化参考文档** — 文档应包含：
   - 完整请求 XML（保留原始 namespace 声明）
   - 消息层次树（每层标注对应的 XSD 类型）
   - 所有字段的完整表格，含 XSD 类型、样本取值、说明
   - 对于枚举型字段，列出 XSD 中定义的所有合法取值（如 neType/targetTypeID/positioningPeriod/isDataMonitoringOnly）
   - 对于位掩码字段，列出常见合法组合值（如 supplementaryInfo=1/3/7/31/287/543）
   - 典型成功响应 XML 示例
   - 与之前已入库的关联样本建立双向链接（login ↔ createWarrant）

6. **版本对比** — 如果 WSDL/XSD 有多个版本存在：
   - 列出样本所用版本（如 ws2dot1）与最新版（ws16a）之间的类型差异
   - 如 userName 从 limitedStringType → xs:string，namespace 变化等

7. **type.__value 操作类型映射** — 从 header.type.__value 反向映射操作语义，写入知识库文档：

   | 值 | CRUD | 含义 | 操作 |
   |:---:|:----:|------|------|
   | 1 | C | Create | createWarrant |
   | 2 | D | Delete | deleteWarrant |
   | 3 | R | Read/Query | getWarrantList |
   | 4 | U | Update/Modify | modifyWarrant |

8. **listInformation 分页结构** — 查询类操作（getWarrantList）的独立处理流程：
   - `recordsOnThisPage=0`（请求时固定值）
   - `maxRecordsPerPage=10000`（或按需设置）
   - `pageNumber=1`（从1开始）
   - `totalPages=-1`（请求时固定值）
   - 响应时 LIIMS 填充实际值
   - 建立 `orderArray` 排序规则：`listElementIdentifier=0`(warrantID), `orderDirection.__value=1`(ASCENDING)

9. **modifyWarrant 的两种用途** — 同一操作在不同上下文中的语义差异：
   - **修改参数**：state=activated，在 item 中填入需修改的字段（如 MCNB/LEMF/定位周期/MUID），LIIMS 只更新非空字段
   - **终止监听（Terminate）**：state=terminated，之后必须 sleep 3s 等待 MSC 确认，然后才能执行 deleteWarrant
   - 结构上与 createWarrant 完全一致（header + item + dtlWarrants），仅 type.__value=4 不同

10. **deleteWarrant 关键差异** — 与 create/modifyWarrant 同字段但结构最简：
    - `warrantDeleteRequest` 只有 `header + item`，**没有 dtlWarrants**（XSD 中 `warrantDeleteRequest` 不包含 dtlWarrantNeTypeItemArray）
    - type.__value=2（DELETE 语义，HTTP DELETE 类比）
    - warrantID 必须是已分配的真实 ID（非 -1）
    - 必须先完成 modifyWarrant(state=terminated) → sleep 3s → 确认后才可 delete，否则返回失败

11. **完整 SOAP 样本文件规范** — 每个样本文件必须包含：
    - 完整请求 XML（保留 namespace 声明）
    - 消息层次树（每层标注 XSD 类型）
    - 所有字段完整表格（XSD 类型 + 样本值 + 说明）
    - 枚举字段列出 XSD 定义的全部合法值
    - 位掩码字段列常见组合值
    - 典型成功响应 XML 示例
    - **四样本对比表**（login / createWarrant / getWarrantList / modifyWarrant）：Service / type.__value / 关键入参 / 关键出参
    - **完整生命周期工作流图**：login → createWarrant → getWarrantList(确认) → modifyWarrant(terminate) → sleep 3s → getWarrantList(确认terminated) → deleteWarrant → logout
    - 与已有样本的双向 wikilink

### 3.11 PCAP 报文验证学习模式（user: "学这个目录下 *的报文，分析是否学到了"）

当用户先分享培训文档（或已有 KB 笔记），再指向一个 PCAP 目录要求分析验证时：

1. **探索 PCAP 目录** — 列出所有 `.pcap` / `.pcapng` 文件，文件名通常对应培训文档的各个识别方法（如 `五元组ip.pcap`、`http-host.pcap`、`https-sni.pcap`、`quic-sni.pcapng`、`协议插件.pcap`、`组合条件.pcap`）

2. **按识别方法分类分析每个 PCAP** — 使用 `tcpdump -nr <file> -v` 查看报文概览，对关键报文用 `-X` 查看 hex dump：

   | 识别方法 | 关键检查点 |
   |---------|-----------|
   | 五元组 IP | 目标 IP 是否匹配培训文档中的应用 IP 列表 |
   | HTTP Host | `http.host` 字段值是否匹配 |
   | HTTPS SNI | TLS Client Hello 中 SNI Extension 的值 |
   | QUIC SNI | QUIC CHLO 包中的 SNI tag 值 |
   | 协议插件 | TCP payload 前 N 字节的固定魔数 |
   | 组合条件 | 多个特征字段同时存在且交叉匹配 |

3. **验证 TCP 报文完整性** — 检查是否包含三次握手包（SYN → SYN-ACK → ACK），缺握手包的报文可能来自 TCP 长连接的重传或 keepalive，需要告知用户

4. **对照培训文档逐条验证** — 对每个 PCAP，检查其特征（IP、Host、SNI、码流）是否与培训文档中的说明完全吻合。标注 ✓ 或 ✗

5. **HEX 码流定位** — 用 `tcpdump -X` 输出中找到特征字段的精确偏移位置（如 `0x00d0:  692e 696e 7374 6167 7261 6d2e 636f 6d` = `i.instagram.com`），在笔记中标注偏移量方便日后快速定位

6. **产出结构化分析笔记** — 每个 PCAP 在笔记中的条目包含：
   - 时间戳、源/目标 IP 和端口
   - 对应培训文档中的识别方法
   - 关键码流特征（含 HEX 偏移定位）
   - DPI 特征表达式（如 `ip.addr == 69.171.250.52`）
   - 与培训文档的对照结论（✓完全吻合/✗有差异）
   - 实测洞察（如"CDN 混淆"、"端口不决定协议"、"长连接无握手包"）

7. **建立双向链接** — 分析笔记通过 wikilink 关联培训文档笔记，反之亦然

8. **注意异端场景**（本模式陷阱）：
   - **QUIC 流量**是 UDP 不是 TCP，tcpdump 默认不解析 QUIC 协议层，需手动查看 hex 中的 SNI 标签
   - **协议插件场景**的 TCP payload 在 80 端口但非标准 HTTP，不可用 `-A`（ASCII）查看，必须看 hex
   - **CDN 混淆** — 同一个 IP 可能服务于多个应用（如 Facebook CDN），必须结合 SNI/CN/Host 多重验证
   - **防火墙/NAT 后的 IP** — PCAP 中的源 IP 可能是测试专用地址（如 192.168.23.x），不代表现网真实设备地址

当用户提供的目录中包含 `.png` 工作流图（如 ZTLIG 架构图、数据流图）时：

1. **优先尝试 vision_analyze** — 使用当前模型支持的视觉能力分析图片。如果失败（模型不支持 `image_url` 类型），改用 3.8.2 的 API 直调方案

#### 3.10.2 API 直调方案（vision_analyze 不可用时的备用路线）
   - 确认可用视觉模型：通过 `curl -s -X GET 'https://api.siliconflow.cn/v1/models' -H "Authorization: Bearer $KEY"` 列出 VL 模型
   - SiliconFlow CN 可用 VL 模型（2026-06）：`Qwen/Qwen3-VL-32B-Instruct`、`Qwen/Qwen3-VL-8B-Instruct` 等
   - **密钥传递技巧**：API 密钥存储在环境变量中（如 `SILICONFLOW_CN_API_KEY`），但 Hermes 会在 terminal 命令输出中将其替换为 `***`，导致写入脚本后密钥变为字面量 `***` 而失效
   - **正确做法**：先生成 payload JSON 文件到 `/tmp/`（不含密钥），然后用 `K=$(printenv KEY_NAME) && curl -H "Authorization: Bearer $KEY"` 两步法执行，curl 从 shell env 读取密钥但 shell 自身不会将 env 值泄露到文件
   - 模型选择策略：大图（>500KB）用 8B，细节密集型用 32B；超时设 180-300s
   - 图片预处理：将原图缩小到 800px 宽、JPEG 85% 质量可大幅减少 base64 体积（~60KB），同时保持可读的文字细节

3. **提示词要求** — 视觉模型提示词必须明确说明系统背景（如“这是一个 ZTLIG 法律监听系统的工作流图”），要求列出所有可见文字（中英文）、所有组件框和箭头流向。中文提示词比英文更准确。

4. **结果处理** — 视觉模型识别的文本可能有偏差或幻觉，需结合已有文档做交叉验证。将识别结果整理为结构化 Markdown 笔记写入 `li/Ericsson/`（爱立信场景）或 `li/projects/` 目录，包含组件表、数据流描述、配置信息、与已有文档的关联。

#### 3.10.3 视觉识别不可用时的最终回退

当 vision_analyze 和 SiliconFlow VL API 均失败（模型不支持 image_url、无 VL API key、无 tesseract OCR）时：

1. **告知用户现状** — 当前环境无法自动 OCR 图片内容，说明原因（model 不支持 vision + 无 OCR 工具）
2. **提供可操作的安装命令** — 给出 `sudo apt install -y tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-eng` 让用户自行安装
3. **pytesseract 预装** — pip pytesseract 可提前装好，tesseract 二进制到位后即生效
4. **推荐运行命令** — `tesseract image.png stdout -l chi_sim+eng --psm 6`
5. 如果用户无法安装，请求用户简要描述图片内容，由 agent 手动整理

### 3.6 压缩包/XSD/WSDL/XML 样本分析模式（非 markdown 文档场景）

当压缩包（.7z/.tar/.tar.gz）内容为 XSD/WSDL/XML 样本文件而非 markdown 文档时：

1. **读取原始 Schema 文件** — `.xsd` 和 `.wsdl` 文件需直接 read_file 提取接口定义和数据结构，而非依赖 markdown 摘要。重点关注：
   - WSDL: 命名空间、操作列表（SOAP binding）、请求/响应消息类型、端口地址
   - XSD: complexType 定义、element 枚举值、minOccurs/maxOccurs 约束、pattern/restriction
2. **读取 XML 样本** — 从请求/响应样本中提取：
   - 完整字段取值（如 litid/target/deliveryfunction2/3 等）
   - 区分编码方式（CDATA 明文 SIP vs Base64 编码）
   - 提取现网特征（MCC/MNC/IMS 域/User-Agent/接入网类型/媒体编码等）
3. **交叉引用现有知识库** — 搜索 `knowledge/li/<vendor>/` 和 `knowledge/hi2/` 中已有文档：
   - 已有状态码文档（核对返回码是否匹配）
   - 已有工具文档（如 `LI_ASN1解码工具_架构文档.md` 中的 Mavenir XML 解码说明）
   - ZTLIG 对接配置（如 `ztlig.ssf.xxx.interfaceType = 3`）
4. **确定是"新笔记"还是"补充现有笔记"**：
   - 同一接口/协议的不同方面（如已有状态码文档，现在新增 X1/X2/X3 Schema）→ **创建新笔记**，在同一厂商目录下并列
   - 同一文档的新版本/新增章节（如 WSDL 从 R4A 升级到 R6A）→ **patch 更新** 现有笔记
5. **YAML frontmatter** — 必须包含：
   - `source`: 记录原始文件路径（如 `/home/andymao/tempfile/Mavenir-IMS-LI.7z`）
   - `links`: 双向链接既有知识库文档
   - `created`: 入库日期
6. **资源归档** — `cp -a` 将原始压缩包提取内容复制到 `li/<vendor>/<archive_basename>/` 保留原始素材
7. **清理临时目录** — `rm -rf` 提取目录

### 3.7 逐段碎片（增量模式）

用户逐段分享（如 "Arguments", "Status", "0", "201,202", "liid=LiId", "net=Networks"）时：

1. **识别上下文** — 根据前后文判定属于哪个命令/章节
2. **收集而非立即写入** — 参数类内容（如 `liid=LiId`, `net=Networks`）按「收集-批处理」模式处理：在内存中累积参数列表，等用户发完 Status/Output/Examples 后一次性更新笔记
3. **状态码按行追加** — 用户发单个码值（0, 201,202, 501）时同样收集，等完整后再写入表格
4. **用 patch 增量更新** — 内容齐备后用 skill_manage(action=patch) 或 patch 工具做精确更新
5. **参数表格式** — 统一用 Markdown 表格 `| 参数 | M/O | 说明 |`
6. **状态码格式** — 统一用 `| 码 | 含义 |` 表格
7. **保留原始引用** — 文档中的 (cf. 4.1.3)、(cf. 4.14) 等交叉引用要保持原样写入，帮助用户关联原始文档章节

8. **⚠️ patch 上下文匹配陷阱（多表格场景）** — 当同一文件中有多个结构相同但内容不同的 Markdown 表格时（例如 tdel 和 tmod 的状态码表都包含 `| 0 | 成功 |`），直接 patch 会因为匹配到多处而失败（返回 "Found 2 matches"）。应对方法：

   - 在 old_string 中包含足够多的上下文行（包括章节标题 `#### 状态码`）消除歧义
   - 例如：用 `` `tmod` 命令可返回以下状态码（cf. 4.14 完整状态码表）：\n\n| 码 | 含义 |` `` 替代 `| 码 | 含义 |` 作为匹配起点
   - 如果匹配仍然重复，先读文件确认该区域的精确内容，复制更长的 old_string
   - **最后手段**：如果旧字符串跨越多行且仍匹配多处，使用 read_file 确认当前文件的精确状态后，用包含章节标题 + 表头 + 至少一行数据的内容作为 old_string。如：`` `tmod` 命令可返回以下状态码（cf. 4.14 完整状态码表）：\\n\\n| 码 | 含义 |\\n|----|------|\\n| 0 | 成功 |` ``\n\n9. **⚠️ 长期 patch 的结构脆弱性陷阱** — 当对同一文件进行 50+ 次增量 patch 后，文档结构可能无声退化：代码块结束标记（```）被消耗、章节标题被覆盖、列表缩进错位、分隔线（---）丢失。这是因为每次 old_string 匹配都在切割和替换文件片段，长序列操作后边界可能偏移。应对方法：\n   - 每 20-30 次 patch 后，用 read_file 重新读取受影响区域的完整上下文\n   - 如果发现结构损坏（如缺少 ``` 或 ## 标题），立即用 patch 修复后再继续\n   - 在 patch 中优先选择包含周围上下文行（如上方标题+下方空白行）的 old_string，不只用单行匹配\n   - 特别注意代码块（```）和水平分割线（---）—— 它们是结构边界，最容易在反复 patch 中被意外替换或消耗

#### 典型增量场景示例（Utimaco RAI tmod 参数表 — Andymao 工作模式）

用户（Andymao）可能以如下碎片序列分享命令定义：

```
Step 1: Syntax 行 → tmod tno_id=TargetNoId liid=LiId net=Networks ...
Step 2~N: 逐参数补充 Description（20+ 次往返）
Step N+1: Flags 参数（mcflags/srflags/gprsflags/hlrflags/targetflags 等）
Step N+2: LBS 参数（periodic_loc/resp_type/.../max_loc_age）
Step N+3: Status → 逐码分享（0 → 100-199 → 201 → 202 → ...）
Step N+4: Output → 单句描述
Step N+5: Examples
```

**补充场景：tstate 简单命令模式**

当用户分享简单命令（3 个参数以内，如 `tstate icd=UemRefno tno=TargetNo doo=DateOfOrder`）时：
- 所有参数通常为 M（必填），无 O/C 区分
- 同样遵循碎片化分享：先 Syntax，再逐参数描述，再逐码分享状态码
- Doo 描述模板同 tmod/tdel：`"The date of order for the ICD change. Same format as in icdadd (cf. 4.5.2)"`
- 状态码子集通常与 tdel/tmod 共享（0/100-199/201/202/250/251/290/291/501）

**补充场景：Utimaco LIMS RAI 协议（二进制 PDU + CLI 混合模式）**

Utimaco LIMS RAI 是比较罕见的 二进制会话协议 + 文本命令语言 混合 LI 管理接口。有以下专属模式：

1. **RAI-SP 会话层规则** — 7 种 PDU（Type 1-7），固定头格式。TCP 端口 52134，登录 PDU 固定 126 字节。需记录 PDU 结构表（Offset+Size+Description）

2. **mc_xxx 语义一致性** — 所有 mc_xxx 参数（mc_voice/mc_iri/mc_data/mc_iri_po/mc_iri_mm/mc_vm/mc_mm/mc_email/mc_ia/mc_online/mc_offline/mc_iri_5g/mc_data_5g）共享相同语义：不传则保留现有 MC 分配，传入则必须是已存在 MC ID 并替换。但每个参数的描述必须独立输入英文原文，不可使用 Same semantics 缩写 — 用户要求每个 mc_xxx 的描述完整且与原始文档一致

3. **tmod 参数复用 tadd 结构** — tmod 参数表与 tadd 高度一致，但有三类差异需注释：
   - tmod 中几乎所有参数为 O（tadd 中部分为 M，如 net/dtype/mc_voice）
   - tmod 的不传则保留原值 语义
   - 部分参数从 O 变为 C（如 LBS 参数 periodic_loc/resp_type/hor_acc 等，PSTN 参数 dir/ton）
   - 建骨架时：先在 tadd 参数表基础上快速复制，再统一替换 M/O/C 标记

4. **LBS 参数群（所有均为 C 非 O）** — 共享 In LBS networks you can define... 描述模式：
   - periodic_loc (DDhhmmss, default exists) | resp_type (0=no_delay/1=low_delay/2=delay_tolerant)
   - resp_timer (integer, seconds) | hor_acc (integer, meter) | alt_acc (integer, meter)
   - ll_acc (integer, seconds) | max_loc_age (integer, seconds)

5. **PSTN 参数** — dir(C) / ton(C) 仅 PSTN 目标时适用

6. **tnelist 命令特殊属性**：
   - 功能仅对部分 NE 供应商实现（Nokia 7750 SR MG/VMG/CMG, Nokia MSC/MSS, Nokia DX HLR, Nokia NTAS, Huawei SOFTX3000, Broadsoft, Starent, Sonus, Ericsson 等）
   - 非确定性实现：两次相同条件的 tnelist 结果可能不同（异步供应商接口 + 并行 RAI 命令 + LIMS 事件调度）
   - Parsing Error 是 Communication Error 的子类型，应通过 NE 配置修复

7. **mc/mclist 监控中心命令** — mclist 支持 mc= 和 lea= 两个筛选参数。输出格式包含 MC 全部配置参数。状态码范围包括 261/262/340/341

8. **业务规则关联** — 参数 net、dtype 和 mc_xxx 非独立，必须始终遵循 LIMS 业务规则（cf. 4.2.2 和 4.2.3）

9. **MC 管理命令模式** — Utimaco MC 命令与 Target 命令共享很多参数，但有独立模式：
   - **mclist**：支持 mc= 和 lea= 两个筛选参数，输出 38 个字段（含 Genband C20 LAES 参数）。状态码 261/262/340/341
   - **mcadd**：按 MC 类型差异很大。FTP MC 需 ipaddr+user+pwd+dir；ISDN MC 需 isdn+cugilc+cugdnic；FTAM/X25 需 x25addr+tsel+ssel+psel+aent；TCP MC 需 ipaddr+port+keepalive+dataloss 等。成功输出 `mc_created mc=MCId`
   - **mcdel**：仅 1 个参数 mc=M。被目标引用时返回码 630
   - **mcmod**：参数与 mcadd 一致但均为 O。各 MC 类型有各自允许的参数集

**补充场景：tnelist 网元查询命令**

当用户分享网元查询命令（如 `tnelist`）时注意其特殊属性：
- 功能可能仅对部分 NE 供应商实现（完整支持列表见知识库文档，包括 Nokia 7750 SR MG/VMG/CMG, Nokia MSC/MSS, Nokia DX HLR, Nokia LIG/NTAS/Open TAS/CFX-5000 IMS/SBC, Huawei SOFTX3000/CDMA MSC/WCDMA MSC/HLR CS/IMS/PES-PSS AS CS/CSCF CS/AGCF CS/SBC/MSOFTX3000/mAGCF CS, Broadsoft BroadWorks, Starent GPRS/LTE, Sonus EMS, Ericsson MSC 等）
- **非确定性实现**：两次相同条件的 tnelist 结果可能不同（因异步供应商接口 + 并行 RAI 命令 + LIMS 事件调度），需在笔记中标注此属性
- Parsing Error 是 Communication Error 的子类型。如果 LIMS 无法理解 NE 返回的报告，可能将错误的报告解析为正确（不报 Parsing Error），应通过 NE 配置修复
- 仅审计员可用，且该用户不能绑定到任何 LEA
- 输出格式：`netarget neid=NeId tno=NeResult`（tno 可能是实际号码、"Communication Error" 或 "Parsing Error"）

**补充场景：NC/MC Management 命令群**

当用户分享 MC 管理命令（mclist/mcadd/mcdel/mcmod）时：

1. **mclist** — 输出 38 个字段，含 Genband C20 LAES Mode 特有参数（agency/billing/sts/pre_trans/lca/pic/lata）。支持 mc= 和 lea= 两个筛选参数（取交集）。状态码范围 261/262/340/341
2. **mcadd** — 参数按 MC 类型差异大：FTP 需 ipaddr+user+pwd+dir；ISDN 需 isdn+cugilc+cugdnic；FTAM/X25 需 x25addr+tsel+ssel+psel+aent；TCP 需 ipaddr+port+keepalive+dataloss 等 Keepalive 群参数。成功输出 `mc_created mc=MCId`
3. **mcdel** — 仅 1 参数 mc=M。被目标引用时返回码 630，ICD 状态无关。无输出
4. **mcmod** — 参数与 mcadd 一致但均为 O。各 MC 类型允许的参数集不同。无输出

**补充场景：NE 管理命令（nelist/neadd/nedel）**

当用户分享 NE 管理命令时：

1. **nelist** — 支持 neid= / provider= / all 参数。输出含 neid/netype/osversion/nextosversion/effect/status/param1-paramx/provider/net/ttype。状态码范围 700-749。effect 支持 YYYYMMDDhhmm 或 "NOW"/"NONE"。status 值为 ADMIN / ADMIN/CHECK（默认）/ NO
2. **neadd** — neid/netype/osversion 为 M；param1-paramx 为 M（按项目需求）；effect 为 C；status/provider 为 O。成功输出 `ne_created neid=NeId`。状态码 900=网元已存在
| **nedel** | 仅 neid=M。状态码 700-749。无输出
| **nemod** | neid(M)，其余 O。状态码 700-749, 900。无输出
| **necheck** | neid(M)，icd+tno 或 tno_id 为 C，all/check_only 为 O。输出 necheckerror 格式，corr=y/n/c。状态码 201/202/700-703
| **nepurge** | neid(M)，all(O)。输出 nepurge 或 nepurgeerror 格式。状态码 201-202/700-703

**补充场景：LEA/User 管理命令群**

当用户分享 LEA 或用户管理命令时：

1. **LEA 命令** — lealist/leaadd/leadel/leamod：
   - lealist：参数 lea(O)，输出 11 字段（含 HSM/SSL 加密参数 enckey/account/password/groupname/ipaddress）
   - leaadd：lea(M)/leaname(M)，其余 O（含加密参数需许可且仅管理员）。输出 lea_created lea=LeaId
   - leadel：lea(M)。无输出
   - leamod：lea(M)，其余 O。无输出
   - HSM/SSL 参数（enckey/account/password/groupname/ipaddress）在 lealist/leaadd/leamod 中共享相同描述模式

2. **User 命令** — userlist/useradd/userdel/usermod：
   - userlist：参数 userid(O)，输出 6 字段（userid/username/usertype/state/lea/functions）
   - useradd：userid(M)/username(M)/password(M)/usertype(M)/lea(M)/functions(M)，state(O=default active)。输出 user_created userid=UserId
   - userdel：userid(M)。无输出
   - usermod：userid(M)，其余 O。无输出
   - usertype: A=Administrator, O=Operator, K=Auditor

3. **审计日志** — backuplog/functionlog/loginlog：
   - 命令 from/to 参数通常为 O，格式 YYYYMMDD。状态码共享 222/223/227
   - backuplog 输出含 user/time/result (failed/successful)
   - functionlog 输出含 user/time/info/function/result
   - loginlog 输出含 system_user/user/time/function (Login/Logout)/result

**补充场景：5G LI 标准知识入库**

当用户分享 5G LI 标准/演进内容时（如毛恒镇《LI 标准和演进》）：

1. **定位到 telecom/lawful_interception/** 目录
2. **提取内容**：3GPP SA3-LI 新规范体系（33.126/33.127/33.128）、ETSI TC-LI 标准族（102232/103120/103221/101331/102657/101671）、X1/X2/X3 标准化接口细节、5G NF 触发机制（LI_T3）
3. **建立链接**：与已有 hw-svc-5gc-li-x-interface.md、wsdl-xsd-basics.md 等文档建立双向链接
4. **交叉参考**：5G NF（AMF/SMF/UPF/UDM/SMSF）、临时标识符与永久标识符映射、虚拟化安全

**处理策略（本模式专属）：**

1. **Syntax 先行建骨架** — 收到 Syntax 行后立即在笔记中建立完整命令框架。参数表用参数名先行占位，Description 列用 "TBD"。`| 参数名 | M/O | 说明 |` 表格格式先行定稿

3. **参数描述逐段 patch**：
   - **mc_xxx 语义一致性** — 所有 mc_xxx 参数（mc_voice/mc_iri/mc_data/mc_iri_po/mc_iri_mm 等）共享 "If not present keep existing, otherwise replace with existing MC ID" 语义。但每个参数必须独立输入英文原文，不可使用 Same semantics 缩写 — 用户要求每个 mc_xxx 的描述完整且与原始文档一致
   - **tmod 参数复用 tadd 结构** — tmod 参数表与 tadd 高度一致（共享相同参数名称和值域），但需注意三类差异：tmod 中几乎所有参数均为 O（tadd 中部分为 M）；tmod 的不传则保留原值 语义；部分参数在 tmod 中从 O 变为 C（如 LBS/PSTN 参数）。建议：先在 tadd 参数表基础上快速建骨架，再批量替换 M/O 标识，最后逐段完善描述
   - **NEID 参数语义一致性** — fix_neid/fix_neid2/ia_neid/hlr_neid/voip_neid/cmts_neid
   - **LBS 参数** — 所有 LBS 参数均为 `C`（条件可选，非 O），共享 "In LBS networks you can define..." 模式

4. **参数类型标记注意** — 用户可能中途修正 M/O 标记（如 `O` → `C`），每次 patch 时需留意。常见场景：LBS 参数 initial 为 O，用户中途更正为 C；PSTN 参数 dir/ton 同理

4. **状态码逐码收集** — 规则：
   - 单码（`0`）→ 直接追加
   - 码段（`100-199`）→ 保留范围不展开
   - 码对（`250, 251`）→ 分两个独立行
   - 全部收齐后检查顺序

5. **示例收集** — 多条示例收集后一次性写入，不逐条 patch

6. **用户习惯**：
   - 单字回复 `?` 表示 "继续/等待"，非疑问
   - 页码标记（`80 March 21 ? ? Copyright Utimaco TS GmbH`）可忽略，这是文档水印/页眉
   - **空消息/仅标点回复：永远不要返回空响应。** 当收到空消息、仅标点的消息、或不完整的参数名开头时，不要静默跳过。应回复一句简短确认（如"收到了，请继续分享更多内容。"或"要继续分享剩余参数还是跳到 Status？"），让用户知道你在等待。
   - `(cf. X.X.X)` 引用保留原样
   - 用户偏好 80 行左右的终端宽度文本渲染

7. **参数名称不完整输入（本模式专属陷阱）**：

   用户可能以不完整字符串开始一个参数名，等待你先行处理再发送后续字符补全。例如用户先发 `"modem_ma"` 再发 `"c"` 或先发 `"max_loc_ag"` 再发 `"e"`。

   应对策略：
   - 收到不完整的参数名时，不要立即搜索或 patch
   - 回复一句简短的确认等待用户发送完整内容
   - 等到用户发送完整参数名和描述后再一次性处理

### 3.13 .alx 爱立信产品文档包分析模式（user: "学习 xxx.alx"）

当用户指向 `.alx` 文件（Ericsson 标准化产品文档包，SEIF 格式）时：

1. **确认格式** — 用 `file` 命令确认，.alx 本质是标准 ZIP 压缩包
2. **列出文档结构** — `unzip -l xxx.alx` 查看文件数量和类型。典型构成：HTML（目录导航+正文）+ PDF（架构图/流程图）+ GIF/PNG（截图）
3. **获取文档元数据** — 读取 `profile.xml`（xml 格式，utf-8 编码）获取：`libName`（产品名）、`productVersion`、`issueDate`、`topicNumber`（主题数）、`securityLevel`、`productType` 等
4. **提取 HTML 标题** — 遍历所有 `.html` 文件，读取 `<title>` 标签内容。分类统计：CLI 命令参考、接口描述、功能特性、告警处理等
5. **编码处理** — HTML 文件可能为 UTF-8 或 GBK（中文文档），用 `.decode('gbk', errors='replace')` 或 `.decode('utf-8', errors='replace')` 尝试解码
6. **输出结构化笔记** — 产出包含：产品名/版本/日期/文档 ID、文档结构树（三级）、CLI 命令分类、接口列表、功能特性清单、其他内容（参数/告警/应急/健康检查）、文件间关联关系图
7. **多包关联** — 若存在多个 .alx（如 SGSN-MME + OSS-RC + SmartEdge），需梳理产品线间的关联关系（分组核心网→运维平台→硬件平台）
8. **特殊处理** — 部分 `.alx` 是拼接式 ZIP（多个 PK headers 在同一个文件中），标准 `ZipFile` 可能报错。可用 `data.rfind(b'PK\\x05\\x06')` 定位 EOCD，截取 `data[:eocd_pos+22]` 为合法 zip。或直接二进制扫描提取文件名

### 3.14 工作/学习材料整理模式（user: 分享英语学习/技术教程等非 LI 内容）

当用户分享非 LI 技术文档的工作/学习材料时（如工作英语、C 源码教程等）：

1. **识别内容类型**：词汇表用 `| 搭配 | 中文 |` 表格组织；会话场景分场景列表，中英对照；信函模板保留原文 + 结构分析 + 可学短语；实战范例保留原文 → 背景 → 结构分析 → 写作技巧 → 短语表；技术教程提取核心步骤 + 注意事项
2. **输出格式**：中英对照表格统一排版；原文保留格式不截断；每个例句标注适用场景；按基础→进阶→实战层次组织
3. **归类策略**：英语类→ `knowledge/articles/`；编程教程→ `knowledge/program-info/` 对应子目录；工具教程→ `knowledge/program-info/开发运维/`；不写入 LI 涉密目录

### 3.12 厂商 LI 配置文件分析模式（user: 分享 ztlig.cfg / ZTE 配置脚本 / 参数表）

当用户分享厂商 LI 系统配置文件时（如 ztlig.cfg、ZTE MSC/MGW 配置脚本、对接参数表）：

1. **识别配置块类型** — ztlig.cfg 有多段结构：
   - `[GLOBAL]` — 全局参数（FTP 凭证、Kafka 模式）
   - `[ZTLIG1_*]` — X1 口设控实例
   - `[ZTLIG2_*]` — X2 口 IRM 实例（含 leaid_port 映射）
   - `[NE_*]` — 网元配置（vendor/version/x1_ip/x1_port/x2_ip/x2_transtype）
   - `[VNE_*]` — 虚拟网元（vneid/vne_type/operid/hi2_neid）
   - `[LEA_*]` — 监听机构（hi1_ip/hi2_ip/hi3_ip/vne_oper/neid_port）
   - `[CSHI3_GLOBAL]` — X3 口 SS7 参数（pointcode/MTP2 links/pcmindex）
   - `[SSF_*]` — 信令面参数（countrycode/SIP-I params）
   - `[RVF_*]` — 语音面参数（RTP 端口/录音时长）

2. **提取关键字段表** — 为每种配置块类型建立参数字段总表，标注：参数名、类型（字符串/整数/IP/端口）、默认值、取值说明、适用场景

3. **关联多段配置** — 同一对接场景跨越多个配置块（如 Airtel ZTE LIS 场景跨越 `[ZTLIG2_464]` + `[NE_666]` + `[VNE_766/767]` + `[LEA_800]`），必须做跨块关联分析

4. **提取对接参数表** — 从配置中提取：X1/X2/X3 接口参数总表、VNEID ↔ MSC Number 映射表、E1/CIC 分配表（PCM/SLC/CIC 范围/信令时隙）、NEID ↔ 端口映射

5. **注释现场信息** — 配置文件中的中文注释（如 `#ZTE 1口地址`、`# 针对重复vneid增加配置读取alias`）是现场经验的重要来源，需保留并描述

6. **标注已知问题** — 配置中可能包含：格式问题（alias 字段多余分号）、厂商标注不准确（hw 标注但实际是 ZTE）、死配置（ping 不通的 IP）、历史遗留注释

7. **跨运营商对比** — 当同一配置文件包含多运营商时（如 Airtel ZTE LIS + MTN HW + Zamtel），对比配置模式差异

8. **写入规范** — 配置分析写入 `li/ZTLIG/`（ZTLIG 配置）或 `li/<vendor>/`（厂商脚本），原文保存到 `li/ZTLIG/references/`

## 四、知识库条目模板

### 文件头 (frontmatter)

```yaml
---
title: 规范的文档标题
tags:
  - 厂商名
  - 协议名称
  - LI
  - 相关标签
links:
  - "[[已有文档1]]"
  - "[[已有文档2]]"
created: YYYY-MM-DD
source: 原始文档标题
---
```

### 内容结构

```
# 标题

## 目录（可选，长文档）

## 1. 概述/定位

## 2. 协议细节（逐层深入）

## N. 与同类系统对比（可选，跨厂商时）

## 关联知识点

- [[文档1]] — 用途说明
- [[文档2]] — 用途说明

## 元数据

- **来源**：...
- **入库时间**：...
- **分类**：...
- **数据级别**：LEVEL 3（标准接口规范，可外发）
```

### 数据级别规则

| 级别 | 说明 | 外发限制 |
|------|------|---------|
| LEVEL 3 | 标准协议/接口规范 | 可外发 |
| LEVEL 4 | 运维经验/配置细节 | 谨慎外发 |
| LEVEL 5 | LIID/IMSI/MSISDN等真实数据 | 绝对禁止外发 |

## 五、确认与授权

- 首次分析完成后，必须询问用户是否要入库
- 用户简短回复（"好的"/"OK"/"Description"）即视为授权
- 逐段更新时不需要重复询问，直接 patch

## 六、关联知识点

- `zte-li` — ZTLIG（Sinovatio）LI 网关运维
- `hw-li` — 华为 LI 全栈
- `li-system-ops` — LI 系统日常运维
- `etsi-lawful-intercept` — ETSI LI 标准体系
- `asn1-codec` — ASN.1 编解码

## 参考资料

- `references/utimaco-lims-rai-v16-1.md` — Utimaco RAI 协议快捷参考（已入库）
- `references/zte-cs-li-hi1-hi2-hi3.md` — ZTE CS LI 三接口规范参考（已入库）
- `references/ericsson-hi1-external-api.md` — Ericsson HI1 External API 参考（已入库）
- `references/ericsson-cxc1373777-r4a-vs-r6a.md` — Ericsson CXC1373777 R4A vs R6A 版本对比+API演进史（已入库）
- `references/ericsson-mss17a-pod-x2-ird.md` — Ericsson MSS17A POD (X2) IRD ASN.1 + RCEFILE1 格式快捷参考（已入库）
- `references/ericsson-mss17a-complete-document-set.md` — Ericsson MSS17A 完整文档集（含 X1/COD + X2/POD + X3/IWD + 对接经验）快捷参考（已入库）
- `references/ericsson-lims-workflow.md` — 爱立信LI-IMS ZTLIG工作流快捷参考（设控→IRI→语音→排障）
- `references/ericsson-soap-samples-2dot1.md` — Ericsson LI SOAP login + createWarrant 样本快捷参考（2dot1 版本，已入库）
- `references/ericsson-soap-samples-2dot1-complete.md` — Ericsson LI SOAP 完整生命周期样本集快捷参考（login + createWarrant + getWarrantList + modifyWarrant + deleteWarrant，type.__value CRUD 映射）
- `li/Ericsson/LIMS_Workflow_and_Maintenance.md` — 爱立信LI-IMS集成: ZTLIG工作流与运维
- `references/mavenir-ims-li-x1-x2-x3.md` — Mavenir IMS LI X1/X2/X3 接口包快捷参考（WSDL 操作、hi2-uag 结构、TargetType 枚举、现网参数）（设控→IRI→语音→排障全链路；⚠️ 爱立信场景专属，非通用项目运维）
- `references/sinovatio-dfx-dpi-protocol-id-pcaps.md` — Sinovatio DFX DPI 串接阻断 PCAP 验证分析参考（6 个 PCAP 的协议识别特征、HEX 偏移定位、常用 tcpdump 命令集）
