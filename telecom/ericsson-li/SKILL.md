---
name: ericsson-li
description: 爱立信合法监听(Ericsson LI) — MSS17A CS 域 COD X1 命令(28个)+X2/X3输出 + IMS SOAP API (External API WS) + ZTLIG Kafka 对接 + CURL 实战 + 故障排查
category: telecom
tags: [Ericsson, LI, 合法监听, X1, SOAP, WSDL, XSD, External API, WarrantService, SessionService, IMS, IRI, LEMF, MCNB, NE, createWarrant, SoapUI]
triggers:
  - user mentions: 爱立信监听, ericsson li, ericsson x1, 爱立信SOAP, External API
  - user mentions: WarrantService, createWarrant, SessionService, IMS LI External API
  - user mentions: CXC1373777, warrantservice.wsdl, Hi-Path, ETSI LI 爱立信
  - user mentions: 爱立信X1, Ericsson HI1, SOAP WSDL, 爱立信 设控
  - user mentions: MSS17A, COD, POD, IWD, RCEOUTM, RCEFILE1, RCEMAA, RCELEDA
  - user mentions: RCMCI, RCSUI, RCARI, RCMUI, RCHMI, RCSUE, RCMUE
  - user mentions: 爱立信MSC, 爱立信CURL, TMC_TARGET_INFO, ZTLIG eric, 爱立信X2/X3
---

# Ericsson LI — IMS LI External API (X1 SOAP/WebService)

## 概述

爱立信 IMS LI 系统的 X1 接口基于 SOAP/WebService（WSDL+XSD+properties），而非传统 TCP/ASN.1 或 CLI 方式。提供完整的 LI 搜查令远程管理接口。共 22 种 WebService，核心为 SessionService（登录认证）和 WarrantService（搜查令 CRUD）。

## 标准文档

- **文档编号**: CXC1373777 (R6A / R8A)
- **本地路径**: `/home/andymao/tempfile/Ericsson/CXC1373777_R6A/`
- **副本路径**: `/home/andymao/SmartBear/ericsson-x1-wsdl/`（可直接供 SoapUI 引用）
- **文件构成**: 672 个文件（WSDL + XSD + properties）

### 版本演进

| 版本目录 | WSDL | XSD | properties | 新增 |
|---------|:----:|:---:|:----------:|------|
| External_API_WS_1 | 24 | 38 | 21 | 基础版 |
| External_API_WS_1dot8 | 24 | 39 | 21 | limitedstring_schema |
| External_API_WS_2dot1 | 21 | 34 | 21 | **E-LIMS 参考项目使用**，getHostList + hosts field |
| External_API_WS_12A | 24 | 34 | 22 | AliasService, TargetAliasService |
| External_API_WS_13A | 29 | 43 | 22 | 多条 FD 分支 |
| External_API_WS_14B | 28 | 42 | 22 | exception/list/request/response schema 独立 |
| External_API_WS_16A | 27 | 39 | 21 | **最新版，最完整** |

## 服务体系（22 种 WebService）

### 基础服务
- **SessionService** — `login` / `logout`：入口认证，获取 sessionID
- **UtilityService** — 实用工具

### 搜查令管理（核心）
- **WarrantService** — 13 种操作，完整搜查令 CRUD
- **WarrantDtlService** — 搜查令详情
- **WarrantMcService** / **WarrantMcnbService** — 搜查令与 MC/MCNB 关联
- **AuditWarrantService** — 搜查令审计
- **TargetAliasService** — 目标别名

### NE（网元）管理
- **NeService** — 10 种操作，NE 查询/配置/Profile
- **NeGroupService** — NE 组管理
- **SuppNeService** — 补充 NE
- **IntGroupService** — 拦截组

### LEA / LEMF
- **LeaService** — `getLeaList`：执法机构查询
- **LemfService** — `getLemfList`：LEMF 查询

### IMS 监控
- **ImsMonitorService** — `getImsSWData`（软件健康）/ `getImsHWData`（硬件健康）

## WarrantService 核心操作（13种）

