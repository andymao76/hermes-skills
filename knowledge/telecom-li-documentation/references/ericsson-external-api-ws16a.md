# Ericsson LI IMS External API WebServices (WS 16A)

**来源**: CXC1373777_16_R6A.0 / R8A 文档包中的 External_API_WebServices 目录
**协议**: SOAP 1.1 (document/literal) over HTTP
**默认端点**: `http://localhost:9090/{ServiceName}Port`

## 架构概览

外部系统通过 SOAP API 与 Ericsson LI IMS 系统交互。需先通过 SessionService 登录获取 sessionID，后续所有操作携带该 sessionID。

```
┌─────────────┐     SOAP/HTTP      ┌──────────────────┐
│  外部系统    │ ◄──────────────►  │ Ericsson LI IMS  │
│ (LEA/LEMF)  │                   │ (EPA Server)      │
└─────────────┘                   └──────────────────┘
```

## 服务清单（共 22 个服务）

### 核心 LI 管理服务

| 服务 | WSDL | 操作 | 说明 |
|------|------|------|------|
| **SessionService** | `sessionservice.wsdl` | `login`, `logout` | 登录认证，返回 sessionID |
| **WarrantService** | `warrantservice.wsdl` | 13 种操作 | 搜查令 CRUD 管理 |
| **NeService** | `neservice.wsdl` | 10 种操作 | NE 配置与管理 |
| **LeaService** | `leaservice.wsdl` | `getLeaList` | LEA 列表查询 |
| **LemfService** | `lemfservice.wsdl` | `getLemfList` | LEMF 列表查询 |

### 辅助管理服务

| 服务 | 说明 |
|------|------|
| **AclService** | ACL 权限控制 |
| **TargetAliasService** | 目标别名管理 |
| **PayloadFilterService** | 载荷过滤规则 |
| **AuditWarrantService** | 搜查令审计 |
| **IntGroupService** | 拦截组管理 |
| **NeGroupService** | NE 组管理 |
| **CountersService** | 系统计数器 |
| **FeatureCacheService** | 特性缓存 |
| **IriccService** | IRICC 管理 |
| **McService** / **McnbService** | MC/MCNB 管理 |
| **SuppNeService** | 补充 NE 管理 |
| **WarrantDtlService** | 搜查令详情 |
| **WarrantMcService** / **WarrantMcnbService** | 搜查令-MC 关联 |
| **AliasService** | 别名管理 |
| **UtilityService** | 实用工具 |
| **ImsMonitorService** | IMS 健康监控 |

## WarrantService 操作详解（13 种）

### 搜查令 CRUD

| 操作 | SOAP Action | 请求体 | 说明 |
|------|-------------|--------|------|
| `createWarrant` | `urn:CreateWarrant` | `warrantCreateRequest` | 创建搜查令 |
| `modifyWarrant` | `urn:ModifyWarrant` | `warrantModifyRequest` | 修改搜查令 |
| `deleteWarrant` | `urn:DeleteWarrant` | `warrantDeleteRequest` | 删除搜查令 |
| `getWarrantList` | `urn:GetWarrantList` | `warrantQuery` | 查询搜查令列表 |

### 动态搜查令

| 操作 | 说明 |
|------|------|
| `activateDynamicWarrant` | 激活动态搜查令 |
| `terminateDynamicWarrant` | 终止动态搜查令 |
| `deleteDynamicWarrant` | 删除动态搜查令 |
| `getDynamicWarrantList` | 查询动态搜查令 |

### 查询/操作

| 操作 | 说明 |
|------|------|
| `getWarrantPosition` | 获取目标位置 |
| `activateListAllPhoneOnDemand` | 按需激活全号定位 |
| `getLinkedWarrantList` | 关联搜查令列表 |
| `getDtlWarrantNeTypeList` | 按 NE 类型查详情 |
| `getWarrantNasCtxList` | NAS 上下文列表 |
| `retrieveWarrantOVStatus` | 查询 OV 状态 |

## WarrantItem 核心字段

| 字段 | 类型 | 说明 |
|------|------|------|
| warrantID | int | 搜查令 ID（新建填 -1） |
| targetNumber | string | 目标号码 |
| targetTypeID | string | 目标类型 ID |
| neName | string | NE 名称 |
| neGroupName | string | NE 组名 |
| lea | string | 执法机构 |
| interceptGroupID | string | 拦截组 ID |
| MUID | string | MUID |
| useOneLemf | short | |
| lemf | string | LEMF 地址 |
| isTargetPABX | boolean | 是否 PABX |
| PABXName | string | PABX 名称 |
| legalBasis | string | 法律依据 |
| acc | string | ACC |
| subnetOperatorID | string | 子网运营商 ID |
| netOperatorID | string | 网络运营商 ID |
| caseID | string | 案件 ID |
| isTargetNumberSuppressed | boolean | 号码是否隐藏 |
| activationTime | long | 激活时间戳 (ms) |
| terminationTime | long | 终止时间戳 (ms) |
| state | string | 状态 |
| status | string | 子状态 |
| closeUserGroup | string | 闭合用户组 |
| userID | string | 操作用户 |
| dtID | string | 交付目标 ID |
| sfID | string | 会话功能 ID |
| networkIdentifier | string | 网络标识 |
| maxCall | string | 最大呼叫数 |
| verifyMcnb | string | MCNB 验证 |
| cType | string | 内容类型 |
| connectionID | string | 连接 ID |
| supplementaryInfo | short | **补充信息位掩码** |
| GGSNMonitoring | boolean | GGSN 监控启用 |
| positioningPeriod | int | 定位周期 (5/15/30/45/60/-1) |
| contextId | string | 上下文 ID |
| direction | string | 方向 |
| radiusWarrantId | int | RADIUS 关联搜查令 ID |

