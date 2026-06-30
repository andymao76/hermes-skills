---
name: knowledge-privacy-policy
description: Hermes Agent 知识分层隔离策略 — 明确哪些知识可以发给在线 LLM，哪些必须本地隔离。适用于电信 LI、客户项目、密码密钥等敏感场景。
---

# 知识分层隔离策略

## 核心理念

**本地存储 ≠ 本地推理。** 知识文件在本地磁盘上，不等于它们只在本地处理 —— 只要调用在线 LLM API，RAG 检索到的知识片段就会作为 Prompt 发送出去。

## 速查数据流

```
公开技能库
      ↓
允许 RAG 发送给 LLM

项目资料库
      ↓
脱敏后发送

客户资料库
      ↓
禁止发送

密码/API Key
      ↓
永不进入知识库
```

## 五级数据分类体系

知识库物理目录结构已按安全级别分区，每个目录配有 `README.md` 说明规则。

```
knowledge/
├── public/          ← LEVEL 1: 公开知识  允许发送
│   ├── README.md          分类规则说明
│   ├── bigdata/    → ../bigdata/        (symlink)
│   ├── hermes/     → ../hermes/         (symlink)
│   ├── kafka/      → ../kafka/          (symlink)
│   ├── flink/      → ../flink/          (symlink)
│   ├── 3gpp-*/     → ../3gpp-*/         (symlink)
│   ├── skills/     → ../skills/         (symlink)
│   ├── research/   → ../research/       (symlink)
│   └── ... 共 31 个相对路径 symlink → 实际目录
├── internal/        ← LEVEL 2: 内部经验  脱敏后发送
├── customers/       ← LEVEL 3: 客户数据  禁止发送
├── secrets/         ← LEVEL 4: 敏感信息  绝对禁止
├── li/              ← LEVEL 5: LI数据   绝对禁止（最高级, 103 文件）
│   ├── lawful_interception/  HW/ZTE LI 文档
│   ├── a1-project/           A1 项目运维
│   ├── international_project/ 国际项目含 LI 内容
│   │   ├── baidu-netdisk-import/  百度网盘导入的 LI 文档
│   │   └── imported/              7z+pandoc 批量从 CHM 提取的文档（ME60/GGSN/GPRS/VoLTE/CSFB/Wireshark等，~84MB/18文件，LEVEL5）
├── _system/         ← 系统配置，不进 Prompt
│   └── security/         安全治理文档 + 审计报告归档
│       ├── llm_data_governance.skill.md  数据治理规则
│       └── audit-reports/security-audit-YYYY-MM-DD.md
│
├── bigdata/         ← LEVEL 1（原始位置，public/ 已有 symlink）
├── telecom/         ← LEVEL 1: 公开通信技术（已拆分，LI 内容已迁至 li/）
│   ├── (公开通信技术)      ← LEVEL 1
│   └── (LI 内容已全部迁出)  ← 见 li/{lawful_interception,a1-project,international_project}
├── hermes/          ← LEVEL 1
├── kafka/           ← LEVEL 1
├── hi2/             ← LEVEL 5 LI 数据
├── projects/        ← LEVEL 3-5 混合
├── ...（其他保留在原位的 LEVEL 1 目录）
```

**public/ 设计原理：** 通过 31 个相对路径 symlink 将散布的 LEVEL 1 目录统一暴露在 `public/` 下，作为 RAG 检索的唯一 LEVEL 1 入口。原始目录保留原位不动，兼容旧引用路径。

### LEVEL 1 — 公开知识（允许发送）
- 公开标准规范：3GPP / ETSI / RFC 文档内容
- 通用技术经验：HDFS 排障 / Kafka 调优 / Flink Checkpoint 诊断等
- 开源/通用技能文档：Linux 运维 / Docker / MCP 等
- 个人学习笔记（不含项目具体信息）

**风险：🟢 低** — 这些本身就是公开内容或通用经验
**RAG 规则：** ✅ 允许检索进入 Prompt
**物理目录：** `knowledge/public/`, `knowledge/telecom/`, `knowledge/bigdata/`, `knowledge/hermes/`