| 操作 | SOAPAction | 说明 |
|------|-----------|------|
| `createWarrant` | `urn:CreateWarrant` | **创建搜查令（X1 初始化核心）** |
| `modifyWarrant` | `urn:ModifyWarrant` | 修改搜查令 |
| `deleteWarrant` | `urn:DeleteWarrant` | 删除搜查令 |
| `getWarrantList` | `urn:GetWarrantList` | 查询搜查令列表 |
| `getWarrantPosition` | `urn:GetWarrantPosition` | 获取定位 |
| `getLinkedWarrantList` | `urn:GetLinkedWarrantList` | 关联搜查令 |
| `getDtlWarrantNeTypeList` | `urn:GetDtlWarrantNeTypeList` | 按 NE 类型查详情 |
| `getWarrantNasCtxList` | `urn:GetWarrantNasCtxList` | NAS 上下文 |
| `activateDynamicWarrant` | `urn:ActivateDynamicWarrant` | 激活动态搜查令 |
| `terminateDynamicWarrant` | `urn:TerminateDynamicWarrant` | 终止动态搜查令 |
| `deleteDynamicWarrant` | `urn:DeleteDynamicWarrant` | 删除动态搜查令 |
| `getDynamicWarrantList` | `urn:GetDynamicWarrantList` | 动态搜查令列表 |
| `activateListAllPhoneOnDemand` | `urn:ActivateListAllPhoneOnDemand` | 按需定位 |
| `retrieveWarrantOVStatus` | `urn:RetrieveWarrantOVStatus` | 查询 OV 状态 |

## X1 初始化流程

```
Step 1: SessionService.login      → 获取 sessionID
Step 2: WarrantService.createWarrant  → 创建搜查令（warrantID=-1 由系统分配）
Step 3: WarrantService.getWarrantList → 验证创建结果
Step 4: WarrantService.deleteWarrant  → 清理（可选）
```

## SOAP 请求结构

### 命名空间（1dot8 版本）

| 前缀 | 命名空间 |
|------|---------|
| `sess` | `http://session.bind.external.ws1dot8.ims.epa.ericsson.se/` |
| `war` | `http://warrant.bind.external.ws1dot8.ims.epa.ericsson.se/` |
| `nrq` | `http://request.header.bind.ws1dot8.ims.epa.ericsson.se/` |
| `nrs` | `http://response.header.bind.ws1dot8.ims.epa.ericsson.se/` |
| `nsx` | `http://utility.bind.ws1dot8.ims.epa.ericsson.se/` |

### requestHeader 结构
```xml
<header>
  <type><__value>int</__value></type>   <!-- 0=CHECKED_CREATE, 1=CREATE, 2=DELETE, 3=LIST, 4=MODIFY, 5=VIEW, 6=WARRANT_AUDIT -->
  <userID>string</userID>
  <sessionID>string</sessionID>
</header>
```

### createWarrant 请求嵌套结构
```
createWarrant
  └── arg0 (warrantCreateRequest)
        ├── header         → requestHeader
        ├── item           → warrantItem
        └── dtlWarrants    → dtlWarrantNeTypeItemArray[]
              └── item[]   → dtlWarrantNeTypeItem
```

### warrantItem 关键字段

| 字段 | 类型 | 创建值 | 说明 |
|------|------|--------|------|
| warrantID | int | **-1** | 创建时必填 -1，系统分配 |
| targetNumber | string | MSISDN | 目标号码 |
| targetTypeID | string | "1" | 目标类型 |
| neName | string | NE名 | 所属 NE 名称 |
| lea | string | LEA代码 | 执法机构 |
| MUID | string | 唯一值 | MUID |
| useOneLemf | short | 1 | 使用单一 LEMF |
| lemf | string | IP:Port | LEMF 地址 |
| isTargetPABX | boolean | false | PABX 目标标识 |
| legalBasis | string | 法律条款 | 法律依据 |
| caseID | string | 案件ID | 案件编号 |
| isTargetNumberSuppressed | boolean | false | 目标号码隐藏 |
| activationTime | long | Unix时间戳 | 激活时间（毫秒） |
| terminationTime | long | Unix时间戳 | 终止时间（毫秒） |
| supplementaryInfo | short | 0 | 补充信息位掩码 |
| GGSNMonitoring | boolean | false | GGSN 监控 |
| positioningPeriod | int | -1 | 定位周期：5/15/30/45/60/-1(禁用) |
| radiusWarrantId | int | -1 | RADIUS 关联 |

