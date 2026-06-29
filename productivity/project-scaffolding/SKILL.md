---
name: project-scaffolding
description: "为新项目创建目录结构 — 必须先问用户项目类型，再按类型选择对应的目录模板"
---

# Project Scaffolding — 项目目录结构创建

## 核心规则

**创建任何项目目录前，必须先问用户项目类型。** 不同类型有完全不同的目录模板，不能强行套用。

## 触发条件

用户说以下内容时触发：
- "创建项目" / "建立项目" / "建项目"
- "迁移项目到 ~/projects" / "整理项目文件"
- "分类迁移" / "文件分类" / "归类"
- "帮我整理项目文件" / "把文件移到项目目录"
- "建立 xxx 项目目录结构"
- 用户提到散落的文件需要按项目分类存放

## 工作流

### 第 1 步：询问项目类型

```
必须问的问题：
1. 项目名称（中文/英文？）
2. 项目类型是？（LI/LIG / Web开发 / Python库 / 运维脚本 / 文档项目 / 协议分析/监控系统 / 其他）
3. 项目用途简述（几句话）
```

**不要**假设项目类型。即使名称看着像 LI 项目，也先确认。

### 第 2 步：按类型选择目录结构

#### 类型 A1: LI/LIG 合法监听项目（基础）

```
项目名/
├── README.md
├── 对接/     ← 各网元 X1/X2/X3 对接记录
├── 工勘/     ← 网元信息调查、IP/端口/协议确认
├── 巡检/     ← 日常巡检项、排障 checklist
├── 方案/     ← 技术方案、Meeting Minutes
├── 抓包/     ← PCAP 抓包文件及分析
└── 解码/     ← ASN.1 BER 解码参考 / 自定义规范
```

**注意：** 纯 LI/LIG 项目不含 `配置/` 目录，cfg 文件放在项目根目录即可。

**模板：** 创建 cfg/READEME.md 时参考 `templates/li-cfg-readme.md`

#### 类型 A2: LI 多层整合项目（ZTLIG 前端 + OWLS 后端 + 大数据平台）

当 LI 项目不止包含 ZTLIG 前端配置，还涉及 OWLS 后端分析 + 底层大数据平台时，使用此结构：

```
项目名/
├── README.md                   ← 项目全景说明（三层架构总览）
│
├── cfg/                        ← ZTLIG 配置文件（集中管理）
│   ├── *-ztlig.cfg             各运营商配置文件
│   └── README.md               配置参数速查
│
├── ztlig/                      ← ZTLIG 前端层
│   ├── 对接/   X1/X2/X3 对接记录
│   ├── 工勘/   网元信息调查、IP/端口/协议确认
│   ├── 巡检/   日常巡检项、排障 checklist
│   ├── 方案/   技术方案、Meeting Minutes
│   ├── 抓包/   PCAP 抓包文件及分析
│   └── 解码/   ASN.1 BER 解码参考
│
├── owls/                       ← OWLS 后端层
│   ├── architecture/   系统架构、模块划分
│   ├── dataflow/       数据流程（离线/实时）
│   ├── features/       业务功能（虚-实关联、三码补全、阻断）
│   ├── config/         OWLS 配置参考
│   ├── deployment/     部署/运维
│   └── troubleshooting/ 排错经验
│
├── bigdata/                    ← 大数据平台层
│   ├── hdfs/           HDFS 运维
│   ├── hbase/          HBase 表设计/运维
│   ├── kafka/          Kafka Topic 清单/Consumer 配置
│   ├── flink/          Flink Job 管理
│   ├── redis/          Redis 配置
│   └── mysql/          MySQL 库表结构
│
├── integration/                ← 跨层集成文档（关键！）
│   ├── topology.md     整体拓扑（三层物理拓扑 + 网元清单）
│   ├── kafka-topics.md Kafka Topic 映射表
│   ├── data-flow.md    数据端到端流图
│   └── api-guide.md    各层接口说明
│
└── docs/                       ← 项目通用文档
    ├── progress/       进度/甘特图
    ├── meeting/        会议纪要
    └── references/     参考文档索引（指向知识库）
```

