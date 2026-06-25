# Ericsson CXC1373777: R4A vs R6A 版本对比

## 文件概况

| 版本 | 文件数 | 版本目录 | 来源 |
|------|:------:|:--------:|------|
| R4A | 596 | 7 个（1, 1dot8, 2dot1, 12A, 13A, 14B, 16A）| `~/knowledge/li/Ericsson/CXC1373777_16_R4A.0_External_API_WebServices.tar` |
| R6A | 672 | 8 个（+2dot4）| `/home/andymao/tempfile/Ericsson/CXC1373777_16_R6A.0_External_API_WebServices.tar` |

## 核心结论

R4A 和 R6A 的 **16A（最新版）WSDL/XSD 字节级相同**：
- `warrantservice_schema1.xsd`: 均为 26390B
- `warrantservice.wsdl`: 均为 18147B
- `sessionservice.wsdl`: 均为 3308B
- `neservice.wsdl`: 均为 12798B

**两版本间无协议级别差异。** R6A 仅新增 `External_API_WS_2dot4` 目录（21 个 WSDL，与 2dot1 服务集相同，无新服务上线）。

## API 版本演进（7 个版本目录）

| 版本 | WSDL 数 | FD 变体 | 关键变化 |
|------|:-------:|:-------:|----------|
| **1** | 24 | 0 | 基础版，含 WarrantoService12/13 |
| **1dot8** | 24 | 0 | 细化，增加 limitedstring_schema |
| **2dot1** | 21 | 0 | 精简版 — 移除 WarrantoService12/13 和 lemfservice1 |
| **12A** | 24 | 0 | 新增 AliasService + TargetAliasService |
| **13A** | 29 | 6 | 多条 FD 分支（Neservice FD1/FD2, Lemfservice FD2, Mcnbservice FD2, Auditwarrant FD2）|
| **14B** | 28 | 5 | 整合审计服务，exception/list/response 独立 schema |
| **16A** | 27 | 6 | 最新完整版 — 新增 WarrantoService FD1/FD2, Lemfservice FD1/FD2, Mcnbservice FD1/FD2；移除 TargetAliasService 和 aliasservice（功能合并）|

## 服务一致性表

| 服务 | 1 | 1dot8 | 2dot1 | 12A | 13A | 14B | 16A |
|------|:-:|:-----:|:-----:|:---:|:---:|:---:|:---:|
| SessionService | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| WarrantService | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| WarrantService FD1/FD2 | | | | | | | ✓ |
| NeService | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| NeService FD1/FD2 | | | | | ✓ | | |
| McService / McnbService | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| McnbService FD1/FD2 | | | | | ✓ | ✓ | ✓ |
| AliasService | | | | ✓ | ✓ | ✓ | |
| TargetAliasService | | | | ✓ | ✓ | ✓ | |
| ImsMonitorService | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| UtilityService | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| LeaService / LeaService12b | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| LemfService / FD1/FD2 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| PayloadFilterService | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| CountersService | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| AclService | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| IntGroupService | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| SuppNeService | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| FeatureCacheService | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| IriccService | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| AuditWarrantService | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| AuditWarrantService FD2 | | | | | ✓ | | |
| NeGroupService | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| WarrantDtlService | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| WarrantMcService | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| WarrantMcnbService | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

## 已知部署版本

- **埃塞俄比亚 A1 项目现场**：曾使用 14B 版本，后升级至 V2.3（端口 65211 → 8443），平台从 CORBA 迁移到 Web API

## 相关笔记

- `~/knowledge/telecom/lawful_interception/Ericsson_IMS_LI_External_API_WebServices_R6A.md` — 完整 API 文档
- `~/knowledge/li/Ericsson/` — 原始 tar 包 + 调试手册 + 踩坑记录