### dtlWarrantNeTypeItem

| 字段 | 类型 | 说明 |
|------|------|------|
| warrantID | int | -1（创建时） |
| neType | string | NE 类型（MSC/SIPSERVER/GPRS/HLR/FIX/5GCORE 等） |
| isDataMonitoringOnly | short | 0=IRI+CC, 1=仅IRI（详见枚举值） |
| targetInfo | short | 目标信息 |

### isDataMonitoringOnly 枚举值

| 值 | 含义 |
|:--:|------|
| 0 | IRI + CC |
| 1 | IRI only |
| 2~384 | 各种组合（详见 XSD warrantservice_schema1.xsd） |

### neType 枚举值

| 取值 | 节点 |
|------|------|
| "MSC" / "OV_MSC" | MSC 节点 |
| "HLR" / "OV_HLR" | HLR 节点 |
| "GPRS" / "OV_GPRS" | GPRS 节点 |
| "SIPSERVER" / "OV_SIPSERVER" | IPMM 节点 |
| "FIX" / "OV_FIX" | 固网节点 |
| "AAASERVER" / "OV_AAASERVER" | AAA 节点 |
| "5GCORE" | 5G Core 节点 |
| "HSS_GPRS" / "HSS_SIPSERVER" | HSS 节点 |

## 响应码

| 常量 | 值 | 说明 |
|------|:--:|------|
| BUSINESS_RULE_VIOLATION | 0 | 业务规则违反 |
| INTERNAL_ERROR | 1 | 内部错误 |
| INVALID_SESSION | 2 | 无效会话 |
| **SUCCESS** | **3** | **成功** |
| WARNING | 4 | 警告 |
| LOGOUT_SESSION | 5 | 会话已登出 |
| ORDERED | 6 | 已排队 |

## 响应结构
```xml
<return>
  <code><__value>3</__value></code>    <!-- 响应码 -->
  <reason>SUCCESS</reason>              <!-- 原因描述 -->
  <objectId>10001</objectId>            <!-- 返回的 warrantID -->
</return>
```

## SoapUI 测试

完整的 SoapUI 项目位于：
- **项目文件**: `/home/andymao/SmartBear/ericsson-x1-init.xml` (1dot8 版，已填入完整参数)
- **E-LIMS 参考项目**: `/home/andymao/SmartBear/E-LIMS-soapui-project.xml` (2dot1 版，模板占位符)
- **WSDL 副本**: `/home/andymao/SmartBear/ericsson-x1-wsdl/`
- **Python Mock**: `/tmp/ericsson-li-mock.py`（脚本已在 skill 中，参考 `scripts/ericsson-li-mock.py`）

### SoapUI 项目结构

#### E-LIMS 参考项目特征（External_API_WS_2dot1）
- 纯 WSDL 接口导入，**无测试套件**，**无 Mock 服务**
- WSDL 内容通过 `<con:definitionCache>` 嵌入项目 XML 中（SoapUI GUI 自动生成）
- 接口名 `WarrantServiceInterfaceSoapBinding` = WSDL binding name
- SOAP 请求模板使用 `?` 占位符，需手动填写
- 比 1dot8 多 `getHostList` 操作和 `hosts` 字段
- 命名空间: `http://warrant.bind.external.ws2dot1.ims.epa.ericsson.se/`

#### ericsson-x1-init.xml 项目特征（External_API_WS_1dot8）
- 包含 WSDL 接口 + 测试套件（4 个 TestCase） + MockService
- SOAP 请求已填入完整参数值（warrantItem 完整字段 + dtlWarrants）
- 命名空间: `http://warrant.bind.external.ws1dot8.ims.epa.ericsson.se/`

