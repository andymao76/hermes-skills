此文件位于知识库路径：
- `~/knowledge/telecom/GTP_PFCP完整消息库速查手册.md` (1,289行/62KB)
- Obsidian: `知识/telecom/GTP_PFCP完整消息库速查手册.md`

内容覆盖：

**PART 1 — GTPv1-U (TS 29.281)**
- 8字节固定头结构（Version/PT/E/S/PN/Message Type/Length/TEID/Seq#）
- 消息类型：Echo(0x01)、Error Indication(0x04)、End Marker(0x06)、G-PDU(0xFE)
- 扩展头：PDU Session Container(0x85)、NR RAN Container(0x86)、PSCell Info(0x87)等

**PART 2 — GTPv2-C (TS 29.274)**
- 消息类型表：Echo→Create/Modify/Delete Session→Bearer Mgmt→DDN→CS Paging等
- 关键IE表：IMSI(1)、Cause(2)、F-TEID(87)、Bearer Context(93)、ULI(157)等
- Cause值表：Request Accepted(16)、System failure(86)、No memory(71)等
- LTE Attach 15步完整流程图

**PART 3 — PFCP (TS 29.244)**
- 消息类型：Session Est/Mod/Del/Report、Heartbeat、Association Setup/Update/Release
- 核心规则：PDR(PDI/F-TEID)→FAR(Action/Destination)→URR(Volume/Time)→QER(Gate/QFI)→BAR→MAR
- 关键IE类型码：CREATE_PDR(1)、CREATE_FAR(2)、CREATE_URR(3)、CREATE_QER(4)、PDI(16)、SDF_FILTER(10)、FULL_TEID(21)
- 6个ASCII流程图（Association/Session/Modification/Deletion/Report）
