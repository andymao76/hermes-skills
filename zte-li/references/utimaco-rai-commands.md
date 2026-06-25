# Utimaco LIMS RAI 命令速查

## 连接
- TCP 端口 52134
- 二进制 PDU 协议（非 Telnet/SSH）
- 固定 126 字节 LOGIN PDU

## ICD 管理
| 命令 | 用途 | 关键参数 |
|------|------|---------|
| icdlist | 列出 ICD | icd=, status= (NPAIC), all |
| icdadd | 创建 ICD | lea=M, fileref=M, doo=M, start=M, stop=M, class=M |
| icdact | 激活 N→P | icd=M |
| icdreact | 重激活 I→P | icd=M, doo=M |
| icddel | 删除 ICD | icd=M (仅N或C) |
| icdmod | 修改 ICD | icd=M, doo=M, stop=NOW |
| icdreport | 生成报告 | icd=M, [final] |
| icdlog | ICD日志 | icd=, from=, to= |

## Target 管理
| 命令 | 用途 | 语法 |
|------|------|------|
| tlist | 查询目标 | `tlist [icd=] [tno=]` — 支持*通配符 |
| tadd | 添加目标 | `tadd icd=M tno=M ttype=M liid=O net=M dtype=M mc_xxx= doo=M` → `tno_created tno_id=N` |
| tdel | 删除目标 | `tdel tno_id=M doo=M` — 无输出 |
| tmod | 修改目标 | `tmod tno_id=M [params...] doo=M` — 不传则保留，传入则替换 |
| tstate | 位置请求 | `tstate icd=M tno=M doo=M` — LBS 专用 |
| tnelist | 网元目标 | `tnelist neid=M` — 仅部分 Nokia+Huawei NE 支持 |

## MC 管理
| 命令 | 用途 | 输出 |
|------|------|------|
| mclist | 列出 MC | `mc mc=ID mcname=... mctype=... lea=...` (38字段) |
| mcadd | 创建 MC | `mc_created mc=ID` |
| mcdel | 删除 MC | 无输出 (被引用时630) |
| mcmod | 修改 MC | 无输出 |

## 常用状态码
| 码 | 含义 | 码 | 含义 |
|----|------|----|------|
| 0 | 成功 | 201 | 目标不存在 |
| 100 | Unknown command | 202 | ICD不存在 |
| 101 | 语法错误 | 250/251 | 订单日期错误 |
| 110 | 数据库错误 | 262 | LEA未知 |
| 111 | 内部错误 | 290/291 | 目标号码错误 |
| 115 | 功能未启用 | 501 | ICD状态不允许 |
| 120 | 无权限 | 630 | MC被引用无法删除 |
| 130-136 | 登录相关错误 | 700-749 | 网元通信错误 |
| 132 | 密码过期 | 900 | 网元已存在 |

## SPEECHTYPE (中兴 HI1 / ZTLIG)
| 值 | 模式 | 通道 |
|----|------|------|
| 0 | Single Combined (Combined A) | 1 混合 |
| 1 | Multi-leg Separate (Option A) | 每路 2 通道 |
| 2 | Single Separate (Option B) | 2 通道 |
| 3 | Multi-party Separate | N 上行 |
| 4 | Multi-conversation Separate (SORM) | 每路 2 通道 |
| 5 | Multi-conversation Combined (Combined B) | 1 混合 |