### LEVEL 2 — 内部经验（脱敏后发送）
- 运维经验、故障处理记录（不含具体客户名）
- 项目技术总结
- 内部最佳实践、调优方案
- 日常巡检记录、日报中的技术经验

**脱敏规则：**
- 客户名称 → `Customer_A`, `Customer_B`
- 项目名称 → `Project_X`, `Project_Y`
- 国别信息 → `Region_1`, `Region_2`
- 内部系统代号 → `System_Alpha`
- 具体 IP →  `x.x.x.x`

**风险：🟡 中**
**RAG 规则：** ⚠️ 谨慎检索，发送前脱敏
**物理目录：** `knowledge/internal/`

### LEVEL 3 — 企业机密（禁止发送）
- 客户名称、联系人、合同信息
- 商务报价、招投标文档
- 客户网络拓扑、实施方案（含客户信息）
- 客户会议纪要

**风险：🔴 高**
**RAG 规则：** ❌ 禁止检索进入 Prompt
**物理目录：** `knowledge/customers/`

### LEVEL 4 — 敏感数据（绝对禁止）
- 密码、Token、API Key
- .env / config.yaml 配置备份
- 云平台凭据、SSH 私钥、VPN 密钥
- 数据库密码、内网地址

**风险：🔥 CRITICAL**
**RAG 规则：** ❌ 绝对禁止
**物理目录：** `knowledge/secrets/`

### LEVEL 5 — LI 数据（最高等级）
- ETSI HI1/HI2/HI3 接口数据
- X1/X2/X3 监听接口样例
- LIID、CC Data、IRI Data
- IMSI/IMEI/MSISDN 等用户标识
- 真实手机号、身份证号
- HW/ZTE LI 运维文档（`lawful_interception/`）
- A1 项目全套运维手册（`a1-project/`）
- 国际项目含 LI 组网/工勘内容（`international_project/`）
- 百度网盘导入的 LI 文档（`baidu-netdisk-import/`）

**风险：🔴 TOP SECRET**
**RAG 规则：** ❌ 绝对禁止，待私有 LLM 部署后再导入
**物理目录：** `knowledge/li/`（含 `lawful_interception/`, `a1-project/`, `international_project/`, `baidu-netdisk-import/` 子目录）

### 厂家文档隔离（跨级别规则 — 依 RULE20 优先级）

以下规则按 **RULE20 最高原则**执行，覆盖旧版全禁止策略：

| 厂家/领域 | 在线 LLM 处理？ | 规则依据 |
|-----------|:--------------:|---------|
| **ZTLIG / Sinovatio(中新赛克)** | ❌ 禁止 | 等本地 LLM 建立后处理 |
| **A1 项目** | ❌ 禁止 | 全程本地处理 |
| **LI 协议概念/架构** | ✅ 用 **OpenLI** 开源替代方案后可在线 | LI 相关知识替换为 OpenLI 对应概念 |
| **HW(华为) 公开信息** | ✅ 可在线 | 仅限公开渠道可查的资料 |
| **ZTE(中兴) 公开信息** | ✅ 可在线 | 仅限公开渠道可查的资料 |
| **Ericsson(爱立信) 公开信息** | ✅ 可在线 | 仅限公开渠道可查的资料 |
| **NSN(诺基亚西门子) 公开信息** | ✅ 可在线 | 仅限公开渠道可查的资料 |
| **OWLS / SICMS / SECPASS** | ❌ 禁止 | 等本地 LLM 建立后处理 |

**注意：** 旧版 RULE6 的全禁止策略已被 RULE20 覆盖/细化。如果 RULE6 和 RULE20 冲突，以 RULE20 为准。

> 详细决策流程见 `references/rule20-decision-tree.md`

### 危险信号（自动阻断规则）

当发现以下内容在输出中时，立即中止发送：
- `password=` / `token=` / `secret=` / `api_key=`
- `-----BEGIN OPENSSH PRIVATE KEY-----`
- `IMSI` / `IMEI` / `MSISDN` / `LIID`
- 真实手机号模式（连续 11 位数字）

