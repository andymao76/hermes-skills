---
name: telecom-li-documentation
description: 合法监听(LI)系统技术文档编写与知识沉淀 — 覆盖华为/ZTE/ETSI X1/X2/X3接口、BER/ASN.1编码、CDR字段定义、ZTLIG运维手册等。当用户提供LI系统技术细节、抓包日志、配置参数时触发。
trigger: 用户提供合法监听接口/协议细节、X接口日志、ASN.1定义、CDR字段、ZTLIG配置、或要求整理LI系统知识。包括 5GC SVC / 5GC LI / 5G Core 监听接口、X1M 证书管理、FUNCType 5GC 编码、5GC TNEType 网元模型 (UNC/UDG/UDM/USN) 等内容。
---

## Telecom LI Documentation — Knowledge Capture Workflow

When the user provides lawful interception system technical details in chunks, follow this structured documentation workflow.

### 1. Determine Class of Content

| Content type | Storage path | Notes |
|-------------|-------------|-------|
| Protocol principle (IMS/CS X1/X2/X3) | `知识/telecom/lawful_interception/{topic}方案.md` | Standards, modes, parameters |
| Real packet/decode reference | `知识/telecom/lawful_interception/{topic}抓包示例.md` | Full decode with SIP messages |
| Interface reference (connection, config, errors) | `知识/telecom/lawful_interception/{topic}接口说明.md` | Protocol + ops combined |
| System operations manual | `知识/telecom/lawful_interception/{topic}运维手册.md` | Installation, inspection, troubleshooting |
| Vendor LI interface protocol reference | `知识/hi2/厂商对接/{Vendor}_{Domain}_{Interface}规范.md` | HI1/HI2/HI3 vendor protocol specs, RAI binary protocol, ASN.1 definitions, CLI command references |
| Ericsson LI-IMS SOAP samples | `~/knowledge/li/Ericsson/Ericsson_LI_{Operation}_SOAP_Sample_2dot1.md` | 5 CRUD SOAP XML samples → stored under `li/Ericsson/`, NOT under `li/projects/` |
| Ericsson LIMS integration workflow | `~/knowledge/li/Ericsson/LIMS_Workflow_and_Maintenance.md` | ZTLIG → Ericsson LI-IMS whole pipeline (Kafka→ztlig1/2→SSF/RVF→Flink→Web) |
| ZTLIG workflow diagram | `~/knowledge/li/Ericsson/ztlig-workflow.png` | PNG flowchart of ZTLIG processing pipeline |
| Vendor-specific config reference | `知识/telecom/lawful_interception/{topic}配置说明.md` | ztlig.cfg/LIMS config sections (NE/VNE/LEA/process blocks) |
| SOAP/WebService interface | `知识/telecom/lawful_interception/{vendor}1口对接调试文档.md` | WSDL+XSD+properties based interfaces, SOAP operations |
| Deployment survey template | `知识/telecom/lawful_interception/{topic}工勘指导.md` | Pre-deployment NE information collection tables |
| 5GC protocol reference | `知识/telecom/lawful_interception/hw-svc-5gc-li-x-interface.md` | 5GC SVC X1/X1M/X2/X3 协议栈, TNEType/UNC/UDG/USN, FUNCType Bit7=1 编码 |

### 2. Documentation Sections for Each Content Type

**For Protocol/Principle docs:**
- Standards reference (ETSI number, ASN.1 file)
- Interface overview (transport protocol, C/S mode, constraints)
- Parameter tables (field name, encoding, bit-level details)
- Differences between modes (CS vs IMS, IMSBASE vs SIP-I)
- Call flow examples

**For Packet Decode references:**
- Call basic info table (LIID, CallID, ICID, timestamps)
- Full signal flow timeline (message name, direction, sipMessageDirection)
- Media information (IP, ports, codecs)
- Key observations (ICID unchanged, ecid differences, etc.)
- Each packet IRI decode structure annotated