### SoapUI testrunner 已知限制

SoapUI 5.10.0 testrunner 在 CLI 模式下无法创建 `xsi:type` 测试步骤：
```
ERROR [WsdlTestCase] Failed to create test step for [Login]
WARN  [SoapUI] Missing interface [null] for MockOperation in project
```
**根因**: SoapUI 项目 XML 中使用 `xsi:type="con:WsdlTestRequestStep"` 等类型属性来指定步骤类型，但 CLI testrunner 的 XMLBeans 解析器无法实例化这些类型。**不受 Java 版本影响**（Java 17 和 Java 21 均复现）。

**影响范围**: `WsdlTestRequestStep`、`GroovyScriptStep`、所有 `xsi:type` 步骤类型。

**变通方案**:
1. **GUI 调试**: SoapUI GUI 中可正常创建和执行所有测试步骤
2. **Python Mock + curl**: 用 skill 中的 `scripts/ericsson-li-mock.py` + curl 命令行替代（已验证通过）
3. **直接 SOAP**: 用 `javax.xml.soap` 或 Groovy 脚本编程构造 SOAP 消息

### 项目 XML 注意事项
- 根元素**必须**声明 `xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"`，否则项目加载报 "The prefix xsi for attribute xsi:type is not bound"
- `definition` 属性建议用相对路径或 `file:` URI: `definition="file:sessionservice.wsdl"`
- 对于跨目录使用的项目，建议通过 SoapUI GUI 导入 WSDL，让 GUI 自动生成 `<con:definitionCache>` 内嵌内容

详见 `references/ericsson-x1-soapui-project.md`

SOAP Login 请求/响应样本详见 `references/ericsson-x1-soap-login-sample.md`（含 2dot1 实际 XML、16A 对比、返回码 1-12 含义）

## 调试工具
- **SoapUI** — WSDL 导入 → 可视化构造 SOAP 请求 → 直接 Send 到真实 LI-IMS
- **Python Mock** — 快速模拟 LI-IMS 响应，无需真实环境
- **curl** — 手动构造 SOAP XML 直接 POST 测试
- **Wireshark** — 抓包分析 SOAP over HTTP

## 已知重叠技能
- `hw-li`: 也覆盖 Ericsson 的部分对接配置（ztlig.cfg NE-ERIC 块），本 skill 专注 Ericsson LI 原生 X1 SOAP 接口
- `zte-li`: 类似 ZTE 专用 skill 模式

---

# Ericsson MSS17A CS 域 — X1/X2/X3 完整操作参考

> 对 MSS17A MSC 的 LI 操作，基于 MSS17A.7z 完整文档集（48文件/4文件夹）
> 本地文档位置: `/home/andymao/knowledge/li/Ericsson/MSS17A/`
> 完整 SOP 参考: `references/ericsson-mss17a-x1-x2-x3-sop.md`

爱立信 MSS17A 存在两套 X1 接口：
1. **MSC 命令行 COD** — 面向 CS 域的 CLI 命令（RCMCI/RCSUI 等 28 个命令）
2. **LIMS SOAP API** — 面向 IMS 域的 SOAP/HTTPS（见前文 External API 章节）

## X1 (HI1) — 28 个 COD 命令

### 监控目标设控（核心）

| 命令 | 功能 | 关键参数 |
|------|------|----------|
| **RCMCI** | 监控中心 Initiate — **最重要的设控命令** | MONB/IMEI/IMSI/EBNR/CA, MCNB, DT, MUID, CO |
| **RCMCC** | 监控中心 Change | - |
| **RCMCP** | MSC A号码 Change/Print | - |

### 监控用户管理

| 命令 | 功能 |
|------|------|
| **RCMUI** | 监控用户 Initiate |
| **RCMUE** | 监控用户 End |
| **RCMUP** | 监控用户 Print |
| **RCMUC** | 监控用户 Change |

### 移动用户监控（SU = Subscriber）

