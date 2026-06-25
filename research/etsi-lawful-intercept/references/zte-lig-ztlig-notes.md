# Sinovatio LIG (ZTLIG) 接口实战笔记

> 来源：`/home/andymao/LI/ZTLIG/ztlig_target字段详细解释.md`
> 知识库入口：`~/knowledge/research/ZTLIG_Target字段详解.md`

## Target 字段格式

ZTLIG 的 Target 记录用于配置监听目标，一般 23 个字段（多 TMC 模式 25 个），CSV 格式：

```
leaID,liid,targetType,targetID,module,incptType,failDeal,speechType,hi2A,hi2Port,
hi2User,hi2Pass,hi2link,hi3A,startDay,startTime,endDay,endTime,virneID,neID,
hw_lioid,nsn_reqId,mcID[,mcliid,imsi]
```

### 字段详解

| # | 字段 | 说明 |
|---|------|------|
| 1 | leaID | LEA 编号（TMC 设控下发） |
| 2 | liid | lawfulInterceptionIdentifier，下发给网元的 LI 标识 |
| 3 | targetType | 跟踪类型（见下表） |
| 4 | targetID | 布控目标 ID |
| 5 | module | 模块（Kafka 下发默认不填） |
| 6 | incptType | 1=IRI, 2=CC, 3=IRI+CC |
| 7 | failDeal | 失败处理策略 |
| 8 | speechType | 0=语音合并, 1=语音分离 |
| 9 | hi2A | HI2 地址 |
| 10 | hi2Port | HI2 端口 |
| 11 | hi2User | HI2 用户名 |
| 12 | hi2Pass | HI2 密码 |
| 13 | hi2Link | HI2 链路类型（主动/被动） |
| 14 | hi3A | HI3（CC）地址 |
| 15-18 | startDay/startTime/endDay/endTime | 布控起止时间 |
| 19 | virneID | 虚拟网元 ID |
| 20 | neID | 物理网元 ID |
| 21 | hw_lioid | 华为特有 LIOID（非华为网元不需要） |
| 22 | nsn_reqId | NSN PS 域请求 ID |
| 23 | mcID | 监听中心编号 |

**多 TMC 模式额外字段：**

| # | 字段 | 说明 |
|---|------|------|
| 24 | mcliid | MC 下发的真实 LIID |
| 25 | imsi | NSN 1IPV1 网元设控 IMEI/MSISDN 时保存的 IMSI |

### Target Type 对照表

| 值 | 含义 | 说明 |
|----|------|------|
| 0 | User Number | 具体的用户号码（电话号码） |
| 1 | Trunk group | 中继群（聚合物理链路） |
| 2 | User Number Prefix | 号码前缀（如国家/地区代码） |
| 3 | IMEI | 国际移动设备标识 |
| 4 | TEI | 隧道端点标识符 |
| 5 | IMSI | 国际移动用户标识 |
| 6 | MSISDN | 移动站国际用户目录号码 |
| 7 | E.164 | 国际电话号码标准格式 |
| 8 | SIP-URL | SIP 会话标识 |
| 9 | Tel-URL | 电话 URL 格式 |
| 10 | IDSN | 综合业务数字网 |

### 多 TMC 模式

通过配置 `ztlig.dbLeaID` 开启：
- `= 0`：不开启（默认）
- `> 0`：开启多 TMC 模式，下发网元的 leaID 为配置值

典型场景：两个站点，每运营商只有一套 PS，需对接两套后端。

## ZTLIG vs 华为 LIG 对比要点

| 维度 | ZTLIG | 华为 LIG |
|------|-------|----------|
| Target 格式 | CSV 文本（23字段） | X1 消息中 ASN.1/二进制结构 |
| 监听类型 | incptType 字段（1/2/3） | LIOID 关联 incptType |
| 华为兼容 | 有 hw_lioid 字段适配 | 原生 LIOID 机制 |
| NSN 兼容 | 有 nsn_reqId 字段适配 | 无 |
| 多TMC | mcliid + imsi 扩展字段 | 多LEA 共享 Target 机制 |

## 数据流示意

```markdown
TMC (MC) → ZTLIG → [HI2/HI3 下发给网元]
                    ↓
                 [NE 拦截] → X2(IRI) / X3(CC) → DF2/DF3 → HI2/HI3 → LEMF
```

## 部署实战：乌干达前后台传输不通场景

### 背景

ZTLIG 部署在运营商机房（前台），后台 OWLS 到运营商机房传输未通。此时需在前台部署 Kafka，否则 ZTLIG 1 进程不启动并报错。

### 拓扑

```
运营商机房              ← 物理不通 →          后台机房
ZTLIG (前台)                              OWLS (后台)
  ↓ 写 KAFKA                               ↑ 读 KAFKA
KAFKA (前台部署)
```

### 必须创建的 Kafka Topic

```bash
bin/kafka-topics.sh --create --zookeeper 192.168.3.168:2181 \
  --replication-factor 1 --partitions 1 --topic TARGET_INFO
bin/kafka-topics.sh --create --zookeeper 192.168.3.168:2181 \
  --replication-factor 1 --partitions 1 --topic TARGET_INFO_STATUS
bin/kafka-topics.sh --create --zookeeper 192.168.3.168:2181 \
  --replication-factor 1 --partitions 1 --topic OWLS_TMC_REALTIME
bin/kafka-topics.sh --create --zookeeper 192.168.3.168:2181 \
  --replication-factor 1 --partitions 1 --topic OWLS_TMC_OFFLINE
```

### 验证

```bash
bin/kafka-topics.sh -list -zookeeper 192.168.3.168:2181
# 输出: OWLS_TMC_OFFLINE, OWLS_TMC_REALTIME, TARGET_INFO, TARGET_INFO_STATUS
```

### Topic 用途

| Topic | 用途 |
|-------|------|
| TARGET_INFO | 拦截目标信息 |
| TARGET_INFO_STATUS | 拦截目标状态 |
| OWLS_TMC_REALTIME | 实时 TMC 数据 |
| OWLS_TMC_OFFLINE | 离线 TMC 数据 |

ZTLIG(Sinovatio) 作为 Mediation Function，将 TMC 下发的 Target 配置转发给各种类型的网元（华为/中兴/NSN），同时处理多 TMC 场景的 LIID 映射。
