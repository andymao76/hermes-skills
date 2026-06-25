---
name: knowledge-closed-loop
description: >
  知识闭环系统 — 每次问题解决后自动沉淀为可复用资产。流程：
  问题→解决→经验总结→反思卡片→(Skill过程记忆 / Knowledge陈述记忆)→未来复用。
  当用户完成一次故障排查、技术调研、配置部署、或新知识学习后，自动触发反思卡片生成。
  也适用于用户说"记下来""保存""学到了""知道了""搞定了"等完成信号时。
version: 1.0.0
author: Andy Mao
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [knowledge, closed-loop, reflection, skill-creation, knowledge-base]
    related_skills: [hermes-second-brain-v5, second-brain-inbox, skill-creator, self-improvement, auto-skill-precipitator]
    config:
      - key: knowledge.paths.reflection_cards
        description: "反思卡片存放目录，相对于 knowledge 根"
        default: "00_INBOX/反思卡片/"
      - key: knowledge.paths.skills_backup
        description: "Skill 备份到知识库的路径"
        default: "技能/hermes-skills/"
---

# 知识闭环系统 (Knowledge Closed-Loop)

## When to Use

加载此技能的触发场景：

| 触发信号 | 示例用户表述 |
|---------|-------------|
| **排错/解决成功** | "终于搞定了" / "解决了" / "通了" / "可以了" |
| **学到新知识** | "原来是这样" / "学到了" / "还有这种操作" |
| **用户直接指令 "学习"** | "学习 X" / "学习并整合" — 用户提供技术内容要求保存到知识库。特征：用户说"学习"作为命令动词，后跟待学内容或文件路径 |
| **完成技术调研** | "帮我查一下..." / "对比一下XXX和YYY" |
| **配置部署成功** | "能用了" / "部署成功" / "装好了" |
| **用户主动触发** | "记下来" / "保存" / "记住这个" / "沉淀一下" |
| **知识口述采集** | 用户分段口述专业知识（跨多轮次），Agent 编译、结构化、确认后入库。特征：用户是知识源，而非 Agent 去查资料。常见于技术方案自述、产品特性说明、配置规范口述 |
| **非 MD 文件入库** | "把 .xmind 导进来" / "把 PPT 放知识库" / "解析这些流程图" — 将二进制/专有格式文档转为知识库 Markdown 笔记 |
| **Session 结束** | 用户表示满意或任务明确完成时 |

**不触发的情况：** 纯聊天、日常信息查询（天气/油价/新闻）、简单问答、用户明确说"不用记了"。

## Quick Reference

| 步骤 | 动作 | 产出物 |
|------|------|-------|
| ① 反思 | 生成「反思卡片」 | `~/knowledge/00_INBOX/反思卡片/YYYYMMDD-主题.md` |
| ② 分流 | 按规则判断 → Skill（过程记忆）/ Knowledge（陈述记忆） | 卡片中标注结论 |
| ③a 升格 Skill | 用 skill-creator 流程创建 SKILL.md + 备份到知识库 | `~/.hermes/skills/` + `~/knowledge/技能/hermes-skills/` |
| ③b 存入Knowledge | 存入对应知识库分类目录 | `~/knowledge/` 下对应分类 |
| ④ 索引更新 | 更新酶索引 | enzyme_refresh() |
| ⑤ 自动扫描 | auto-skill-precipitator（每天22:00 cron） | 后台自动检测 Pattern，生成草案待确认 |
| ⑥ 闭环确认 | 告知用户沉淀成功 | 消息回复 |

## Procedure

### Step 1: 识别触发时机

参考上方的"When to Use"表。关键判别标准：
- **用户表达了完成感** — 问题已解决、部署已成功、信息已获取
- **过程中有非直觉的步骤或知识点** — 如果只是简单的"开个开关"，不需要沉淀
- **可跨场景复用** — 如果是绝对一次性的事情（如某个特定 bug 修复但上下文不可复现），标记为归档

