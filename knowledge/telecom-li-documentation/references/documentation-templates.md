# Documentation Templates for LI Knowledge Notes

## Template A: Protocol/Principle Note

```markdown
---
title: {Vendor}_{Technology}_{Topic}
tags: [{vendor}, {interface}, LI, 合法监听, {mode}]
---

# {Vendor} {Technology} {Topic}

## 参考标准
- **{ETSISpec}** — {description}

## 一、{First Section}
...

## 二、{Interface} 信令面

### 上报机制
...

### 参数结构
| 字段 | 说明 |
|------|------|
| ... | ... |

## 三、{Interface} 媒体面

### 各网元输出方式
| 网元 | 模式 | 原因 |
|------|------|------|
| ... | ... | ... |
```

## Template B: Packet Decode Reference

```markdown
---
title: {Vendor}_{Interface}_抓包示例
tags: [{vendor}, {interface}, IRI, 抓包, {mode}, LI]
---

# {Vendor} {Interface} 抓包示例

## 概述

### 呼叫基本信息
| 字段 | 值 |
|------|-----|
| LIID |  |
| CallID |  |
| ICID |  |
| ... |  |

### 信令流程（时间轴）
| # | 时间 | 消息 | 方向 | 关键参数 |
|---|------|------|------|---------|
| 1 |  | INVITE | 上行 | ... |
| 2 |  | 183 | 下行 | ... |

### 观察总结
1. ...
```

## Template C: Operations Manual

```markdown
---
title: {System}运维手册
tags: [{system}, LI, 运维, 排障, 配置]
---

# {System} 运维手册

## 一、系统架构

### 进程说明
| 进程 | 接口 | 功能 |
|------|------|------|
| ... | ... | ... |

### 数据流
```
...
```

## 二、{Process1} — {Function}

### 配置
```ini
...
```

## 三、版本升级

### 步骤
1. ...
```

## Template E: Vendor Config Reference (ztlig.cfg style)

```markdown
### {Config Block} 部分

{Block}(x) 配置块定义 {功能描述}，x 为编号。

| 配置项名称 | 类型 | 默认值 | 含义 | 取值范围 | 需重启进程 | 属性 |
|-----------|------|--------|------|---------|-----------|------|
| ... | ... | ... | ... | ... | ... | ... |
| ... | ... | ... | ... | ... | ... | ... |

#### 注意事项
- 特定条件1：需要注意事项
- 特定条件2：需要注意事项
```

#### Vendor-Specific Sub-section Pattern

```markdown
#### NE-{VENDOR} 部分（{厂商名}网元特有配置）

| 配置项名称 | 类型 | 默认值 | 含义 | 取值范围 | 需重启进程 | 属性 |
|-----------|------|--------|------|---------|-----------|------|
| ... | ... | ... | ... | ... | ... | ... |
```

## Template F: SOAP Interface (Ericsson LI-IMS style)

```markdown
## SOAP 操作接口一览

| 操作 | 说明 | 关键参数 |
|------|------|---------|
| `login` | 登录认证 | userName, password → sessionID |
| `createWarrant` | 创建监听令牌 | warrantID=-1, targetNumber, neType |

### createWarrant 结构
```
requestHeader (type + userID + sessionID)
  + warrantItem (...)
  + dtlWarrantNeTypeItemArray[]
```

### 关键字段
- `warrantID`: -1 创建, 返回实际值
- `supplementaryInfo`: bitmask (1=LIPA, 2=EventTriggered, 4=Simple, ...)
```

```markdown
---
title: {Vendor}_CS_X接口说明与{System}部署实战
tags: [{vendor}, {interface}, {mode}, LI, {system}]
---

# {Vendor} CS X 接口说明与 {System} 部署实战

## 一、X1 接口
### 基本特征 (TCP/IP, C/S, 并发, 超时)
### 对接日志
### 抓包命令
### LIID / X1SetTarget参数
### 设控号码格式

## 二、X2 接口 (信令面)
### BER编码规则 (TLV, 定长, 厂商头)
### 号码编码 (0x91, TBCD-STRING)
### 位置信息编码 (CGI/LAI/SAI/RAI/TAI/ECGI)
### CDR字段定义 + EventDetail
### 补充业务码表
### 排查命令 (Wireshark/tail/tcpdump)
### 呼叫流程示例

## 三、X3 接口 (媒体面)
### 信令传输 (TMD→ISUP, IP→M3UA)
### X2/X3关联 (LIID+CIN, SIP-I)
### SSF+RVF日志分析

## 四、系统软件架构
### 进程说明 + 数据流

## 五、部署实战
```