## 本地源码安全隔离（LEVEL 6）

### 覆盖范围

以下本地项目目录中的**所有源文件**（含 .py/.asn/.cfg/.json/.yaml/.xml 等）属于最高安全等级：

| 项目目录 | 内容说明 | 风险等级 |
|---------|---------|---------|
| `~/work-projects/ETSI-ASN1-Assistant/` | HI2 Operations ASN.1 编解码实现、X2 接口定义 | 🔴 TOP SECRET |
| **`~/work-projects/A1/`** | ZTLIG 配置（Sinovatio LI 网关） | 🔴 TOP SECRET |
| **`~/projects/A1/202606/`** | ZTLIG 部署包、现场配置、二进制分析产物 | 🔴 TOP SECRET |
| `~/work-projects/_archive/telecom-pack/` | 华为/ZTE LI 字典、NGAP/NAS/GTP/PFCP 消息库 | 🔴 TOP SECRET |
| `~/myprogram/` 及其他 LI 相关项目 | 尚未识别的 LI 领域源码 | 🔴 TOP SECRET |

### 核心禁令

- ❌ **禁止** 将上述目录下的任何源码内容发送到 Web 搜索引擎
- ❌ **禁止** 将上述目录下的任何源码内容发送到在线 LLM API（DeepSeek / SiliconFlow / OpenAI / Anthropic 等）
- ❌ **禁止** 使用 web_search / web_extract / browser 工具搜索或获取与这些源码相关的实现细节
- ❌ **禁止** 将二进制分析结果（函数名、线程名、符号表、模块拓扑、进程架构等通过 `nm`/`strings`/`file`/`ldd` 获取的信息）发送到在线 LLM API。这些符号虽在二进制中公开可读，但组合起来可以还原产品内部架构，属于厂商保密信息。
- ✅ **仅允许** 本地文件操作：read_file / search_files / patch / write_file（用于本地编辑）
- ✅ **仅允许** 本地终端操作：terminal（用于本地编译/测试/运行/二进制分析）

### 本地工具白名单（无需联网即可完成的 LI 分析）

以下工具可安全在本地使用，结果不应外发：
- `nm` / `strings` / `file` / `ldd` — 二进制分析
- `readelf` / `objdump` — ELF 结构分析
- `grep` / `search_files` — 文本搜索
- `diff` — 配置对比
- `gdb` — 调试（二进制已含 debug_info 未 strip）
- `tcpdump` / `Wireshark` — 抓包分析（限于本地或内网流量）

### 例外规则

- 需要分析/修改/调试这些源码时，先问用户"是否需要处理这些 LI 领域源码"并**获得明确许可**
- 用户明确说"可以分析"后，只在本地进行 read_file / search_files 操作，不调用任何在线工具
- 用户说"帮我操作"时，可直接执行本地文件操作

### 项目目录扩展机制

如果新建了 LI 相关项目目录，应手动添加到上述覆盖范围表中。怀疑某目录包含敏感源码时，先问用户确认。

> 参考文件 `references/source-code-scenarios.md` 提供了详细的场景化决策指南，覆盖"什么时候需要先问用户"、"已确认后的操作限制"、"例外场景"等。

## 文档作者名处理规则

| 文档类型 | 处理方式 |
|---------|---------|
| LI/项目敏感文档中的作者名 | 属第三层，不进 Prompt（这些文档本身不应被 RAG 检索发送） |
| 公开技术文档（3GPP/ETSI/HDFS等）中的作者名 | 作为原文元数据，可随 RAG 发送 |
| 个人/宠物文件中的宠主名 | 替换为 `andym`，保留原文完整性 |
| **原则：不修改源文件的作者署名行** | 仅在 RAG 检索时按上述规则过滤 |

## Hermes 中的数据流路径

```
知识库 (knowledge/)
  ↓
RAG 检索（相关段落 1000-5000 字）
  ↓
拼接到 Prompt
  ↓
发送给在线 LLM API (DeepSeek / SiliconFlow / OpenRouter 等)
  ↓
模型回答
```