### Step 2: 生成反思卡片

按以下模板填写，写入 `~/knowledge/00_INBOX/反思卡片/YYYYMMDD-主题.md`：

```markdown
# 反思卡片: [主题]
日期: YYYY-MM-DD
来源: [问题描述/任务名称]

## 发生了什么
[简要描述问题和解决过程，2-4句话]

## 学到了什么
[核心收获，2-3个要点，突出非直觉的步骤]

## 可复用判断
- 同类问题发生频率: [首次 / 偶尔 / 频繁]
- 解决步骤是否固定: [是 / 否]
- 是否依赖特定环境: [是 / 否]
- 是否需要工具命令: [是 / 否]

## 结论
→ ⭐ **升级为 Skill**（跨项目可复用 + 有固定步骤）
→ 📝 **存入 Knowledge**（事实/笔记/参考）
→ [ ] 归档（一次性，无需保留）
```

### Step 3: Skill ↔ Knowledge 分流决策

| 条件 | ⭐ Skill（过程记忆） | 📝 Knowledge（陈述记忆） |
|------|-------------------|----------------------|
| 有固定操作步骤 | ✅ | — |
| 需要工具/命令调用 | ✅ | — |
| 跨项目可复用 | ✅ | — |
| 事实/概念/原理 | — | ✅ |
| 项目背景/决策记录 | — | ✅ |
| 参考文档/笔记 | — | ✅ |

**复合判断：** 如果既有固定步骤又有背景知识，Skill 为主，Knowledge 为辅（Skill 中引用 Knowledge 笔记）。

### Step 4a: 升格为 Skill

当结论为 ⭐ 时：

1. 用 `skill_manage(action='create')` 创建正式 SKILL.md
2. 同时备份到知识库：`~/knowledge/技能/hermes-skills/<skill-name>/SKILL.md`
3. 在 Skill 的 description 中加入触发关键词，确保下次自动命中
4. 如果卡片内容超过 300 行，将详细信息移到 `references/` 目录

**Skill 命名规范：** 必须是类级名称（如 `system-diagnostics`, `github-api-fallback`），禁止单次会话名称（如 `fix-tencent-cloud-install`）。

### Step 4b: 存入 Knowledge

当结论为 📝 时：

1. 分类存入对应知识库目录：
   - `~/knowledge/01_PROJECTS/` — 项目相关
   - `~/knowledge/02_AREAS/` — 长期责任领域（如宠物/健康）
   - `~/knowledge/03_RESOURCES/` — 技术参考
   - 对应 Obsidian 三分类：`工作/` / `知识/` / `技能/`
2. 反思卡片保留在 INBOX，标注 "✅ 已处理"

### Step 5: 更新索引

```bash
cd ~/knowledge && bash ~/.hermes/scripts/enzyme-init.sh
```

> ⚠️ **注意**：enzyme 的催化剂生成依赖 LLM 的 JSON mode 支持。DeepSeek V4 不支持 `json_object` response_format，会导致催化剂生成失败。托管服务 app.tryenzyme.com 在代理环境下不可达。
> 脚本自动使用 SiliconFlow + Qwen3.5-397B-A17B（已验证可用，催化剂产量 73→251）。
> 如果脚本静默失败（exit code 2 无输出），用 Python 回退方法，详见 `references/enzyme-refresh.md`。

### Step 6: 闭环确认

回复用户，简短的闭环确认：

```
✅ 已沉淀 (主题) → [Skill / Knowledge]，下次遇到同类问题可以直接复用。
```

## 知识口述采集流程（Special Pattern）

当触发场景为"知识口述采集"时，流程与上述标准步骤不同：

### 口述采集四步法