**适用场景：**
- ZTLIG 使用 kafkaowls 模式（Kafka 对接 OWLS）
- 项目包含离线/实时 IRI 处理、虚-实关联等后端分析功能
- 底层依赖 Hadoop/HBase/Kafka/Flink 等大数据组件

**关键点：**
- cfg 文件从项目根目录移入 cfg/ 子目录集中管理（区别于纯 LI 项目）
- integration/ 是三层整合的核心，必须包含拓扑、Topic 映射、数据流
- 各层子目录内部可继续参考具体技术 skill 的组织方式

**参考案例：** 见 `references/a1-li-multi-layer-example.md` — A1 真实项目结构、Kafka Topic 映射表、数据端到端流

#### 类型 B: AI 数据分析 / 大模型应用项目

```
项目名/
├── README.md
├── data/                ← 数据集（原始/处理后）
├── notebooks/           ← Jupyter Notebooks 分析
├── scripts/             ← Python 脚本、数据处理 pipeline
├── models/              ← 模型文件 / 权重
├── docs/                ← 技术文档、方案
└── output/              ← 输出结果、报告、图表
```

#### 类型 C: AI 模型部署 / 推理服务项目

```
项目名/
├── README.md
├── src/                 ← 推理代码
├── config/              ← 部署配置（API key 放 .env）
├── docker/              ← Dockerfile / docker-compose
├── deploy/              ← K8s manifest / helm
├── tests/               ← 测试
└── docs/                ← 说明文档
```

#### 类型 D: AI Agent / 智能体应用项目

```
项目名/
├── README.md
├── agents/              ← Agent 定义
├── tools/               ← 工具函数
├── prompts/             ← 提示词模板
├── memory/              ← 记忆/上下文管理
├── workflows/           ← 工作流编排
├── config/
├── logs/
├── tests/
└── docs/
```

#### 类型 E: 大数据平台 (Hadoop/HBase/Kafka/Flink) 项目

```
项目名/
├── README.md
├── config/              ← 集群配置
├── scripts/             ← 运维脚本
├── sql/                 ← Hive SQL / 查询
├── jobs/                ← Flink/Spark job
├── alerts/              ← 告警规则
├── backup/              ← 备份策略
├── monitor/             ← 监控配置
└── docs/
```

#### 类型 F: MLOps / 模型训练项目

```
项目名/
├── README.md
├── pyproject.toml
├── data/
│   ├── raw/
│   ├── processed/
│   └── external/
├── notebooks/
├── src/
│   ├── features.py
│   ├── modeling/
│   │   ├── train.py
│   │   └── predict.py
│   └── config.py
├── models/              ← 训练产物
├── docker/
├── tests/
├── docs/
└── reports/
    └── figures/
```

#### 类型 G: Web/后端/API 开发项目

```
项目名/
├── README.md
├── .gitignore
├── docs/               ← 文档
├── src/                ← 源代码
├── tests/              ← 测试
├── config/             ← 配置文件
└── scripts/            ← 脚本（构建/部署/工具）
```

#### 类型 E1: 运维脚本项目

```
项目名/
├── README.md
├── scripts/            ← 脚本
├── templates/          ← 配置模板
└── docs/               ← 说明文档
```

#### 类型 F1: 纯文档/知识类项目

```
项目名/
├── README.md
└── docs/               ← 文档
```

#### 类型 H: 协议分析/监控系统项目 (Telecom Protocol Analysis / Monitoring System)

用于开发电信协议分析、信令监控、协议解码工具等系统的项目结构。特点：设计文档 + 多层解码器源码 + 测试 + 配置分离。

```
项目名/
├── README.md                   ← 项目介绍（支持接口、协议、流程总览）
├── 设计文档/                   ← 协议解析设计文档（章节化组织）
│   ├── index.md                ← 主页 / 目录
│   ├── 01-解析接口.md           ← 解析接口定义
│   ├── 02-缩略词表.md           ← 缩略词和术语表
│   ├── ...                     ← 按接口/协议/场景分章节
│   └── N5-架构场景.md          ← 架构场景（SA/NSA、漫游等）
├── 源码/                       ← 源代码（分层架构）
│   ├── core/                   ← 核心框架（配置/日志/解码器基类/会话关联）
│   ├── protocols/              ← 协议层解码器（如 ngap/nas/sbi/gtpv2c）
│   ├── services/               ← 服务层（接口级别的高层处理）
│   ├── decoder/                ← 编解码/加密工具（KDF/SUCI/GUTI映射/NEA）
│   └── utils/                  ← 工具函数（常量/TLV parse/hex dump）
├── 测试/                       ← 测试用例和测试数据
├── 配置/                       ← 系统配置文件（JSON/YAML 格式）
├── 文档/                       ← 参考文档和笔记
│   ├── 标准参考/                ← 协议标准索引（指向 3GPP TS）
│   └── notes/                  ← 开发笔记
└── stcms.py / main.py          ← CLI 入口
```

