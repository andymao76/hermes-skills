# LI Knowledge Base — Current Notes Index

知识库路径: `知识/telecom/lawful_interception/`
> 最后更新: 2026-06-30

| # | 笔记 | 字数 | 说明 |
|---|------|------|------|
| 1 | 华为LI技术文档索引.md | ~2.5K | **顶层索引** — 华为 LI 体系文档全景 |
| 2 | 华为ETSI合法拦截标准_57_Lawful_Interception.md | ~2.5K | ETSI/3GPP 标准在 USN9810 上的实现 |
| 3 | 华为监听操作手册.md | ~2K | LI 产品内部开发运维指南 |
| 4 | 华为CGP维护宝典.md | ~1.6K | CGP 平台维护案例与信息收集 |
| 5 | 华为EPC信令协议分析手册.md | ~2.1K | EPC/NAS/S1AP/Diameter 全信令流程 |
| 6 | 华为VoLTE信令分析手册.md | ~2.8K | VoLTE/IMS/SIP 全信令流程 |
| 7 | 华为ETSI监听搭建手册.md | ~2K | ETSI 标准监听(VoBB/RCSe/VoLTE)搭建 |
| 8 | 华为LICI特通监听搭建手册.md | ~2.3K | 中国特通(LICI)监听搭建 |
| 9 | 华为SVC_VoLTE_ETSI监听方案.md | ~4.6K | IMS 方案原理 |
| 10 | 华为SVC_IMS_X2报告抓包示例.md | ~13.7K | IMS X2 13步VoLTE呼叫完整解码 |
| 11 | 华为CS_X接口说明与ZTLIG部署实战.md | ~20K+ | CS X1+X2+X3 全接口 + BER编码 + 实战日志 |
| 12 | ZTLIG运维手册.md | ~65K | **旗舰文档** — ZTLIG 完整运维(含附录6个: cmf/DPDK/SICMS/抓包/地址映射) |
| 13 | TMC系统工勘指导.md | ~4.4K | LI 系统开局工勘模板 |
| 14 | 爱立信1口对接调试文档.md | ~8K+ | Ericsson LI-IMS SOAP 接口 |
| 15 | HI2和标准.md | ~10K | HI2 ASN.1 解码 + 标准对比 |
| 16 | LI_ASN1解码工具_000000app_v1分析.md | ~4.3K | ASN.1 解码工具分析 |
| 17 | OWLS Operation Manual.md | ~88K | OWLS 后端操作手册 V4.6 |
| 26 | hw-svc-5gc-li-x-interface.md | ~4.6K | **5GC SVC LI** — X1/X1M/X2/X3 协议栈, TNEType/UNC/UDG/USN, FUNCType 5GC编码, 部署与安全要求 |
| 27 | hw-dkba1421-cs-ims-etsi-li.md | ~10.5K | **CS&IMS ETSI LI** — DKBA1421 2016版, X1/X2/X3, IMS监听(imsGenIRIReport), mAGCF, X3 IPCC模式, NEID编码 |
| 28 | owls-target-management-api.md | ~3.2K | **OWLS API** — 设控目标查询接口(queryActiveTargetInfo/queryAllTargetInfo), type/protocol枚举 |
| 29 | hi2/厂商对接/Utimaco_LIMS_RAI_v16.1_协议规范.md | ~20K | **Utimaco LIMS RAI** — 德国Utimaco TS GmbH, LIMS远程管理二进制协议(端口52134), RAI-SP+RAI-CL, ICD/Target/MC/NE命令体系, 86种TargetType, Flags体系 |
| 30 | hi2/厂商对接/ZTE_CS_LI_HI1_HI2_HI3_三接口规范.md | ~18K | **ZTE CS LI三接口** — ZXUN LIG CS域HI1(65xx CLI命令)+HI2(ASN.1/BER IRI)+HI3(ISDN/SIP-I CC), 三级用户体系, 10种事件, 关联数据流 |
| 31 | 5g-li-standards-evolution.md | ~6.5K | **5G LI标准演进** — 毛恒镇《LI标准和演进》, 3GPP SA3-LI新规范(33.126/127/128), ETSI TS 103 221(X1/X2/X3), TS 102 232(HI2/HI3), 5G NF(AMF/SMF/UPF/UDM/SMSF) |