**关键结论：** DeepSeek 不会因为喂了 1000 份 Skill 就"学会"你的知识变成新模型。但它每次 API 调用时**会临时读取**这些内容来回答问题。模型服务商理论上可以接触到这些 Prompt。

## API 政策速查

| 平台 | API 数据用于训练？ | 备注 |
|------|-----------------|------|
| OpenAI API | ❌ 不用于训练 | 除非主动加入数据共享计划 |
| Anthropic Claude API | ❌ 不用于训练 | |
| DeepSeek API | ❌ 不用于训练 | 需关注政策变更 |
| SiliconFlow API | ❌ 不用于训练 | 国内厂商需额外注意合规 |
| OpenRouter | — 仅做转发 | 最终模型各有规则 |
| 网页版/App 对话 | ✅ 可能用于训练 | 与 API 渠道分离 |

## 自动化安全审计

每 2 天自动生成安全审计报告，扫描目录隔离违规、敏感词泄漏、RAG 索引风险。

| 组件 | 路径/命令 |
|------|----------|
| 治理规则 | `knowledge/_system/security/llm_data_governance.skill.md` |
| 审计脚本 | `~/.hermes/scripts/security-audit.py` |
| Cron 任务 | `安全审计报告` (每 2 天, job_id: `f2b601b831fe`) |
| 报告归档 | `knowledge/_system/security/audit-reports/security-audit-YYYY-MM-DD.md` |

### 报告模块（4 个）

1. **目录隔离检查** — 确认 LEVEL 1 目录不含 LEVEL 5 内容残留
2. **敏感词扫描** — LEVEL 1 目录内扫描 IMSI/MSISDN/密码/手机号等（含误报过滤）
3. **外部 LLM Prompt 风险统计** — 索引路径中是否含 customers/li/secrets
4. **高危文件迁移建议** — 发现敏感词自动建议迁移到对应目录

### 误报过滤

审计脚本内置多层过滤：
- 3GPP/ETSI 标准文件（TS_24/TS_23/Diameter/GTP_PFCP）跳过 IMSI/MSISDN 字段名扫描
- media_id/UUID 中的 hex 数字跳过 PHONE_11
- 测试号码（46000+123****7890）跳过 IMSI_RAW
- Markdown 图像尺寸表达式（width=/height=/in}）跳过 IMSI_RAW
- 详见 `references/security-audit-setup.md`

### 手动触发

```bash
# 手动执行审计
python3 ~/.hermes/scripts/security-audit.py
```

### 扫描范围
审计脚本自动扫描以下 LEVEL 1 目录（包含百度网盘导入目录）：
`public/`, `telecom/`, `bigdata/`, `linux/`, `hermes/`, `ai/`, `flink/`, `kafka/`, `hadoop/`, `hbase/`, `greenplum/`, `wireshark/`, `ima-articles/`, `ima-qa/`, `baidu-netdisk/`, `articles_baidu/`

如果确实需要"完全不外传"，只有两种方案：

### 方案 A：本地模型
- Ollama / vLLM / LM Studio
- 知识本地、推理本地
- 数据完全不出设备

### 方案 B：企业私有部署
- DeepSeek-R1 / Qwen3 / Llama 系列
- 部署在公司机房或私有云

## 用户姓名/PII 处理规则

**除非用户明确要求，真实姓名不得出现在任何系统 Profile / Memory / Skill / 知识库元数据中。**

### 替代标识
- 称呼用户：**「用户」** 或 **「andym」**
- 在 User Profile / Memory 中：只保留领域描述（如"LI 全栈专家"），不保留真实姓名
- RULE 规则编号：RULE1、RULE5、RULE6 等，使用连续编号，空缺序号留待后续补充

### 已知姓名泄漏向量（需要主动检查）