| 阶段 | Agent 动作 | 示例 |
|------|-----------|------|
| ① 接话 | 确认收到，展示已有上下文关联，避免打断用户思路 | "你在记录华为 SVC 监听的技术要点" + 查知识库已有内容 |
| ② 随行编译 | 每轮用户口述后，立即整理为结构化草稿呈现给用户确认 | 编表、分节、提炼关键参数 |
| ③ 迭代整合 | 新口述内容追加到同一份草稿，保持整体结构一致 | 用户说 X2 → 添加到同一笔记的 X2 章节 |
| ④ 最终入库 | 用户确认完成或切换话题后，写入知识库 + 告诉用户保存位置 | "已写入 telecom/lawful_interception/..." |

### 口述采集 vs 标准闭环的区别

| 维度 | 标准闭环 | 口述采集 |
|------|---------|---------|
| 知识来源 | Agent 调研/用户单次表述 | 用户跨多轮次分段输出 |
| 保存时机 | 问题解决后一次性写入 | 用户每段后确认，全部完成再最终写入 |
| 反思卡片 | 需要生成 | 不需要（无"问题"只有"知识输出"） |
| 是否分 Knowledge/Skill | 需判断 | 几乎总是 Knowledge（陈述性知识） |

### 口述采集检查清单

- [ ] 每轮口述后展示结构化草稿让用户确认
- [ ] 草稿保持在同一份笔记中增量更新
- [ ] 用户切换话题或主动表示完成后才最终写入文件
- [ ] 写入后告知用户保存路径
- [ ] 附带的代码/配置/日志片段正确嵌入

### 口述采集实用技巧

| 技巧 | 说明 |
|------|------|
| **用 patch 增量更新** | 不要每轮都用 write_file 覆盖整份文件。用 patch 在已有笔记的对应章节追加或插入新内容，保留用户之前确认过的不变。仅首次写入用 write_file |
| **展示结构树** | 每轮整合后给用户一个缩略结构树（Markdown 列表或 ASCII 树），让用户快速了解当前笔记的全局概览 |
| **编表优先** | 技术参数类内容（枚举值、协议字段、对比表）优先编为表格，比纯文本段落更易于审查和补充 |
| **留待补充占位** | 用户未提及的章节项标记 `(待补充)`，提示用户还有缺口可填 |
| **批量文件先抽样验证** | 非 MD 文件（.xmind/.pptx/.docx）批量入库时，先处理 1-2 个样本给用户确认解析质量，再运行全量脚本 |
| **配置参数三栏表** | 当文档涉及系统配置参数时，用 `参数名 | 值 | 说明` 三栏表组织，下方附实例日志作为上下文佐证。不要只贴配置代码块 |
| **交叉链接与笔记拓扑** | 创建多篇相关笔记时，每篇笔记末尾用 `| 笔记 | 定位 |` 表格列出所有关联笔记及其作用。正文中通过 `[[]]` wikilinks 引用，形成可导航的知识网络 |
| **日志驱动排障文档** | 当用户提供生产环境错误日志时，不要只贴日志。提取日志中的关键行 → 归纳告警码 → 写明根因 → 给出处理步骤。最终形成「报错｜原因｜处理」的排障速查表 |
| **三层笔记架构** | 覆盖同一技术域时，按以下层次分篇：(1) **方案原理篇** — 架构、标准、参数定义；(2) **原始数据/协议篇** — 真实抓包/解码/日志；(3) **运维部署篇** — 配置、命令、排障。每篇用 wikilinks 互相关联 |

### 原始协议数据采集（Special Sub-Pattern）

当用户提供的是原始协议数据（ASN.1 解码输出、Hex 码流、Wireshark 导出文本、tcpdump 输出等）时，遵循以下补充流程：

#### 协议数据采集四步法