**For Interface/Operations references:**
- BER encoding basics (T L V structure, length encoding >127 with 0x81)
- HW header structure with hex examples
- ASN.1 definition extracts
- CDR field definition tables with all enumeration values
- Location information encoding (CGI/LAI/SAI/RAI/TAI/ECGI byte structure)
- TBCD-STRING encoding with AddressString bit definition
- Error codes and troubleshooting
- tcpdump packet capture commands for each interface
- Real log examples (successful setup, authentication failure)

**For SOAP/WebService interfaces (Ericsson LI-IMS):**
- WSDL binding → portType → message → element trace
- Cross-file XSD reference resolution (multiple XSDs per namespace)
- createWarrant structure: requestHeader + warrantItem + dtlWarrantNeTypeItemArray
- modifyWarrant/warrantDeleteRequest: same warrantItem structure; deleteWarrant has NO dtlWarrants
- getWarrantList: uses warrantQuery = header + listInformation(pagination) + filterDetails(warrantItem) + filterNeType + filterHI2Lemf + reason + orderArray
- Key fields: warrantID(-1), neType, isDataMonitoringOnly, mcnbs, supplementaryInfo(bitmask), targetTypeID
- Login → sessionID → authenticated operations flow
- sessionID lifecycle: 5 minutes, inject into every subsequent requestHeader.sessionID
- Available functions from login response (WarCreate/WarDelete etc.)
- Response code semantics (3=success/0=pending)
- **CRUD type.__value encoding** (from requestHeader.type.__value):
  - **1** = Create (createWarrant)
  - **2** = Delete (deleteWarrant)
  - **3** = Read/Query (getWarrantList)
  - **4** = Update/Modify (modifyWarrant)
- **deleteWarrant prerequisite**: must modifyWarrant(state=terminated) first, then sleep 3s, then verify state=TERMINATED via getWarrantList, only then deleteWarrant
- **Storage path**: Save under `~/knowledge/li/Ericsson/` as `Ericsson_LI_{Operation}_SOAP_Sample_2dot1.md` — NOT under li/projects/
- **Reference file**: `references/ericsson-soap-crud-comparison.md` (5-operation comparison table)

**For ZTLIG → LI-IMS backend workflow (Kafka pipeline):**
- Overall pipeline: Web UI → Kafka → ztlig1(HI1设控) → LI侧网元 → ztlig2(HI2解析IRI) + SSF(HI3信令) + RVF(HI3媒体) → Kafka(TMC_REALTIME + TMC_OFFLINE) → Flink(Realtime + Afterwards) → Web展示
- ztlig1.xxx.txt: HI1设控/解控日志（消费Kafka → 发往LI → 接收响应 → 回写Kafka）
- ztlig2.xxx.txt: HI2 IRI解析日志
- ssf.xxx.txt: SIP/ISUP信令分析日志
- rvf.xxx.txt: RTP媒体分析日志
- Flink realtime: TMC_REALTIME → TargetRealTimeMsg（实时IRI展示）
- Flink afterwards: TMC_OFFLINE → business_listen（存入数据库持久化）
- 语音文件规则: Liid.cin.callermsisdn.calledmsisdn.direction, ts切片+m3u8播放
- 实时语音同步: 200bytes/s限速本地拷贝; 离线语音: FTP同步
- 厂商debug: `ztsh` → `debug ztlig1 300 {vendor_code} on`
- 已知厂商代码: ericlis24(Ericsson), zeel(Airtel), utimaco(Glo)
- Kafka recv日志: isDel=0(添加)/1(删除); Kafka rsp日志: ret=0(成功)/1(失败)

**For Vendor Config references (ztlig.cfg/LIMS):**
- Organize by config block: NE-COM → VNE-COM → LEA → Process(ZTLIG1/2/3/SSF/RVF)
- For each block: name, type, default, meaning, range, restart scope, attribute(C/M/O)
- Vendor-specific sub-sections (NE-HW, NE-ZTE, NE-NSN, NE-ERIC, NE-UTIMACO, NE-GROUP2K, NE-ZEEL)
- Include actual default values and valid ranges
- Add "notes" section for version-specific requirements

