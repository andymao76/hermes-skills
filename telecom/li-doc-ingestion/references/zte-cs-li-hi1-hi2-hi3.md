# ZTE CS LI 三接口 — 快捷参考

## HI1 CLI 命令结构

格式: `CMD: PARAM1=VAL: PARAM2=VAL:`
反馈: `CMD=XXXX;RESULT=0:Succeed.;[RECORDCOUNT=N;]`

## 核心 HI1 命令

| 命令 | 代码 | 参数(M) | 参数(O) |
|------|------|---------|---------|
| ADD LITGT | 6505 | MCID,LIID,TT,TI,IT,FD | SPEECHTYPE,TRCT,HI3A,HI3PORT,SD,ST,ED,ET,HI3M,NENo,PRIORITY |
| DEL LITGT | 6506 | MCID | LIID,TT,TI,NENo |
| MOD LITGT | 6507 | MCID | LIID,TT,TI,IT,FD,SPEECHTYPE,...,NENo |
| SHW LITGT | 6508 | — | MCID,LIID,TT,TI,...,NENo |
| SHW TGTINF | 6510 | TT,TI | NENo |
| SET BARRING | 6529 | MCID,BARRING | LIID,TT,TI,NENo |
| ADD OP | 6516 | OP,PWD,CFM | CG,MCID,NENo |

## 用户三级

| 级别 | 代码 | 权限 |
|------|------|------|
| NE 超级 | 260 | 管理 IP、创建 261/262 |
| LEA 管理 | 261 | 配置通信参数、创建 262 |
| LEA 操作 | 262 | 目标增删改查 |

## HI2 ASN.1 记录类型

| 类型 | Tag | 用途 |
|------|-----|------|
| iRI-Begin-record | A1 | 呼叫建立 |
| iRI-End-record | A2 | 呼叫释放 |
| iRI-Continue-record | A3 | 中间事件 |
| iRI-Report-record | A4 | 非呼叫事件 |
| iRI-Alarm-record | B0 | 网元告警 |

## 事件类型（umts-Cs-Event tag 9F21）

1=呼叫建立, 2=应答, 3=补充业务, 4=切换, 5=释放,
6=短信, 7=位置更新, 8=SCI(DTMF), 9=关机, 10=HI3链路, 11=开机

## HI3 — ISUP/PRI/BICC/SIP-I

- 主叫号码: NEID
- 被叫号码: HI3 Address
- 被叫子地址: {OperatorID, CIN, CCLID}
- 主叫子地址: {LIID, Direction, ServiceOctets}