**适用场景：**
- 协议解码工具开发 (NGAP/NAS/HTTP2 SBI/GTPv2-C)
- 信令监控系统（多接口关联分析）
- 加密/鉴权流程解码器
- 多接口会话关联系统

**分层说明：**
- `core/` — 基础框架：Config、Logger、BaseDecoder、SessionCorrelator
- `protocols/` — 协议层：各原始协议的解码器（如 Nas5GmmDecoder、NgapDecoder）
- `services/` — 服务层：接口级别的高层处理（如 N8AmfUdmDecoder）
- `decoder/` — 编解码工具：KDF、加密算法、SUCI/GUTI 映射
- `utils/` — 通用工具：constants/TLV parser/hex dump 等
- `设计文档/` — 分章节组织，按接口编号命名（01-/02-/...）

**依赖安装：**
```bash
pip install pycryptodome  # NEA2 AES 加密
pip install scapy          # PCAP 解析（可选）
pip install snow3g zuc     # NEA1/NEA3（可选）
```

**参考案例：** `~/projects/STCMS/` — 5G 信令跟踪与协议解析系统，覆盖 N1/N2/N8/N10/N11/N12/N13/N14/N20/N26 共 10 个接口，16 章设计文档，5 层源码框架。

#### 类型 I: B2B 医药/化工网站项目

``` 
项目名/
├── README.md                       # 项目概述
├── docs/
│   ├── SKILL.md                    # SEO/运营策略
│   ├── *SOP*.docx                  # 上线SOP、操作手册
│   ├── *方案*.docx                 # 批量导入方案等
│   ├── references/
│   │   ├── *keywords*.md           # 产品关键词表
│   │   ├── *safety*.md             # YMYL安全过滤
│   │   └── technical-seo/          # SEO技术参考截图
│   └── screenshots/                # 后台管理界面截图
├── references/
│   └── competitive/                # 同行/竞品网站截图
├── personnel/                      # 项目团队成员资料
├── backup/                         # 旧版本备份
├── scripts/                        # 自动化脚本
└── src/                            # 源代码/模板
```

**适用场景：** B2B API/中间体/科研试剂供应商网站，内容驱动的运营型项目。
**参考项目：** `~/work-projects/pharma-website/`

#### 类型 J: Hermes Enterprise Skill Pack（Hermes 技能包）

用于将一组相关技能打包为可部署的企业级技能包。适用于运维套件、电信能力包、知识管理组件等场景。

```
pack-name/
├── README.md                   ← 技能包总览（用途、包含技能清单）
├── VERSION                     ← 语义版本号
├── INSTALL.md                  ← 安装/部署说明
├── CHANGELOG.md                ← 版本变更日志
│
├── skills/                     ← 技能定义（每个技能一个子目录）
│   ├── skill_a/
│   │   ├── skill.yaml          ← 元数据 + 工作流步骤
│   │   ├── prompt.md           ← 模型加载时的操作指引
│   │   └── examples.md         ← 使用场景/示例
│   ├── skill_b/
│   │   ├── skill.yaml
│   │   ├── prompt.md
│   │   └── examples.md
│   └── ...
│
├── prompts/                    ← 跨技能的操作参考卡片
│   ├── model-routing.md
│   ├── compression-thresholds.md
│   ├── emergency-response.md
│   └── ...
│
├── templates/                  ← 可复用的样板文件
│   ├── skill-template.yaml
│   ├── daily-report-template.md
│   └── ...
│
├── scripts/                    ← 自动化脚本（需可执行权限）
│   ├── healthcheck.sh
│   ├── backup.sh
│   └── ...
│
└── docs/                       ← 参考文档
    ├── architecture-overview.md
    ├── getting-started.md
    ├── faq.md
    ├── troubleshooting.md
    └── ...
```