| 命令 | 功能 | 触发 X2 输出 |
|------|------|:------------:|
| **RCSUI** | 移动用户监控 Initiate | ✓ |
| **RCSUC** | 移动用户 Change | ✓ |
| **RCSUP** | 移动用户数据 Print | - |
| **RCSUE** | 移动用户 End（解控） | - |

### 监控区域 / HLR / MTAP

| 命令 | 功能 |
|------|------|
| **RCARI/RCARC/RCARE/RCARP** | 监控区域 Initiate/Change/End/Print |
| **RCMUI(CA)** | 移动用户监控区域 Change |
| **RCHMI/RCHME/RCHMP** | HLR 监控 Initiate/End/Print |
| **RCMRI/RCMRE/RCMRP** | MTAP 输出 Initiate/End/Status |

### 安全/密码/审计

| 命令 | 功能 |
|------|------|
| **RCPWI/RCPWC/RCPWP** | 密码 Initiate/Change/Print |
| **RCSAI** | 手动审计和同步 Initiate |
| **RCSAS/RCSAE/RCSAC/RCSAP** | 增强安全性 Initiate/End/Change/Print |

### 命令通用格式

```
COMMAND:PARAM=value[,PARAM=value...];
```
- Procedure Printouts: `EXECUTED` / `NOT ACCEPTED (fault type)`
- Fault type: `FUNCTION BUSY`, `FORMAT ERROR`, `UNREASONABLE VALUE` + FAULT CODE
- 命令在系统重启后保持 (order remains after system restart)

### 典型设控流程

```
Phase 1: RCMUI:MUID=LEA01,CO=1;            — 创建监控用户
Phase 2: RCMCI:MONB=8613800123456,          — 设控目标号码
                MCNB=861090001234,
                CO=1,DT=AVF-1,MUID=LEA01;
Phase 3: RCSUI:MUID=LEA01,CO=1;            — 开启 X2 数据输出
Phase 4: RCSUP:MUID=LEA01,CO=1;            — 验证状态

解控:
Phase 5: RCSUE:MUID=LEA01,CO=1;            — 停止数据输出
Phase 6: RCMUE:MUID=LEA01;                  — 删除监控用户
```

### RCMCI 故障码

| FCODE | 含义 | FCODE | 含义 |
|:-----:|------|:-----:|------|
| 4 | 未监控 | 30 | MCNB 已定义 |
| 7 | dumping | 31 | 仅 IRI |
| 8 | MUID 未监控对象 | 51 | IMSI 未监控 |
| 14 | MUID 未定义 | 70-77 | APC 处理器拥塞 |
| 17 | IMEI 未监控 | 83 | AVFNB 未定义 |
| 20 | 多用户未激活 | 88 | EBNR 未监控 |
| 21 | IMEI 监控未激活 | 92 | LI 保护未激活 |
| 23 | 必须指定 MUID | 94 | 用户名/密码错误 |
| 26 | MCNB ≠ MONB/EBNR | 107 | CA 未监控 |

## X2 (HI2) — 拦截数据输出（POD）

### IRD ASN.1 输出 (RCEOUTM)

- **Printout Block**: RCEOUTM
- **触发命令**: RCSUI, RCSUC, RCMCI, RCHMI
- **协议**: ASN.1 (ITU-T X.680/X.681/X.682/X.683/X.690)
- **顶层结构**: IRDmessage ::= SEQUENCE { timeStamp, softwareVersion, muInfo, controlInfo, eventInfo }

### RCEFILE1 文件输出 (RCEOUTF)

- **输出编码**: ISO characters, left-justified, filler=spaces
- **23 种记录类型**: Originating(1) ~ PRBT(22) + Reserved(23)
- **CALLID 格式**: `xxxxx-yy-zz` (MonitoredCallID-InterceptID_monitored-InterceptID_nonMonitored)

### IRD FaultCode

| FCODE | 含义 | FCODE | 含义 |
|:-----:|------|:-----:|------|
| 2 | MC 故障 | 13 | MC 号码未定义 |
| 4 | 超时无应答 | 14/15 | CB/连接拥塞 |
| 5 | 应答前释放 | 17 | 接入验证失败 |
| 7 | 队列溢出丢失 | 18-24 | 各种内部/超限/变更 |

