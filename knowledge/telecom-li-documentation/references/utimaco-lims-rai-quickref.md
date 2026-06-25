# Utimaco LIMS RAI v16.1 速查

> 德国 Utimaco TS GmbH 出品 — LIMS (Lawful Interception Management System)
> RAI = Remote Administration Interface，基于 TCP/IP 二进制协议
> 默认端口: 52134

## RAI-SP 会话协议 (7 种 PDU)

| PDU | 值 | 方向 | 说明 |
|-----|-----|------|------|
| LOGIN | 1 | 远程→LIMS | 固定 126 字节 |
| REJECT | 2 | LIMS→远程 | 拒绝+原因码 |
| ACCEPT | 3 | LIMS→远程 | 仅 8 字节 |
| COMMAND | 4 | 远程→LIMS | NUL 结尾 ASCII 命令 |
| REPLY | 5 | LIMS→远程 | CES(4)+CEI(101)+output |
| LOGOUT | 6 | 远程→LIMS | 仅 8 字节 |
| ABORT | 7 | LIMS→远程 | 异常中断 |

### LOGIN PDU 结构 (126 字节)

| Offset | 大小 | 字段 |
|--------|------|------|
| 0 | 4 | 类型=1 |
| 8 | 21 | user id (NUL 终止, 最大 20 字符) |
| 29 | 16 | password (NUL 终止, 最大 15 字符) |
| 45 | 16 | new password (可选改密) |
| 61 | 4 | RAI version (3=3.1, x=x.0) |
| 65 | 1 | UTC-Flag |
| 66 | 4 | SubVersion (0=x.0, 1=x.1) |

### REJECT 原因码

| 值 | 含义 | 后续行为 |
|----|------|---------|
| 1 | 无效用户/密码 | ABORT |
| 2 | 用户锁定 | ABORT |
| 3 | 资源不足(并发超限) | ABORT |
| 4 | **密码过期** | **可重发 LOGIN+新密码** |
| 6 | 新密码不合规 | 继续登录阶段 |

### REPLY PDU 结构

| Offset | 大小 | 字段 |
|--------|------|------|
| 0 | 4 | 类型=5 |
| 8 | 4 | CES (0=成功) |
| 12 | 101 | CEI (NUL 终止文本, 最大 100 字符) |
| 113 | 可变 | Command output (NUL 终止) |

## RAI-CL 命令语言

### 核心数据模型

```
LEA ──1:m── ICD ──1:m── Target ──1:m── MC
```
ICD 生命周期: N(新建)→icdact→P(待启动)→A(活跃)→I(非活跃)→icdreport final→C(关闭)

### 命令速查

| 分类 | 命令 | 功能 |
|------|------|------|
| ICD | icdlist [icd=X] [status=NP] | 查询 ICD（支持*通配符） |
| | icdadd lea=X fileref=X start=YYYYMMDDhhmm stop=... class=0..4 | 创建 ICD |
| | icdact icd=X | 激活 (N→P) |
| | icdreact icd=X start=... stop=... | 重新激活 (I→P) |
| | icddel icd=X | 删除（仅 N 或 C 可删）|
| | icdmod icd=X stop=NOW | 修改（stop=NOW 立即停止）|
| | icdreport icd=X [final] | 生成报告 |
| | icdlog from=YYYYMMDD to=YYYYMMDD icd=X | 操作日志 |
| **Target** | tlist [icd=X] [tno=X*] | 查询目标 |
| | tadd icd=X tno=X ttype=X liid=X net=X dtype=X mc_voice=X mc_iri=X doo=X | **添加目标** |
| | tdel tno_id=X doo=YYYYMMDD | 删除目标（用 tno_id，由 tadd 返回）|
| | tmod tno_id=X [liid=""] [net=X] [dtype=X] [mc_voice=X] [mc_iri=X] [mc_data=X] [mc_data=none] [dir=IN/OUT/BOTH] [ton=INT/NAT] [mcflags=X] [targetflags=X] [area=X] doo=YYYYMMDD | 修改目标参数；`liid=""` 清空 LIID；`mc_data=none` 关闭数据 MC |
| | tstate icd=UemRefno tno=TargetNo doo=DateOfOrder | 启动 LBS 位置请求（GMLC）|
| | tnelist neid=NeIdList | 查询指定网元上的拦截目标（Nokia/Huawei NE 支持）|
| MC | mclist [mc=MCId] [lea=LeaId] | 显示监控中心信息（38 个输出字段）|
| | mcadd lea=X mctype=X ... | 创建监控中心（返回 mc_created mc=MCId）|
| | mcdel / mcmod | 删除/修改监控中心 |
| NE | nelist / neadd / nedel / nemod / necheck / nepurge | 网元管理 |
| User | userlist / useradd / userdel / usermod | 用户管理 |
| LEA | lealist / leaadd / leadel / leamod | LEA管理 |
| Log | backuplog / functionlog / loginlog | 审计日志 |
| Other | alarmlist / nodeactionlist / arealist | 告警/事务/区域 |

### tadd / tmod 关键参数