**设计原则：**
- **每个技能 3 文件** — `skill.yaml`（元数据+工作流）+ `prompt.md`（操作指引）+ `examples.md`（使用示例）。三者缺一构成 stub（占位符）。
- **技能是扁平集合** — 每个技能自包含自己的 prompt 和示例，不依赖其他技能的文件，避免循环耦合。
- **prompts/ 是交叉引用层** — 存放影响多个技能的操作参考（压缩阈值、模型路由、应急响应），而非某个技能的专属 prompt。
- **脚本必须可执行** — `chmod +x` + shebang，可在 setup/healthcheck/backup 流程中被 Hermes 直接调用。
- **模板不属于技能** — `templates/` 是用户可复制的起点样板，不挂载到具体技能。

**适用场景：**
- 电信运维能力包（ZTLIG 对接 + 抓包分析 + PCAP 解码 + 知识入库）
- Hermes 自身配置管理和监控套件（session lifecycle + 模型路由 + 压缩 + 健康检查）
- 大数据运维技能套件（HDFS + Hive + HBase + Kafka + Greenplum 监控）

**参考案例：** `~/hermes-enterprise-pack/` — 11 个技能（9 完整 + 3 stub）+ 5 prompt + 5 template + 4 script + 6 doc 的 Hermes 企业级运维包。

#### 类型 Z: 其他 / 用户自定义

先问用户想要什么结构，按需求创建。

## 项目就绪检查清单（从代码到可发布项目）

用户问"作为软件项目了吗"或"这算正经项目了吗"时触发。代码能跑不等于项目就绪。

### 检查项

```
必备:
  ✅ 清理冗余文件          (遗留 CLI 入口、__pycache__)
  ✅ .gitignore            (Python/IDE/OS 标准规则)
  ✅ LICENSE                (MIT/Apache/GPL 选一个)
  ✅ pyproject.toml         (现代标准，含 pytest 配置)
  ✅ README.md              (安装→使用→API→开发完整链路)
  ✅ git init + 首次提交
  ✅ 测试框架               (pytest 优先)
  ✅ CI 配置                (GitHub Actions / GitLab CI)
  
推荐:
  - 空字典占位符填充         (如 VENDOR_AVP_DICT / EXTENDED_AVP_DICT)
  - setup.py extras 约束    (optional-dependencies 分组)
  - type hints 一致性检查
  - CLI 命令 + python -m 双入口
```

### 验收标准

```bash
# 1. 纯净环境可装
pip install -e . && python -c "import package; print(package.__version__)"

# 2. 所有测试通过
pytest -v

# 3. CLI 可用
package-name --help

# 4. git 状态干净
git status  # should show nothing

# 5. 无 __pycache__ 残留
git clean -nd
```

### 参考案例

`diameter-decoder-project` — 初始只有代码和 19 个自制测试，补齐后成为 15 文件/3080 行/29 pytest/CI 的完整项目。

### 第 3 步：创建 + 确认

1. `mkdir -p` 创建目录
2. 写一个简短 README.md 说明项目用途
3. 显示最终结构给用户确认
4. 如有 `.gitignore` 等文件，一并创建

### 第 3.5 步：学习并整合已有资料（可选）

项目结构创建后，用户可能要求从 `/tmp/`、`~/knowledge/` 或其他位置**学习已有资料并整合到项目中**。

流程：
1. `find` 查找源文件（通常用户会直接指定路径）
2. 读取文件内容
3. 判断内容归属哪一层（ztlig/owls/bigdata/integration/docs）
4. 写入结构化文档到对应目录
5. 可选：同时写入知识库（`~/knowledge/` 下对应分类目录）

**常见场景：**
- `/tmp/xxx.md` — 临时笔记/技术问答整理 → `integration/` 或 `ztlig/方案/`
- `~/knowledge/` 中的已有文档 → 在 `docs/references/` 建立索引链接
- 排错经验 → `owls/troubleshooting/` 或 `ztlig/巡检/`

**特别注意：**
- 跨层内容（如同步逻辑涉及三层）优先放 `integration/`
- OWLS 和大数据层文档不要放在 `ztlig/` 下