| 泄漏点 | 风险等级 | 说明 |
|--------|---------|------|
| 知识库文档作者/拟制人元数据 | 🟡 中 | 文档本身的作者行，RAG 检索会进 Prompt |
| User Profile / Memory | 🔴 高 | 每轮对话都发给 LLM |
| Skill 名称或描述文字 | 🔴 高 | 通过 skill_view() 注入提示词 |
| 会话历史记录 (session-transcript.jsonl) | 🟢 低 | 不会被在线 LLM 看到 |
| 系统日志 (agent.log) | 🟢 低 | 不会被发送到在线 LLM |
| 缓存文件名 (cache/documents/xxx.pdf) | 🟢 低 | 仅在本地存储 |
| 知识引用文件 (references/ 下的作者标注) | 🟡 中 | 通过 skill_view() 可能进上下文 |

**清理原则：** 只处理当前和未来会进入 LLM Prompt 的内容（Profile / Memory / Skill / 知识库文档元数据）。历史会话记录和日志文件保持原样。

### 操作步骤
1. 用 `search_files` 搜索 `.hermes` 和 `knowledge/` 下的真实姓名
2. 判断结果属于哪个层级（Profile → 立即清理 / 知识库文档元数据 → 可保留原文）
3. 更新 User Profile 和 Memory 中的姓名引用
4. 添加 RULE 规则到 User Profile

---

## RULE 规则体系

在 User Profile 中以 `RULE<N>: <规则内容>` 格式存储。当前规则编号：

| 编号 | 内容 | 场景 |
|------|------|------|
| RULE1 | 工作/项目问题先查本地知识库、技能库、笔记，无结果再上网搜 | 查询优先级 |
| RULE5 | 网上搜索结果必须标注出处(URL/文章名/来源)；维基百科优先用英文版 | 信息检索 |
| RULE6 | 知识隔离：公开技术可发LLM。RULE20 覆盖/细化了本规则的厂家限制（见 RULE20）。二进制符号名(nm/strings)、线程名、模块拓扑、现场配置(ztlig.cfg)等分析结果仍属于 ZTLIG/Sinovatio 禁发范围。作者名保留原文不变。 | 数据安全 |
| RULE7 | 每次启动Hermes时，必须先显示所有RULE规则列表和详细说明 | 启动自检 |
| RULE8 | 网上搜索来源务必标注出处（URL/来源/文章名）供人工核验 | 信息检索 |
| **RULE9** | **源码安全隔离：本地 `~/work-projects/ETSI-ASN1-Assistant/`、`~/work-projects/A1/` 等项目中的 LI 领域源码（含 HI/HI2/HI3/X1/X2/X3 编解码算法实现）严格禁止发送到 Web 搜索引擎或在线 LLM 处理。仅限本地文件/终端操作。** | **数据安全** |
| **RULE10** | **外部 LLM 前必须遵守 `knowledge/_system/security/llm_data_governance.skill.md`。每日 08:30 自动执行安全审计（security-audit.py），扫描知识库目录隔离、敏感词泄漏，报告留存最近 30 份。** | **审计治理** |
| RULE11 | **百度网盘下载的文档（`baidu-netdisk/`、`articles_baidu/`）需经安全审计分类：含 LI/项目文档 → `li/`，客户数据 → `customers/`，密码密钥 → `secrets/`。分类完成前不得用于 RAG 检索。** | **数据安全** |
| **RULE20** | **⚠️ 最高原则 — 知识处理路由规则：LI 内容→用 OpenLI 相关知识替代可在在线处理；HW/ZTE/Ericsson 公开信息→可在在线处理；ZTLIG/Sinovatio→禁止在线 LLM，等本地 LLM 建立后处理；A1 项目→全程本地处理。此规则优先级高于其他所有 **RULE 规则。** | **数据安全** |

**当前状态：** 2026-06-17 通过 31 个相对路径 symlink（`ln -sfn ../<dirname> public/<dirname>`）将散布的 LEVEL 1 目录统一暴露在 `public/` 下，作为 RAG 检索的统一 LEVEL 1 入口。酶素索引自动跟随 symlink。

**维护规则：** RULE 编号不重排（已删除的编号空缺），新规则追加最大序号+1。

**已知关联文件：** `references/env-source-pitfall.md`（`.env` source 陷阱）、`references/rule20-decision-tree.md`（RULE20 决策树）、`references/rule-system-maintenance.md`（RULE 系统维护：存储位置、安全重命名步骤、陷阱清单）