### supplementaryInfo 位掩码定义

| Bit | 值 | 含义 |
|-----|-----|------|
| 0 | 1 | IRI only (信令拦截) |
| 1 | 2 | CC (通信内容拦截) |
| 2 | 4 | Location (位置信息) |
| 3 | 8 | Reserved |
| ... | ... | 按 NE 类型不同定义不同 |

### positioningPeriod 枚举

| 值 | 含义 |
|----|------|
| 5 | 5 秒 |
| 15 | 15 秒 |
| 30 | 30 秒 |
| 45 | 45 秒 |
| 60 | 60 秒 |
| -1 | 关闭定位 |

## dtlWarrantNeTypeItem 字段

| 字段 | 说明 |
|------|------|
| warrantID | 搜查令 ID |
| neType | NE 类型 (如 "SBC", "MSS", "MGW", "HSS", "CSCF") |
| HI2Lemf | HI2 交付的 LEMF |
| isDataMonitoringOnly | 数据监控模式 (0~96 等多枚举值) |
| aclId | ACL 规则 ID |
| ovTargetType | OV 目标类型 |
| mcnbs | MCNB ID 数组 |
| mcs | MC + SuppNE 关联数组 |
| nasCtxsAvailable | 可用 NAS 上下文 |
| nasCtxsSelected | 选定 NAS 上下文 |
| broadcastArea | 广播区域 |
| featureInfo | 特性信息 |
| targetInfo | short |
| ovUserId | OV 用户 ID |

## NeService 操作（10 种）

| 操作 | 查询内容 |
|------|----------|
| `getNeList` | NE 列表（含 neID, neType, address, port, vendor, x2Username/x2Password 等） |
| `getNeListByNeType` | 按类型查 NE |
| `getNeOptionList` | NE 选项（fieldName/value/isOptionOn/isMandatory） |
| `getNeProfileList` | NE 配置集（含 x3IpAddress/x3PortNumber） |
| `getOvNeInfoList` | OV NE 信息 |
| `getOvNeDtlInfoList` | OV NE 详细信息（单 NE） |
| `getLnkInfoList` | 链路附加 NE 信息（SNMPv3 配置: UserName/AuthKey/PrivKey） |
| `getLnkRRList` | RADIUS 路由器关联 |
| `getLnkRSList` | RADIUS 服务器关联 |
| `getIpProbeFilterList` | IP 探针过滤器 |

## ImsMonitorService

| 操作 | 返回 |
|------|------|
| `getImsSWData` | 各子系统健康状态（subsystemName, status, vsz, cpu, memory） |
| `getImsHWData` | 硬件设备数据 |

## 公共数据结构

### requestHeader
```
{ type:     requestType(int)  // CHECKED_CREATE|CREATE|DELETE|LIST|MODIFY|VIEW|WARRANT_AUDIT
  userID:   string            // 登录用户
  sessionID: string           // 登录会话 ID }
```

### responseHeader
```
{ code:     responseCode(int) // 见下
  reason:   string            // 原因描述
  objectId: int }             // 操作对象 ID
```

## 响应码（ResponseConstants）

| 值 | 常量名 | 含义 |
|----|--------|------|
| 0 | BUSINESS_RULE_VIOLATION | 业务规则冲突/待审批 |
| 1 | INTERNAL_ERROR | 内部错误 |
| 2 | INVALID_SESSION | 会话无效/未登录 |
| 3 | SUCCESS | 成功 |
| 4 | WARNING | 警告 |
| 5 | LOGOUT_SESSION | 会话已注销 |
| 6 | ORDERED | 已提交待处理 |

## 请求类型（RequestConstants）

| 值 | 含义 |
|----|------|
| 0 | CHECKED_CREATE（检查后创建） |
| 1 | CREATE |
| 2 | DELETE |
| 3 | LIST |
| 4 | MODIFY |
| 5 | VIEW |
| 6 | WARRANT_AUDIT |

## 认证流程

```
1. login(userID, password) → sessionID
2. createWarrant(requestHeader{type=CREATE, sessionID=xxx}, ...)
3. logout(sessionID)
```

所有服务端口均在 `http://localhost:9090/` 上监听，通过 URL 路径区分：
- `http://localhost:9090/SessionServicePort`
- `http://localhost:9090/WarrantServicePort`
- `http://localhost:9090/NeServicePort`
- `http://localhost:9090/LeaServicePort`
- ...

## 版本说明

包内包含 8 个子版本（1, 1.8, 2.1, 2.4, 12A, 13A, 14B, 16A），16A 为最新最完整版。各版本主要在 XSD 文件组织方式上存在差异（早期版本 schema 内嵌，后期版本独立出 list_schema/request_schema/response_schema/exception_schema）。

## 相关文件

- 原始 WSDL/XSD 源码路径: `External_API_WS_16A/` (tar 包解压后)
- 常量定义: `External_API_WS_16A/constants/*.properties`
- 知识库: `~/knowledge/telecom/lawful_interception/wsdl-xsd-basics.md` (Ericsson SOAP/WSDL 基础)