### 第 4 步：查询参考文件

遇到不确定的类型时，查阅：

- `~/projects/_references/project-structure-reference.md` — 下载自 GitHub/Google 的行业最佳实践（8 类模板）

## 已有项目参考

| 项目 | 类型 | 目录结构 |
|------|------|---------|
| A1 (MTN/SU/ZAIN) | LI 多层整合 | cfg/ztlig/owls/bigdata/integration |
| Indonesia-SIOCC | AI 数据分析 | data/notebooks/scripts/models/docs/output |
| ETSI-ASN1-Assistant | Web 开发 | src/docs/tests |
| pharma-website | B2B 医药/化工网站 | docs/references/screenshots/personnel/backup/scripts/src |
| github-workspace | 开发项目 | src |
| STCMS | 协议分析/监控系统 | 设计文档/源码(core/protocols/services/decoder/utils)/测试/配置/文档 |

## 文件归类和迁移（根目录整理到项目目录）

当用户说"分类迁移"或用户根目录下散落大量文件时，按以下流程操作：

### 工作流

#### 第 1 步：全量扫描
```
ls -la ~/                          # 列出根目录所有文件/目录
ls ~/work-projects/                # 查看现有工作项目
ls ~/personal-projects/            # 查看现有生活项目
```

排除系统目录（`.*`、Desktop/Documents/Downloads/Music/Pictures/Public/Templates/Videos、knowledge、bin/、scripts/、config/、.hermes/）。

#### 第 2 步：按文件内容/名称分类

按项目归属逐一分析。参考 memory 中已有的项目信息来判断归属。

**用户的目录约定（请先问用户是否有自己的约定）：**
- `~/work-projects/` — 工作用项目（默认已存在：A1、Indonesia-SIOCC、pharma-website、ETSI-ASN1-Assistant 等）
- `~/personal-projects/` — 生活/个人项目（默认已存在：hermes-agent、second-brain、diudiu、BACKUP）
- `~/work-projects/_archive/` — 未分类/临时归档

#### 第 3 步：提交分类方案给用户确认

给出表格化的分类方案，让用户确认后再执行。

#### 第 4 步：批量执行迁移

用 `mv` 批量操作，同类文件一批完成。注意：
- 已有项目目录的文件直接移入对应目录
- 无归属的文件统一移入 `_archive/`
- 同名目录合并时，用 `cp -rn source/* target/` 无损合并后删除源目录

#### 第 5 步：验证

```
ls -1 ~/work-projects/
ls -1 ~/personal-projects/
ls ~/work-projects/_archive/ | wc -l
```

确认根目录已清理干净。

### 目录合并（同名目录冲突）

当目标目录已存在同名目录并有不同内容时：
1. `diff -rq dirA dirB` 对比差异
2. `cp -rn dirA/* dirB/` 无损合并（-n: 不覆盖已有文件）
3. `rm -rf dirA` 删除源目录

### 重要的约定

- 即使项目名称看着像 LI/工作类，也要先问用户，不要默认假设分类
- 不要移动用户的家目录下的隐藏文件（`.*`）和系统目录
- 迁移完成后**必须验证**根目录清理效果

## Pitfalls

- **不要按项目名称猜测类型** — SIOCC 看起来像 LI 项目名，实际是 AI 项目
- **不要在非 LI 项目中使用 LI 目录结构** — `对接/工勘/巡检/方案/抓包/解码` 只适用于 LI/LIG
- **LI 项目不含 `配置/` 目录**
- **不要从其他项目复制文件到新项目** — 尤其是带 LI 内容的文件（cfg/解码/抓包）
- **不要假设项目的内容** — 即使知道项目类型，也要先看实际文件再建目录结构（避免放入不存在的文档子目录）
- **建完结构立刻确认** — 显示目录树给用户检查，避免批量创建不合适的目录后再删除
- **区分工作/生活项目目录** — 该用户约定 `~/work-projects/` = 工作项目，`~/personal-projects/` = 生活/个人项目。工作项目包括 A1、Indonesia-SIOCC、pharma-website、ETSI-ASN1-Assistant 等；生活项目包括 hermes-agent、second-brain、diudiu。文件分类时先问用户是否有类似约定再执行