| 参数 | 说明 (tmod 语义: 不传入则保留原值) | 示例 |
|------|------|------|
| icd | ICD 编号 | 00302 |
| tno | 目标号码 | 0031223 |
| ttype | 目标类型 | MSISDN/IMSI/IMEI/SIPURI/IP_ADDR/PSTN... |
| liid | LI 标识；`tmod` 中 `liid=""` 可清空 | 223 |
| net | 网络 (逗号分隔) | GSM,GPRS,LTE,IMS,5G |
| dtype | 数据类型 (逗号分隔) | VOICE,IRI,DATA,IRI_5G,DATA_5G |
| mc_voice | Voice MC ID | 2 |
| mc_iri | IRI MC ID | 27 |
| mc_data | Data MC ID | 65 |
| mc_vm | 语音信箱 MC | — |
| mc_mm | 多媒体 MC | — |
| mc_email | 邮件 MC | — |
| mc_ia | 互联网接入 MC | — |
| mc_online | 在线语音 MC | — |
| mc_offline | 离线语音 MC | — |
| mc_iri_po | GPRS IRI MC (不传则由 IRI-MC 处理) | — |
| mc_iri_mm | 多媒体 IRI MC (条件) | — |
| mc_iri_5g | 5G IRI MC (条件) | — |
| mc_data_5g | 5G 数据 MC (条件) | — |
| area | 区域拦截 ID 列表 | 1,4 |
| mcflags | 监控标志 Integer (4.1.5) | 391 |
| targetflags | 目标标志 Integer (4.1.5) | 0 |
| ton | 号码类型 (PSTN) | INT/NAT |
| dir | 方向 (PSTN) | IN/OUT/BOTH |
| ngn_neid | NGN 网元标识 | — |
| doo | 订单日期 | YYYYMMDD |

### tdel / tmod / tstate 状态码共用

| 码 | 含义 | 适用命令 |
|----|------|---------|
| 0 | 成功 | 全部 |
| 201 | 目标不存在 | tdel/tmod/tstate |
| 202 | ICD 不存在 | tdel/tmod/tstate |
| 250/251 | 数据/参数错误 | tdel/tmod/tstate |
| 290/291 | LIID 冲突 | tdel/tmod/tstate |
| 501 | ICD 状态不允许删除/修改 | tdel/tmod/tstate |
| 262 | 无权限 | tdel/tmod/tstate |

### Target 类型总表 (86 种)

| 类型 | 编号 | 格式说明 |
|------|------|---------|
| MSISDN | 0 | 15 位数字 |
| IMSI | 1 | 15 位数字 |
| IMEI | 2 | 14 位数字 |
| SIPURI | 27 | 255 字符 |
| TELURL | 26 | 255 字符 |
| IP_ADDR | 28 | IPv4 地址 |
| IPv6_ADDR | 9 | IPv6 地址 |
| EMAIL | 4 | email 地址 |
| LAI | 19 | access_type=access_info |
| LBI | 61 | MCC_MNC[_LAC[_CI]] |
| LBI_ECGI | 86 | MCC_MNC[_ECI] |
| FLEX_IP | 50 | IPFrom-IPTo |
| APP_SIG | 51 | protocol//IPFrom-IPTo |
| PSTN | 29 | 17/32 位 |
| LOCN | 44 | 18 位位置号码 |
| TRUNKN | 48 | 255 中继名称 |

### Network 类型 (Bitmap 值)

| 网络 | 值 | 说明 |
|------|-----|------|
| GSM | 1 | 传统 GSM |
| GPRS | 8 | 分组数据 |
| LTE | 1,048,576 | EPS |
| IMS | 16,777,216 | IMS |
| 5G | 268,435,456 | 5G |
| NGN | 32,768 | 下一代网络 |
| IOT | 134,217,728 | 物联网 |
| LBS | 2 | 位置服务 |
| VOIP | 2,048 | VoIP |

### MC 类型与数据类型兼容

| MC 类型 | 适用数据类型 |
|---------|------------|
| FTAM/X.25 | IRI |
| FTAM/IP | IRI |
| ISDN | Voice (CS 语音) |
| FTP | IRI/Data/MM/Email/IA (最通用) |
| TCP | IRI/Data/MM (常用) |
| UDP | IRI_5G/Data/Data_5G |
| SIP | Voice (VoIP 语音) |
- URI | 网元直接交付 |

### 4.14 完整状态码（部分）

完整 4.14 状态码表（0~1002）见知识库笔记 `~/knowledge/hi2/厂商对接/Utimaco_LIMS_RAI_v16.1_协议规范.md` 第 7.10 节。

常用码：
| 码范围 | 含义 |
|--------|------|
| 0 | 成功 |
| 100-136 | 命令/登录/认证错误 |
| 201-293 | ICD/Target/LEA 参数错误 |
| 305-353 | MC/Target 类型/DT参数错误 |
| 360-499 | MC 类型参数错误 |
| 501 | ICD 状态错误 |
| 600-610 | 数据库/内部错误 |
| 700-749 | 网元通信错误 |
| 800 | 查询错误 |
| 900 | 网元已存在/不存在 |
| 997-1002 | 配置/数据库/参数错误 |

### Flags 体系 (关键控制位)

**mcflags**:
- 0x0040 — 无条件呼叫前转
- 0x0080 — GSM 分离 CC 通道
- 0x0400 — GPRS 分离 CC 通道
- 0x1000 — GPRS Failrelease
- 0x8000 — GSM Tracemode

**targetflags**:
- 0x00010 — 抑制 MSISDN (IRI 中删除)
- 0x00020 — 抑制 IMSI
- 0x00040 — 抑制 IMEI
- 0x00080 — 抑制 GSM SMS 内容
- 0x10000000 — IMS Failrelease
- 0x80000000 — IMS Tracemode

**targetflags2**:
- 0x00001 — IMS 呼叫前转
- 0x00008 — 抑制 LTE SMS 内容
- 0x00020 — 仅 SGW 拦截
- 0x00040 — 仅 PGW 拦截
- 0x01000 — LTE 分离 CC 通道
- 0x02000 — LTE Tracemode