**For Operations Manuals:**
- System architecture (processes, data flow)
- Per-process configuration (kafka topics, IPs, ports)
- Version upgrade procedures
- On-site inspection commands
- Log analysis and common ERRORs
- Deployment scenarios

### 3. Domain-Specific Terminology to Use Correctly

| Term | Description |
|------|-------------|
| LIID | Lawful Interception Identifier, unique per target |
| CIN | Call Identification Number, correlates X2 and X3 |
| ICID/imsChargingID | IMS Charging Identifier, correlates IRI within session |
| LIOID | 32-bit unsigned int, unique per LI target per NE (5GC X interface) |
| X1 | Command channel (ADMF→NE, TCP/IP + ASN.1 BER, LIG主动连NF) |
| X1M | Certificate management channel (NE→ADMF, HTTP/HTTPS, NE主动连ADMF) — 5GC 新增 |
| X2 | Signaling plane (NF→DF2, IRI reports, TCP + ASN.1 BER encoded) |
| X3 | Media plane (UPF→DF3, UDP/TCP, RTP/IDP) |
| TNEType | 网元类型标识：UDM(105), UNC(162,含AMF/SMF), UDG(163,含UPF), USN(160,含MME/SGSN) — 5GC 特有 |
| FUNCType | 功能实体标识。Bit7=0 传统方式(GGSN/P-GW/S-GW/MME/SGSN)，Bit7=1 5GC方式(AMF 0x81/SMF 0x82/SMSF 0x83/UPF 0x84) |
| UNC | Universal Network Controller — 5GC 集成 AMF/SMF/SMSF/MME/SGSN 等 |
| UDG | Universal Distributed Gateway — 5GC 集成 UPF/S-GW-U/P-GW-U/GGSN-U 等 |
| SSF | SIP-I session management |
| RVF | RTP media processing |
| 0x91 | AddressString indicator byte (international + E.164) |

### 4. Common Pitfalls

- **Don't assume one format**: Different vendors (hw/zte/ericsson/nsn) have different ASN.1 for X2 reports
- **BER length encoding**: Length > 127 must use 0x81 prefix (e.g., 255 bytes → `0x81 0xFF`)
- **5GC vs EPC 接口混用**: 5GC 新增 X1M 接口(证书管理，NE主动连ADMF via HTTP/HTTPS)，而 X1 保持 ADMF→NE(TCP+BER)。FUNCType 的 Bit7=1 编码(AMF 0x81/SMF 0x82/SMSF 0x83/UPF 0x84)仅在 5GC 有效，传统 EPS 用 Bit7=0。集成 NF 仅允许 1 个 X1 + 1 个 X1M 通道，但允许多个 X2/X3 通道
- **MSISDN decoding**: Contains 0x91 indicator byte that must be stripped
- **e164-Format**: Carries T/L fields, must parse T/L before value
- **SIP-I vs SIP mode**: SIP-I message contains ISUP with Access Transport carrying LIID+CIN; pure SIP uses different correlation
- **Multi-TMC mode**: ztlig_target.txt grows from 23 to 25 fields (mcliid + imsi)
- **⚠️ Vendor API typos — don't copy blindly**: Vendor API documentation (OWLS, SICMS, etc.) often contains typos in enum values, field names, and examples. e.g., OWLS `protocol` enum lists `IMIS` instead of `IMSI`. When documenting vendor API specs, flag such typos with a note (e.g., "疑似拼写，标准写法为 IMSI") and offer to correct them — do not replicate them verbatim without annotation. The user will likely want the standard form.

### 5. Directory Integration Workflow ("学习并整合")

When the user asks to "学习并整合" a directory:

1. **List files**: `ls -la --time=ctime {dir}` — note ctime to spot new files
2. **Read each file** not yet processed — check for images-only docs (screenshots with no text content)
3. **Categorize content**:
   - Already covered in existing notes → skip
   - New, unique content → extract key information
   - Large documents with images (screenshots) → save as-is with TOC summary
   - Background context (OWLS, etc.) → save as reference, note in index