| 阶段 | Agent 动作 | 示例 |
|------|-----------|------|
| ① 秩序重建 | 识别数据是「完整呼叫流程」还是「单条消息」，建立时间线/消息序列 | 用户提供 13 份 iRI_CALL_Report → 按时间排序 + 标记方向 |
| ② 关键字段提取 | 从大量重复字段中提取不变标识（LIID/CallID/ICID）和变化字段，编为摘要表 | CallID/ICID/Dialog Tags → 顶部表格；不同字段 → 对比表 |
| ③ 时序归纳 | 将多条消息整理为时序图或流程表，标注关键状态变迁 | INVITE→183→PRACK→200→UPDATE→...→BYE，每行时间+消息+方向 |
| ④ 观察总结 | 末尾附上「观察总结」小节，提炼可复用的规律和异常点 | ICID 全程不变、ecid 上下行差异、to-tag 何时首次出现 |

#### 协议数据处理要点

- **去冗余**：每条消息中重复的公共字段（domainID、iRIversion、operator-Identifier 等）在摘要部分统一记录一次，正文中精简
- **缩略 vs 展开**：消息头部分（关键字段解码）给出结构化表格；payload 部分（SIP 消息体/Hex 码流）作缩略显示或附录
- **对比表优先**：多条消息之间的差异（如 ecid 变化、to-tag 从 void 变成实际值）用对比表呈现
- **观察总结**：末尾必须有一段总结，提炼从数据中发现的规律，否则只是一堆原始数据的搬移

#### 协议数据 vs 口述采集的区别

| 维度 | 知识口述采集 | 原始协议数据采集 |
|------|------------|----------------|
| 用户输出 | 概念描述/参数说明 | 解码文本/码流/抓包 |
| 主要工作 | 结构化编排 | 去冗余 + 摘要提取 + 时序归纳 |
| 编表重点 | 概念对比表 | 字段变化追踪表 + 时序表 |
| 校验方式 | 让用户确认概念准确性 | 检查字段一致性（如 CallID 是否全程一致） |
| 最终篇幅 | 中等（200-500 行） | 可能很长（需做缩略优化） |

## 非 MD 文件入库流程（Special Pattern）

当触发场景为"非 MD 文件入库"时，遵循以下流程：

### 入库五步法

| 阶段 | Agent 动作 |
|------|-----------|
| ① 格式识别 | 判断文件类型（.xmind = ZIP + JSON/XML；.pptx = ZIP + XML；.docx = ZIP + XML；**.chm = LZX压缩HTML归档，用7z解压**等） |
| ② 解析提取 | 用合适的工具/库提取结构化内容（Python zipfile + json、python-docx、python-pptx 等） |
| ③ 结构映射 | 将源格式的层级结构映射为 Markdown 标题/列表/表格，保留核心元数据 |
| ④ 写入知识库 | 生成 YAML frontmatter + Markdown 正文，写入对应分类目录 |
| ⑤ 索引更新 | 运行 enzyme_refresh() 确保新笔记可搜索 |

### 操作型知识入库注意事项

- 用户提供的 shell 命令/SQL/Gremlin 等操作型知识中，**IP 地址、端口号、Topic 名称、Consumer Group 名称、文件路径、版本号**几乎都是项目专属的
- 入库前先判断：这份材料来自哪个项目（A1/OWLS/ZTLIG/SIOCC）？有没有其他项目通用的部分？
- 在笔记顶部用 ⚠️ 块引用标注项目专属说明，如：`> ⚠️ **项目专属说明**\n> 本文档中的 IP 地址（215.152.1.15:9092）为 A1 项目（苏丹/北苏丹）专属...`
- 标签使用项目级标签（`a1-project`）而非通用标签（`owls/ztlig`），避免误导
- 记忆中也记录项目与配置的映射关系，方便未来跨会话复用

### LI 技术文档入库 — 厂商优先分类规则

用户学习 LI（合法监听）技术文档时，严格按以下优先级确定存放目录：

**规则：厂商名 > 项目名 > 通用目录**

