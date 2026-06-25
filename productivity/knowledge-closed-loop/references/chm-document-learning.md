# CHM 文档学习入库流程

## 概述

CHM（Compiled HTML Help）是微软编译的帮助文档格式，华为LI/ETSI等技术文档常以CHM格式分发。本文档记录了从CHM文件中提取知识并入库的完整工作流。

## CHM 提取工具

### 方案一：7z（推荐，/usr/bin/7z 预装）

```bash
# 解压单个CHM
7z x 文档.chm -o输出目录 -y

# 批量解压所有CHM
cd /tmp/chm_extract
for f in /path/to/*.chm; do
    7z x "$f" -o"$(basename "$f" .chm)" -y
done
```

**优势**：`/usr/bin/7z` 预装在Ubuntu系统中，无需额外安装。
**原理**：CHM本质上是LZX压缩的HTML归档，7z原生支持。
**验证命令**：`which 7z` 确认可用。

### 方案二：archmage（pip安装，备选）

```bash
pip install archmage --break-system-packages
```

**注意**：archmage依赖pychm，后者需要编译libchm C扩展，在某些环境中可能构建失败。当archmage不可用时，7z是可靠的替代方案。

## 中文CHM编码处理（关键！）

华为/中兴等国内厂商的CHM文档使用 **GBK/GB2312** 编码，**不是** UTF-8。必须用 GBK 解码，否则中文内容显示为乱码。

### Python 提取核心文本模板

```python
import re, subprocess, os
from pathlib import Path

def extract_chm_text(chm_path, out_dir):
    """解压CHM并返回结构化摘要"""
    os.makedirs(out_dir, exist_ok=True)
    subprocess.run(["7z", "x", chm_path, f"-o{out_dir}", "-y"], 
                   capture_output=True, timeout=120)
    
    # 1) 读 .hhc 目录（GBK解码）
    hhc_files = list(Path(out_dir).rglob("*.hhc"))
    toc_topics = []
    if hhc_files:
        toc_raw = open(hhc_files[0], "rb").read()
        toc_text = toc_raw.decode('gbk', errors='ignore')
        toc_topics = re.findall(r'<param name="Name" value="([^"]+)"', toc_text)
    
    # 2) 读 HTML 正文（按文件大小降序，大文件截断）
    htmls = [(f, os.path.getsize(f)) for f in Path(out_dir).rglob("*.[hH][tT][mM]*")]
    htmls.sort(key=lambda x: -x[1])
    
    pages = []
    for hf, sz in htmls[:8]:
        raw = open(hf, "rb").read(min(sz, 80000))
        text = raw.decode('gbk', errors='ignore')
        text_clean = re.sub(r'<[^>]+>', ' ', text)
        text_clean = re.sub(r'\s+', ' ', text_clean).strip()
        if len(text_clean) > 50:
            pages.append(text_clean[:500])
    
    return {"toc": toc_topics[:40], "pages": pages[:5]}
```

### 编码注意事项表

| 注意事项 | 说明 |
|---------|------|
| **GBK 优先** | 不要用 UTF-8 直接读，中文会变成 `&#x` 或 `鍔` 等乱码 |
| **忽略解码错误** | `errors='ignore'` 可跳过 CHM 中的非文本数据 |
| **超大文件截断** | 307MB的ME60产品文档有33014个HTML，只读 top-8 个大文件即可 |
| **charset检测** | 部分HTML头部有 `<meta charset=gb2312>` 可辅助确认编码 |

## CHM 解压后目录结构

解压后包含两类文件：

| 类型 | 文件 | 说明 |
|------|------|------|
| **系统文件** | `$FIftiMain`, `$OBJINST`, `#IDXHDR`, `#ITBITS` 等 | CHM内部索引和元数据，可忽略 |
| **内容文件** | `.hhc`（目录）、`.hhk`（索引）、`.htm`/`.html`（正文） | 需要读取的知识内容 |
| **资源目录** | `public_sys-resources/`, `figure/` 等 | CSS/图片资源 |

## 学习流程

### 第一步：解压与结构探查

```bash
7z x /path/to/file.chm -o/tmp/chm_extract/name -y
ls -la /tmp/chm_extract/name/
```

### 第二步：读取目录文件 (.hhc)

`.hhc` 文件是CHM的目录（TOC），类似HTML嵌套列表，包含章节名和对应的HTML文件名。

### 第三步：阅读核心HTML

优先阅读：
- **概述/介绍**章节 — 文档定位
- **架构/原理**章节 — 核心概念
- **配置/命令**章节 — 操作细节
- **告警/故障排查**章节 — 运维参考