**A1 项目专属笔记 (⚠️ 不适用于 OWLS/ZTLIG 等其他项目):**

| # | 笔记 | 字数 | 说明 |
|---|------|------|------|
| 18 | Kafka-Manager运维与CLI命令速查.md | ~8K | Kafka Manager/topic/consumer group |
| 19 | Kafka-Business-Topic查询模板与字段速查.md | — | Business Topic 字段解析 |
| 20 | A1项目Gremlin-JaniusGraph操作手册.md | ~10K | JanusGraph Gremlin 查询 |
| 21 | A1项目Greenplum-psql查询手册.md | ~6.5K | GP psql CLI + 设控库查询 |
| 22 | ZTLIG-MySQL数据库连接.md | ~1.4K | MySQL ztlig_target 连接 |
| 23 | Zabbix-API查询手册.md | ~5.5K | Zabbix API 监控查询 |
| 24 | AI编程Skill体系参考.md | ~3.6K | 通用：AI 编程 Skill 分类参考 |
| 25 | greenplum-commands-cheatsheet.md(更新) | ~9K | 通用：GP 运维速查表(已增psql+会话管理) |
| 32 | A1项目OWLS离线任务清单(RelationGraph).md | ~6K | **新增** — crontab+processD+dt/脚本+SNS数据链路+升级替换规则 |

## 笔记分类原则

| 类型 | 命名规则 | 示例 |
|------|----------|------|
| 方案原理 | `华为{厂商}_{技术}方案.md` | 华为SVC_VoLTE_ETSI监听方案 |
| 抓包解码 | `华为{厂商}_{接口}抓包示例.md` | 华为SVC_IMS_X2报告抓包示例 |
| 接口+运维 | `华为{厂商}_{接口}说明与{系统}部署实战.md` | 华为CS_X接口说明与ZTLIG部署实战 |
| 系统手册 | `{系统}运维手册.md` | ZTLIG运维手册 |
| 工勘模板 | `{系统}工勘指导.md` | TMC系统工勘指导 |
| 厂商接口 | `{厂商}{接口}对接调试文档.md` | 爱立信1口对接调试文档 |
| 后端手册 | `{System} Operation Manual.md` | OWLS Operation Manual |
| 标准演进 | `{topic}-standards-evolution.md` | 5g-li-standards-evolution.md |
| **A1项目专属** | `A1项目{组件}操作手册.md` | A1项目Gremlin查询手册 |
| **A1项目专属** | `{组件}-{功能}命令速查.md` | Kafka-Manager运维与CLI命令速查 |
| **A1项目专属** | `{组件}-API查询手册.md` | Zabbix-API查询手册 |
| **A1项目专属** | `A1项目{组件}离线任务清单.md` | A1项目OWLS离线任务清单(RelationGraph) |

## A1 项目服务器速查

| 节点 | IP | 角色 |
|------|-----|------|
| LIG01 | 215.152.1.20 | CS (SU-CS) |
| LIG02 | 215.152.1.21 | CS (ZAIN-CS) |
| LIG03 | 215.152.1.22 | CS (MTN-CS) |
| LIG04 | 215.152.1.23 | PS (SU-PS) |
| LIG05 | 215.152.1.24 | SICMS (DPI) |
| LIG06 | 215.152.1.25 | PS (ZAIN-PS) |
| LIG07 | 215.152.1.26 | PS (MTN-PS) |
| rhino01~09 | — | 大数据/Kafka 集群 |
| 站点B(CS) | 192.172.16.20~22 | 仅有 CS 节点 |

## 相关资源

- skill `telecom-li-documentation` — LI 文档编写规范
- skill `janusgraph-expert` — JanusGraph 通用技能
- `~/knowledge/research/greenplum-commands-cheatsheet.md` — GP 通用运维