4. **Update/create knowledge notes**:
   - Vendor-specific X1 SOAP docs → `{vendor}1口对接调试文档.md`
   - Configuration tables → merge into existing skill/note
   - OWLS/backend manuals → save as `{System} {type}.md`
5. **Update** `references/knowledge-base-index.md` with new notes
6. Report to user: what was new, what was skipped, what was updated

### 12. Knowledge Base Reorganization Pattern

When the user asks to create a new directory and migrate related knowledge:

1. **Identify content scope** — ask or confirm what "programming knowledge" means in the user's context (coding standards, AI tools, database, MCP, etc.)
2. **Create the new directory** with subdirectories for each content category
3. **Copy files** (not move initially) from their original locations
4. **Create `_index.md`** per subdirectory with summary table and wikilinks
5. **Replace originals with redirect notes**:
   ```markdown
   > **此文档已迁移至 [[program-info/{category}/{file}]]**
   >
   > 新路径: `~/knowledge/program-info/{category}/{file}`
   ```
6. **Add cross-references** between related files at the new location
Run **`kb-index`** to update semantic search
8. **Report the new structure** to the user with a tree listing

**Known reorganization patterns:**
- `program-info/` — 编程相关知识（编码规范/AI编程工具/MCP/Python/Java/数据库/开发运维/开源生态）
- `hi2/厂商对接/` — 厂商LI协议对比文档
- `li/Ericsson/` — Ericsson LI-IMS 完整文档集（SOAP样本 + MSS17A + 工作流）
- `li/projects/a1-project/` — A1项目专属配置/运维

When documenting ztlig.cfg or similar config files:

1. **Create table with columns**: 配置项名称, 类型, 默认值, 含义, 取值范围, 需重启进程, 属性(C/M/O)
2. **Order by config block**: GLOBAL → LICENSE → NE-COM → VNE-COM → LEA → Process sections
3. **Vendor-specific sub-sections**: Under NE-COM add NE-HW, NE-ZTE, NE-NSN, NE-ERIC, NE-UTIMACO, NE-GROUP2K, NE-ZEEL
4. **Add "注意事项"** after each table for version/attribute-specific requirements
5. **Include real default values** and valid ranges — not placeholders

### 7. SOAP/WebService X1 Documentation Pattern

For vendors using SOAP (Ericsson LI-IMS):

1. Document WSDL binding → portType → message → element trace path
2. Show cross-file XSD reference resolution
3. Document request structure as tree: `Operation → arg0 → header + body + dtl`
4. Key fields with legal values tables
5. Bitmask fields with per-NE-Type support tables
6. Login → sessionID → authenticated operations flow
7. Reference to XML template files in source directory

**Ericsson External API WS 16A reference:** See `references/ericsson-external-api-ws16a.md` for full API service hierarchy (22 services), WarrantItem field definitions, supplementaryInfo bitmask, positioningPeriod enum, response/request code tables, and authentication flow. Also covers dtlWarrantNeTypeItem (NE-level warrant detail), NeService (10 operations), and ImsMonitorService. This file was generated from CXC1373777 R6A/R8A External_API_WebServices tar package.

### 8a. Multi-Document Vendor Interface Synthesis ("批量化合" 模式)

When the user sends multiple related vendor interface documents (e.g., HI1 + HI2 + HI3 for the same domain), synthesize them into ONE comprehensive reference instead of separate files:

1. **Create a cross-interface architecture diagram** showing how the interfaces relate (e.g., HI1→NE→HI2→LEMF, HI3→LEMF)
2. **Create per-interface subsections** with:
   - Transport protocol (Telnet/SSH/ASN.1 BER/ISDN/SIP-I)
   - Key parameters and tags
   - Event/command tables
3. **Add a correlation section** showing how fields flow between interfaces:
   - HI1 LIID → HI2 LIID → HI3 Calling Party Subaddress[1]
   - HI1 HI3A → HI3 Called Party Number (LEMF address)
   - HI2 CID → HI3 Called Party Subaddress[2] (CIN)
   - HI1 SPEECHTYPE → HI3 Mono/Stereo mode