| 内容性质 | 目标目录 | 示例 |
|---------|---------|------|
| 特定厂商的协议/接口文档 | `li/<vendor>/` | Ericsson SOAP 样本 → `li/Ericsson/` |
| 厂商对接工作流（含配置/排障） | `li/<vendor>/` | ZTLIG + Ericsson IMS 运维 → `li/Ericsson/` |
| 项目专属的运维笔记 | `li/projects/<project>/` | A1 项目 Greenplum 查询 → `li/projects/a1-project/` |
| 多厂商通用的架构/流程 | `research/` 或 `li/tools-and-standards/` | OWLS 整体架构 → `research/` |

**常见错误**：将 Ericsson/华为/ZTE 的文档先放到 `li/projects/` 或 `research/` 下 → 被用户纠正。默认先往 `li/<vendor>/` 放，只有明确项目专属才放 `li/projects/`。

### 旧版 .doc 二进制文件提取

当知识库中包含旧版 Word .doc 文件（非 .docx）时：

```python
import olefile

ole = olefile.OleFileIO('file.doc')
word_doc = ole.openstream('WordDocument').read()
text = word_doc.decode('utf-16-le', errors='replace')
# 过滤出可读字符
clean = ''.join(c for c in text if c.isprintable() or c in '\n\r\t'
                or '\u4e00' <= c <= '\u9fff')
```

注意：.doc 是 OLE2 复合文档格式，无法用 python-docx 读取（python-docx 只支持 .docx）。使用 `olefile` 库提取 `WordDocument` 流后按 UTF-16-LE 解码可获取主体文本。

### 图片识别回退方案（vision_analyze 不可用时）

当内置 `vision_analyze` 因当前模型不支持 vision 而失败时：

```bash
# 1. 准备 payload（Python）
payload = json.dumps({"model": "Qwen/Qwen3-VL-32B-Instruct",
  "messages": [{"role": "user",
    "content": [
      {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
      {"type": "text", "text": "描述这张图"}}]}]})
with open('/tmp/vl_payload.json', 'w') as f: f.write(payload)

# 2. 用 env 变量传 API key（终端环境有 key 但被 redact，用文件中转）
printenv SILICONFLOW_CN_API_KEY > /tmp/.sfkey.tmp
KEY=$(cat /tmp/.sfkey.tmp)

# 3. 调用 Qwen VL（注意 key 不在命令中硬编码，通过文件中转）
curl -s --max-time 180 -X POST https://api.siliconflow.cn/v1/chat/completions \
  -H "Authorization: Bearer *** \
  -H "Content-Type: application/json" \
  -d @/tmp/vl_payload.json
```

此方法使用 SiliconFlow CN 的 Qwen3-VL-32B-Instruct 模型，需确保 `SILICONFLOW_CN_API_KEY` 环境变量存在。

- 大文件批量入库时，先用 1-2 个样本验证解析质量
- 保留源文件路径引用（放在 frontmatter 或 blockquote 中）
- 文件数量多时，在目标目录下保持原文件名（或合理映射）-  
- 入库完成后给出汇总表（文件名、状态、主题数）
- 详见 `references/chm-document-learning.md` 中的笔记结构化模板（索引笔记格式、单篇知识笔记格式、关键原则）
- 用户分段粘贴 CLI 命令/SQL/Gremlin 等操作型知识时，详见 `references/operational-cli-knowledge-ingest.md`（检查已有知识→识别项目归属→结构化笔记→入库索引完整流程）

### Verification

- [ ] 1-2 个样本文件已人工审查内容质量
- [ ] 所有文件已写入知识库目标目录
- [ ] 数据统计汇总已展示给用户
- [ ] `enzyme_refresh()` 已执行

## Pitfalls

