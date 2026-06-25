# 知识口述采集 + 文件入库 — 会话示例

> 来源：2026-06-15 会话，用户口述华为 SVC VoLTE ETSI 监听技术规范 + 批量解析 .xmind 文件

## 示例一：知识口述采集（Huawei SVC LI）

### 会话过程

用户轮次（共 9 段）：
1. "在华为SVC上监听，1简单说明，设控基本同CS模式..."
2. "X2简析，如果是当基于IMS标准实现拦截时..."
3. "iMS-IRI-Report 中包含的 iMS-Gen-IRI-Report 1)reportReason..."
4. "ETSI ES 201 671，IMS监听采用与接入无关的集中式监听模式..."

### Agent 行为

| 轮次 | Agent 响应 |
|------|-----------|
| 第 1 段 | 不直接写入！先查知识库有无相关已有笔记，整理已接收内容为表格/章节，询问"是否继续/保存" |
| 第 2 段 | 将新内容整合到同一份草稿的对应章节（X2 信令面），保持结构一致 |
| 第 3 段 | 追加参数详解，编表（reportReason 枚举值表 + connectionParameter 表） |
| 第 4 段 | 补充标准号 ETSI ES 201 671、CS-Event 枚举 18，整体笔记接近完成 |
| 第 5–6 段 | 展开 X1SetTarget 约束、X3Address Choice 类型、多号码拦截场景(a/b/c)、CS vs IMS 模式选择 |
| 第 7 段 | 补充 IMS 常见模式(hw_imsbase/mavenir/102232-5)、CC 固定 x3port 无需协商 |
| 第 8 段 | 补充 TS 102.232 标准；RTP 方向头 0x51↑/0x50↓；IMSBASE vs SIP-I 对比（ISUP带方向/四元组关联） |
| 第 9 段 | 补充 IPCC 格式（IP/UDP/RTP/Payload）、IGW 解包/LIG 组装、适用范围(IMS-base+NGN) |

### 关键技巧

- **用 `patch` 增量更新**：每轮新内容只 patch 对应章节，不 rewrite 全文件
- **每轮后展示结构树**：让用户看到整体布局，决定下一步补充方向
- **技术参数编表**：reportReason 枚举、connectionParameter 表、IMSBASE vs SIP-I 对比表——表格优先于段落

### 最终产出
- 路径：`知识/telecom/lawful_interception/华为SVC_VoLTE_ETSI监听方案.md`
- 字数：~4600 bytes / 125 行
- 结构：7 个章节（标准号 → IMS 监听模式概述 → 设控 → X3 媒体面含 IPCC → X2 信令面含参数详解 → 多号码拦截 → CS/IMS模式选择 → IMS常见模式含RTP方向对比）
- 标签：[华为, SVC, VoLTE, ETSI, LI, 合法监听, IMS, X2, X3]

### 关键原则
- ❌ **不要每段口述后立即写入文件** — 用户可能还有更多内容
- ✅ **每段后编译为结构化草稿呈现**，让用户看到进展并继续补充
- ✅ **引用已有知识库内容**，展示上下文关联性
- ✅ **最终写入后给出路径**，方便用户直接打开

## 示例二：非 MD 文件入库（.xmind 批量解析）

### 场景
用户有 16 个 .xmind 思维导图文件在 `~/OWLS/` 目录下，要求解析后存入知识库。

### Agent 行为

1. **格式识别**：.xmind = ZIP 压缩包，内含 content.json（XMind 2020+）或 content.xml（XMind 8）
2. **解析提取**：Python zipfile + json 直接读取，无需第三方库
   ```python
   with zipfile.ZipFile(fpath) as z:
       data = json.loads(z.read('content.json'))
   ```
3. **结构映射**：递归遍历 topic 树，缩进 + 列表形式映射为 Markdown
   - sheet → `## 画布`
   - topic → `- ` 缩进层级
   - children.attached → 子列表
   - note/url/labels → 附加行
4. **元数据保留**：frontmatter 含 title/source/created/modified/format/creator/tags
5. **写入知识库**：`知识库/工作/项目/OWLS/` 下，每文件一篇独立笔记
6. **索引更新**：enzyme_refresh()（不可用时通过 ls 确认文件存在即可）
7. **工具选择**：用 `execute_code` 跑批量处理脚本（16 文件单次完成），比逐文件用 terminal 更高效