4. **Link to existing vendor reference files** (e.g., zte-epc-field-mapping.md, ZTE_V3V4_LIS_ReturnCode状态码)
5. **Save the synthesized reference** as `references/{vendor}-{domain}-three-port.md` under this skill, NOT as a separate knowledge base file in `~/knowledge/`. The knowledge base gets the detailed per-interface document; the skill reference gets the cross-interface synthesis for runtime lookup.

**Known vendor synthesis patterns already in skill references:**
- `references/zte-cs-li-three-port.md` — ZTE CS domain HI1+HI2+HI3
- `references/utimaco-lims-rai-quickref.md` — Utimaco LIMS RAI protocol
- `references/zte-epc-field-mapping.md` — ZTE EPC HI2 ASN.1 field mapping (in `zte-li` skill)

## 8. User-Provided Knowledge Workflow ("学习" 模式)

When the user pastes knowledge directly (vs reading from a directory), use this workflow:

1. **Identify content class** from the content types table above — pick the most fitting storage path
2. **Determine project affiliation** — ask or infer from IPs/names (215.152.1.x = A1项目)
3. **Add project-specific ⚠️ banner** if any environment-specific values exist
4. **Structure the note** with sections in this order:
   - YAML frontmatter (tags + project tag)
   - Project warning banner (if applicable)
   - Connection/env info (table format)
   - Operations grouped by scenario (tables with commands)
   - Troubleshooting / FAQ
   - Quick reference template table
   - Wiki links to related notes
5. **Update the index** `references/knowledge-base-index.md` with the new note
6. **Run kb-index** to update semantic search (注: kb-index 替代了旧的 enzyme，全本地运行无需 LLM 连接)
7. **Handle supplementary/version-comparison info**