### 第四步：多文档并行学习

对多个CHM使用 `delegate_task` 子代理并行处理，每个子代理独立阅读 `.hhc` + 关键HTML，返回结构化摘要。

### 第五步：汇总与入库

- 所有文档摘要合并为结构化知识笔记
- 提取文档间关联关系（标准层/产品层/搭建层等三层架构）
- 写入知识库对应分类目录
- 执行 `enzyme refresh` 更新语义索引

## 真实案例：华为LI技术文档

详见 `references/li-knowledge-three-layer-architecture.md`。

2026-06-17 处理的7个CHM文档：

| 文件名 | 分类 | 文件数 | 核心内容 |
|--------|------|--------|---------|
| 57_Lawful_Interception_ETSI.chm | 标准层 | 808 | ETSI LI标准、X1/X2/X3接口 |
| EPC信令协议分析.chm | 标准层 | 1979 | EPC/NAS/S1AP信令全流程 |
| VoLTE信令分析手册.chm | 标准层 | 3823 | VoLTE/IMS/SIP信令 |
| 监听手册.chm | 产品层 | 293 | 华为LI内部开发运维手册 |
| CGP 维护宝典V3.1.3.chm | 产品层 | 454 | CGP平台故障案例库 |
| LI_ETSI_VoBB_RCSe_VoLTE.chm | 搭建层 | 213 | ETSI标准监听系统搭建 |
| LI_LICI_VoLTE_MCCP_CH.chm | 搭建层 | 384 | 中国特通监听系统搭建 |

## 笔记结构化模板

### 索引笔记格式

当处理多个相关CHM文档时，创建一篇索引笔记作为入口：

```markdown
---
tags:
  - telecom/lawful_interception
  - huawei
  - index
created: YYYY-MM-DD
---

# 文档标题索引

## 文档全景

| 层级 | 文档 | 内容 |
|------|------|------|
| **标准层** | [[文档A]] | 简述 |
| **产品层** | [[文档B]] | 简述 |
| **搭建层** | [[文档C]] | 简述 |

## 文档间关系

ASCII关系图（如三层架构图）

## 核心概念速查

| 概念 | 说明 |
|------|------|
| 关键术语1 | 定义 |
| 关键术语2 | 定义 |

## 相关链接

- [[已有相关知识笔记]]
```

### 单篇知识笔记格式

```markdown
---
tags:
  - telecom/lawful_interception
  - huawei
  - [场景标签]
created: YYYY-MM-DD
aliases:
  - 别名1
  - 别名2
---

# 标题

> 概述段落

## 核心章节

### 1. 架构/原理

| 组件 | 功能 | 说明 |
|------|------|------|
| 组件A | 功能A | 说明A |

### 2. 配置/命令

| 命令 | 用途 |
|------|------|
| `CMD1` | 用途1 |
| `CMD2` | 用途2 |

### 3. 流程/协议

接口、消息表、流程图等。

## 关联文档

- [[文档A]] — 关联说明
- [[文档B]] — 关联说明
```

### 关键原则

| 原则 | 说明 |
|------|------|
| **三层架构归类** | 标准层/产品层/搭建层，每层之间用 wikilink 关联 |
| **表格优先** | 架构表、命令对照表、协议接口表比纯文本段落更可读 |
| **tags 分层** | 一级标签如 `telecom/lawful_interception`，二级标签如 `huawei`/`etsi`/`lici` |
| **aliases** | 设置别名（原文标题）便于搜索 |
| **双向链接** | 每篇末尾的「关联文档」用 wikilinks 双向连接 |
| **索引入口** | 多文档集合必须有一篇索引笔记，含全景表+关系图+速查 |

## 验证清单

- [ ] 文件写入后，确认从 Obsidian vault 路径可访问
- [ ] 检查 vault 的 symlink 结构是否覆盖目标目录
- [ ] `enzyme refresh` 执行成功，`enzyme status` 显示新文件数 > 0
- [ ] 索引笔记中的 wikilinks 有效（目标笔记已创建）
- [ ] 原 CHM 源文件路径可记录在索引笔记中供今后查阅

## 注意事项

- CHM可能包含大量HTML文件（最大3823个），不要逐一阅读
- 优先阅读 `.hhc` 目录文件和概述类HTML
- 系统文件（`$`和`#`开头）无阅读价值
- 7z解压无需sudo，用户权限即可
- Obsidian MCP插件可能偶发连接失败，写文件优先走直接文件系统写（通过 vault symlink），再试 MCP 工具