```yaml
hooks:
  on_session_start:
    - command: "~/.hermes/skills/knowledge-privacy-policy/scripts/rule-rules-display.sh"
      timeout: 5
hooks_auto_accept: true   # 非交互环境需此选项
```

**生效验证：**
- Gateway 模式：`on_session_start` hook 触发脚本，将规则打印到日志
- CLI 模式：`on_session_start` hook 无法通过 stdout 注入上下文，仍需 Agent 在新会话第一条消息主动展示

**当前状态：** 脚本 `scripts/rule-rules-display.sh` 已存在，但 hook 配置尚未写入 config.yaml（等待用户确认）。在新会话中 Agent 会主动展示 RULE 规则（基于 RULE7 记忆实现）。

**生效验证：**

创建或修改知识库文件 / Memory / Skill 时，自问：

- [ ] 这条信息包含用户真实姓名或昵称吗？
- [ ] 包含真实客户名称或国别吗？
- [ ] 包含密码 / Token / API Key 吗？
- [ ] 包含运营商内部资料或 IP 地址吗？
- [ ] 包含监听数据或 LIID 吗？
- [ ] 包含商业机密或合同条款吗？
- [ ] 操作涉及 `work-projects/` 下的 LI 项目源码吗？
- [ ] 已按 RULE20 审核知识处理路由？
  - [LI 内容 → OpenLI 替代后可在线] / [ZTLIG/Sinovatio → 禁止] / [A1 → 全程本地]

**有任何一项为"是" → 属于第三层，不进 Prompt。**
**包含用户真实姓名 → 立即替换为「用户」或「andym」。**

## 跨服务器同步

将本地安全规则和审计系统部署到下游服务器（如腾讯云 Hermes Agent）。

### 完整 MEMORY + RULE 同步

完整的 MEMORY 和 RULE（Skills + Knowledge）同步参考 `hermes-evolution-mechanism` skill 的 `references/multi-instance-sync.md`。以下是安全规则和审计脚本同步：

### 同步安全层

```bash
# 1. SSH ControlMaster 持久连接（腾讯云专用）
mkdir -p ~/.ssh/controlmasters
ssh -Nf tencent

# 2. 同步安全规则（_system 已含在 Knowledge 全量同步中）
# 全量同步见 hermes-evolution-mechanism/references/multi-instance-sync.md

# 3. 同步审计脚本（独立同步，非 Knowledge 同步内容）
rsync -avz ~/.hermes/scripts/security-audit.py tencent:~/.hermes/scripts/

# 4. 远程执行审计
ssh andymao@124.222.206.209 'python3 ~/.hermes/scripts/security-audit.py'

# 5. 读取远程报告
ssh andymao@124.222.206.209 \
  'cat ~/knowledge/_system/security/audit-reports/security-audit-*.md'
```

> 注意：远程用户名为 `andymao`（非旧文档中的 `ubuntu`），SSH Host 为 `tencent`（~/.ssh/config 中配置）。

### 安全限制

- **切勿同步 `li/` 目录内容**到云服务器（LI 数据本地保留）
- **切勿同步 `hi2/` 目录内容**到云服务器（LI 协议标准）
- **切勿同步 `.env` 和 `config.yaml` 中的密钥**到不受信的服务器
- 腾讯云上的 Qdrant 索引需确认集合创建与 `kb-index` 脚本配置

## 参考链接

- DeepSeek 隐私政策：https://platform.deepseek.com/api-docs/policies
- OpenAI 数据使用：https://openai.com/policies/api-data-usage-policies
- Anthropic 数据隐私：https://www.anthropic.com/legal/privacy
- 本技能参考文件：`references/name-leakage-vectors.md`、`references/5-level-classification.md`、`references/knowledge-isolation-analysis.md`、`references/knowledge-directory-security-split.md`、`references/env-source-pitfall.md`、`references/security-audit-setup.md`、`references/baidu-netdisk-import.md`、`references/config-key-migration-record.md`、`references/rule20-decision-tree.md`、`references/rule-system-maintenance.md`