8. **Piece-by-piece content delivery**: When the user sends document content one piece at a time (e.g., Description → Syntax → Arguments for the same command, spread across multiple messages):
   - Acknowledge each piece and confirm you're tracking it
   - Update the knowledge note **incrementally** using `patch` after each relevant piece, rather than rewriting the whole file each time
   - **Exact English wording is critical** — the user will correct even minor word discrepancies (e.g., "horizontal accuracy" vs "horizontal accurancy"). Do NOT use abbreviated descriptions like "Same semantics as X" unless the user explicitly asks for it. Each parameter's description must match the original document verbatim.
   - If the user shares content that **revises** what you previously documented (e.g., corrects a command syntax), patch the KB note immediately
   - When the user sends **empty or single-word signals** (e.g., "?", "unchanged", "characters") after a partial update, apply the word to the note and continue waiting — do not prompt them or try to batch-complete
   - Only batch-write when the user signals they're done (e.g., by saying "OK" or moving to a new topic)
   - **Handle duplicate content gracefully**: If the user shares the same document twice (e.g., pasting the same section again), just state "already covered" without re-writing or re-summarizing.
   - **⚠️ patch 唯一上下文坑**: 当同一知识库笔记包含多个相同结构（如多个命令的状态码表都有 `| 0 | 成功 |`），`patch` 会报 `Found 2 matches` 错误。必须在 old_string 中包含更多唯一上下文（如章节标题+完整表头）来区分。最佳实践：使用该状态码表所在章节的完整头（`#### 状态码\\n\\n| 码...`）作为上下文前缀。
   - **⚠️ patch 结构损坏风险**: 当 old_string 匹配到的内容跨越多行分隔符（如 `---` 或空行），patch 可能意外消耗相邻的结构元素（如 `---` 分隔线、下一章节的 `##` 标题）。表现：下一节标题消失、两个章节被合并、代码块 closing ```` ``` ```` 被替换为文本。修复方法：立即 `read_file` 检查受影响区域，然后使用更大范围的上下文字符串修复。如果多次修复失败，直接读取整个文件后重写受影响的段落。
   - **⚠️ 状态码表逐段录入陷阱**: 当用户从文档中逐段分享状态码（每次几个码值，跨越多页共 150+ 条），且同一笔记中多个命令有自己的状态码子表时，每加一个码值都要匹配到正确的子表。如果单纯用 `| 码 | 含义 |` 做上下文会因为多处匹配而失败。最佳实践：用该码表前的章节 description 行（如 `\\`tmod\\` 命令可返回以下状态码`）作为唯一上下文锚点。

**Additional content types** not yet in the classification table:

| Content type | Storage path | Example |
|-------------|-------------|---------|
| A1 project ops cheatsheet | `知识/li/projects/a1-project/A1项目{组件}操作手册.md` | A1项目Gremlin查询手册 |
| CLI command reference | `知识/telecom/lawful_interception/{组件}运维与CLI命令速查.md` | Kafka-Manager运维与CLI命令速查 |
| API query manual | `知识/telecom/lawful_interception/{平台}-API查询手册.md` | Zabbix-API查询手册 |
| DB connection reference | `知识/telecom/lawful_interception/{系统}-{数据库}连接.md` | ZTLIG-MySQL数据库连接 |
| Packet capture guide | Append to `ZTLIG运维手册.md` as appendix | 抓包命令与调试维护 |
| **Task inventory / crontab manifest** | `知识/li/projects/{project}/{project}离线任务清单.md` | A1项目OWLS离线任务清单(RelationGraph) — 含 crontab、脚本清单、升级替换规则、SNS数据流 |

### 9. Project-Specific Marking (Critical)

When saving operational knowledge that contains IP addresses, ports, topic names, table names, or any environment-specific identifiers:

1. **Determine which project** the content belongs to (ask user if not clear)
2. **Determine if it's vendor-specific vs project-specific**: Ericsson LI-IMS integration docs go under `li/Ericsson/`; project deployment configs go under `li/projects/{project_name}/`. If you misplace a file, the user will correct you — move it immediately.
3. **Add warning banner** at the top of the note:
   ```markdown
   > ⚠️ **项目专属说明**
   > 本文档中的 IP 地址/端口/Topic 名称等均为 **{项目名}** 专属。
   > 其他项目（OWLS、ZTLIG 等）使用前必须人工确认。
   ```
3. **Tag accordingly** in frontmatter: `a1-project`, `owls`, `ztlig` etc.
4. **Annotate every IP/table/topic** in the note body with `(项目名)` where ambiguous
5. **Never assume** that IPs, service names, or table structures carry across projects

**Known project identities:**
- **A1 项目**（苏丹/北苏丹）— LIG01~LIG07 (215.152.1.20~26), rhino01~rhino09, bigdata cluster
- **OWLS** — 后端操作平台
- **ZTLIG** — Sinovatio 中新赛克拦截网关（注意：ZTLIG 本身跨项目，但具体配置属于各项目）

### 9. Quick Template: User-Provided Knowledge Notes

When the user pastes operational knowledge and says "学习" (learn):

```markdown
---
tags:
  - telecom/lawful_interception
  - {component}
  - {project}
  - ops
created: {date}
---

# {Title} ({project} 场景)

> ⚠️ **项目专属说明**
> ...

## 1. 基础信息

{connection info, paths, credentials}

## 2. 核心操作

{commands in tables}

## 3. 常见问题

{troubleshooting}

## 4. 快速查询模板

| 场景 | 命令 |
|------|------|

## 关联文档

- [[related note 1]]
```

### 10. Verification

- After writing, read back the note to ensure structure is correct
- Link-related notes using Obsidian `[[wikilink]]` syntax
- Confirm code block formatting renders correctly (no escaped quotes)
- Remove duplicate sections if multiple edits accumulate
- **Mark project-specific notes** with ⚠️ in the index
- After session, update `references/knowledge-base-index.md` with any new notes created
- The `references/li-quick-ref.md` in this skill is the canonical single-file quick reference — extend it with new field values, error codes, and operations as they appear