## X3 (HI3) — 内部监控数据协议（IWD）

9 个 IWD 协议文档，覆盖：
- 监控数据输出协议 v16/v17（RCE Event/Event Resp/Output Status）
- 元素列表协议 v16/v17
- 监控业务协议 v12
- RCE 集群内部通信协议 V32
- RES 事件协议 v21

## Kafka TMC_TARGET_INFO 直接操作

### 添加目标
```json
{"restoreType":"TMC","targetId":100001,"type":"NUMBER",
 "account":"251970751035","permissions":"SIGNALING",
 "protocolType":"MSISDN","len":1,"officesIds":"5",
 "mapId":100001,"editFlag":0,"IT":"3","FD":"0","SPEECHTYPE":"",
 "HI2A":"10.45.10.18","HI2PORT":"32001",
 "HI2U":"ztlig8","HI2P":"ztlig1","HI2LINK":"","HI3A":"",
 "isDel":0}
```

### 删除目标（isDel=2）
```json
{"...": "...", "targetId":348900, "account":"970751035",
 "isDel":2}
```

## CURL 对接完整 SOP

### 环境准备
- LIMS V2.3+, X1 端口 8443（旧版 14B 用 65211 CORBA）
- ZTLIG 需 `eric_lis_v2dot1=1` License
- OpenSSL 1.0.2+
- `.cer` → `.jks` 证书转换

### 操作序列: Login → Add → GetList → Terminate → sleep 3s → Delete

```bash
# 1. Login 获取 sessionID (有效期5分钟)
curl -X POST https://<LIMS_IP>:8443/ws2dot1/services/SessionServicePort \
  -H "Content-Type: application/soap+xml" -k -d @login.xml

# 2. Add (warrantID=-1)
curl -X POST https://<LIMS_IP>:8443/ws2dot1/services/WarrantServicePort \
  -H "Content-Type: application/soap+xml" -k -d @add.xml

# 3. Get warrantID
curl -X POST https://<LIMS_IP>:8443/ws2dot1/services/WarrantServicePort \
  -H "Content-Type: application/soap+xml" -k -d @get_warrant_list.xml

# 4. Terminate + sleep 3s
curl -X POST https://<LIMS_IP>:8443/ws2dot1/services/WarrantServicePort \
  -H "Content-Type: application/soap+xml" -k -d @terminate.xml
sleep 3

# 5. Delete
curl -X POST https://<LIMS_IP>:8443/ws2dot1/services/WarrantServicePort \
  -H "Content-Type: application/soap+xml" -k -d @delete_warrant.xml
```

### 常见故障

| 现象 | 原因 | 解决 |
|------|------|------|
| License 错误 | 缺 `eric_lis_v2dot1=1` | 添加后重启 cmf |
| OpenSSL 链接失败 | 版本 < 1.0.0 | 升级到 1.0.2 + ldconfig |
| Connection refused | LIMS IP 错/LIMS 未运行 | 检查配置 |
| session invalid | 用户名错/登录超限 | 改用户名/LIMS 侧重置 |
| neType 错误 | 配成 "GPRS" | 改配 GGSN/SGSN |
| GGSNMonitoring=1 失败 | PS 网元不支持 | 改 **0** |
| Terminate 失败 | target 状态 inprogress | LIMS 未连 MSC 或 MSC 掉线 |
| Delete 失败 | 间隔太短 | Terminate 后 sleep **3 秒** |

## 参考 SOP 文档

完整的 24KB SOP 文件：`references/ericsson-mss17a-x1-x2-x3-sop.md`
- 28 个 COD 命令全表
- MSC 命令行设控完整示例（含 Phase 1-6）
- IRD ASN.1 + RCEFILE1 23 种记录类型参数详解
- X3 IWD 协议文档清单
- 实战 CURL 脚本 + Kafka 消息示例
- 全部故障码速查表