### 关键原则
- ✅ **先抽 1-2 个样本验证内容质量**，再批量处理全部文件
- ✅ **保留层级结构**，不压平为纯文本
- ✅ **写入后给出总量汇总**（多少个文件成功/失败）
- ✅ 遇到 .xmind 版本差异（content.json vs content.xml）分别处理

### 文件入库检查清单（本会话）
- [x] 16/16 文件解析成功
- [x] 最深 5 级层级保留
- [x] 含格式版本信息（content.json / content.xml）
- [x] 知识库目录：`工作/项目/OWLS/`
- [x] 用 `execute_code` 批量处理：单脚本遍历16文件，zipfile + json 解析，并行写入知识库
- [x] 处理前后分别验证：先看1个文件样本，全量完成后抽查2份确认质量

## 示例三：原始协议数据采集（Huawei X2 IRI 报告）

### 场景

用户在完成华为 SVC VoLTE ETSI 监听方案的知识口述后（示例一），进一步提供了完整的 X2 接口 iRI_CALL_Report 原始解码数据，涵盖 13 条消息的完整呼叫流程（INVITE → BYE），含 ASN.1 解码文本和 Hex 码流。

### 会话过程

用户轮次（约 10+ 段，每段是一个完整的 IRI 报告解码，约 300-800 行文本）：
1. 第 1 组：INVITE 报告（含完整 SIP INVITE + SDP）
2. 第 2 组：183 Session Progress 报告
3. 第 3-4 组：PRACK + 200 OK
4. ... 依次提供 UPDATE、180 Ringing、BYE 等全部 13 条消息

### Agent 行为

| 阶段 | 具体操作 |
|------|---------|
| ① 秩序重建 | 从每条消息的 timeStamp 提取时间（08:52:46 → 08:53:06），按时间排序。识别方向（sipMessageDirection=01 上行/00 下行） |
| ② 关键字段提取 | 发现 LIID=1、CallID=fepei4njbhl7kllj44egkfggijew7f4k@192.6.170.222、ICID=pcscf06.198.bb.20140722005245 **全程不变** → 提取到顶部摘要表 |
| ③ 时序归纳 | 编为 13 行时序表（时间戳、SIP 消息、方向、方向码），附 SDP 信息表和 P-Charging-Vector ecid 对比表 |
| ④ 观察总结 | 末尾写 10 条观察总结（ICID 不变、CallID 不变、to-tag 何时出现、ecid 上下行差异等） |

### 消息内容处理方式

- **原始 ASN.1 解码文本**：在最终笔记中精简为**结构化解码摘要**（去掉重复的 void 字段、CC 填充字节），每条消息用三重反引号包裹
- **Hex 码流**：作为附录保留参考（标注为原始码流），不在正文中展开
- **SIP 消息体**：完整保留但转换为易读格式（Hex → ASCII 原文）
- **重复公共字段**：只在第一条消息中完整展示 IRI_Parameters 结构，后续消息仅展示有变化的字段

### 最终产出

| 项目 | 值 |
|------|-----|
| 笔记路径 | `知识/telecom/lawful_interception/华为SVC_IMS_X2报告抓包示例.md` |
| 文件大小 | ~13,700 bytes |
| 覆盖消息 | 13 条 iRI_CALL_Report（完整 VoLTE 呼叫流程） |
| 结构 | 概述表 → 呼叫基本信息 → 13 步时序表 → SDP/ecid 对比 → 每条消息解码 → 10 条观察总结 |

### 关键原则

| 原则 | 说明 |
|------|------|
| ✅ **先建立秩序** | 不要直接开始写文件。先识别消息序列、提取公共字段，建立全局视图 |
| ✅ **去冗余** | 每条消息都有的 LIID/CallID/ICID 在顶部统一记录，每条消息正文只写变化字段 + SIP 消息体 |
| ✅ **对比表优于段落** | ICID 变化、ecid 差异、to-tag 首次出现 — 全部用对比表，一目了然 |
| ✅ **观察总结必须写** | 否则只是一堆原始数据的堆砌。总结让数据产生价值 |
| ❌ **不要逐条完整展开** | 13 条消息每条完整展开 IRI_Parameters 结构 → 笔记过于臃肿。用 1 条做完整示例，其余精简 |