| 陷阱 | 说明 |
|------|------|
| ❌ **过于积极** | 不要每个简单问题都生成卡片。判别标准：过程中是否有"非直觉"的步骤？ |
| ❌ **命名太窄** | Skill 名不能用 `fix-xxx-today`、`debug-yyy` 这种一次性的名字 |
| ❌ **忘备份** | 创建 Skill 后必须同时备份到 `~/knowledge/技能/hermes-skills/` |
| ❌ **Skill 和 Knowledge 混为一谈** | 有固定步骤 → Skill；纯事实/概念 → Knowledge。不要合并为一个文件 |
| ❌ **跳过用户确认** | 生成卡片后告诉用户结论，让用户确认后再执行升格。除非用户说"你决定"或"直接做" |
| ❌ **引用模板变量时路径错误** | SKILL.md 中使用 `/home/andymao/.hermes/skills/productivity/knowledge-closed-loop` 引用技能目录路径，不要写死路径 |
| ❌ **卡片中放敏感信息** | 反思卡片只能存经验和流程，不要直接粘贴 API key、密码、私有 URL |
| **日志仅粘贴不提炼** | 用户给生产错误日志时，不要原样贴入笔记。提取关键行→告警码→根因→处理步骤，形成排障速查表 |
| ❌ **项目专属数据未标注范围** | 用户提供的 IP 地址、端口号、Topic 名称、命令路径等极可能是**特定项目专属**（A1/OWLS/ZTLIG）。在笔记顶部用 ⚠️ 标注项目专属说明 + 警告"其他项目使用前需人工确认"。标签也要从通用标签改为项目标签（如 `a1-project` 而非 `owls/ztlig`）。内存中记录项目映射关系 |
| ❌ **单篇笔记塞太多层次** | 方案原理、原始数据、运维部署应分三篇，用 wikilinks 关联。混为一篇导致篇幅失控
| ❌ **enzyme refresh 静默失败** | `enzyme-init.sh` 带 `set -e`，当 `.env` 文件不存在或 API key 提取失败时静默退出（exit code 2）。检查 `echo $?`，如果返回 2 则转用 Python 回退方法（见 references/enzyme-refresh.md 方法二） |
| ❌ **直接用 raw enzyme refresh 而不是脚本** | `cd ~/knowledge && enzyme refresh` 或 `enzyme refresh --use-env-llm` 在当前环境中会失败，因为 LLM 环境变量必须通过 `~/.hermes/scripts/enzyme-init.sh` 从 config.yaml 提取（SiliconFlow API key → OPENAI_API_KEY）。始终执行 Step 5 的 `bash ~/.hermes/scripts/enzyme-init.sh`，不要绕开脚本直接调 enzyme。 |
| ❌ **delegate_task 超过并发限制** | `delegate_task` 的 `tasks` 数组提交超过 3 个任务会报 `max_concurrent_children` 错误。分批处理：第1批3个，第2批3个，以此类推。单任务用单项 `goal` 参数 |

## Verification

完成后检查清单：

- [ ] 反思卡片已写入 `00_INBOX/反思卡片/`
- [ ] 卡片结论标注清晰（⭐/📝/归档）
- [ ] 如果是 Skill：`~/.hermes/skills/` 下有新 SKILL.md
- [ ] 如果是 Skill：`~/knowledge/技能/hermes-skills/` 下有备份
- [ ] 如果是 Knowledge：已移入正确分类目录，INBOX 卡片标记已处理
- [ ] 如果是操作型知识：IP/端口/Topic 等已标注项目范围
- [ ] `enzyme refresh` 已执行，`enzyme status` 显示催化剂数 > 0
- [ ] 已告知用户闭环完成

## References

- `references/reflection-card-examples.md` — 本技能测试时生成的示例反思卡片
- `references/flow-architecture.md` — 闭环系统架构说明（含未来 Phase 2/3 规划）
- `references/li-knowledge-three-layer-architecture.md` — 三层笔记架构示例（HW-LI 合法监听知识体系，2026-06-15 会话）
- `references/chm-document-learning.md` — CHM文档提取与学习入库流程（7z解压 + delegate_task并行处理 + 三层架构归类）
- `references/incremental-doc-ingest.md` — 分段文档分享模式：用户逐段粘贴文档内容，增量更新知识库条目的工作流
