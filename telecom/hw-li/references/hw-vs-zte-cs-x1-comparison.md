# Huawei CS X1 vs ZTE CS X1 接口对比

## 结构对比

| 维度 | 华为 CS X1 | 中兴 CS X1 |
|------|-----------|-----------|
| 传输层 | TCP/IP (NE=Server, LIG=Client) | TCP/IP (NE=Server, LIG=Client) |
| 并发 | ≤5 连接 | ≤5 连接 |
| 超时 | 5s 无响应即失败 | 5s 无响应即失败 |
| 加密 | DES 加密可选 (des_key/encrypt_mode) | 无专用加密 |
| 用户名限制 | 无限制 | 有长度/字符限制 |

## NE 配置差异

### 通用 (NE-COM)
- vendor/version/x1_ip/x1_port/user/pwd/trace_type — 两厂商共用

### 厂商特有配置块

**NE-HW (5项)** — 华为:
- `neid` — 网元 ID
- `alias` — 别名
- `need_time` — 时间同步开关
- `des_key` — DES 加密密钥
- `encrypt_mode` — 加密模式

**NE-ZTE (8项)** — 中兴:
- `phneid` — 物理网元 ID
- `module_ip` — 模块 IP
- `batch` — 批处理参数
- `sp_fg` — 分流标志
- `neno_fg` — NE 编号标志
- `operator` — 运营商
- `password` — 密码
- `alias` — 别名

## VNE 配置差异

| 字段 | 华为 | 中兴 |
|------|------|------|
| 共有 | vneid/hi2_neid/speechtype/incptType | vneid/hi2_neid/speechtype/incptType |
| 特有 | (无) | VNE-ZTE: vmscindex/alias/operator/password |

## LIID 映射

| 特性 | 华为 | 中兴 |
|------|------|------|
| LIID 范围 | 1~65535 (1~25字节 ASCII) | 1~65535 |
| 特殊映射 | `hw_lioid` — lioid ↔ liid 映射 | 无映射字段 |
| 目标类型 | ISDN/MSISDN/IMEI/SIP_URL/TEL_URL | IMSI/MSISDN/IMEI/SIP_URL/TEL_URL |

## 设控消息格式

**华为:**
- `X1SetTarget` — 新增设控
- `X1ModifyTarget` — 修改设控
- `X1DeleteTarget` — 删除设控
- `X1Handshake` — 会话保活

**中兴 (命令行):**
- `ADD LITGT/6505: MCID/1=?: LIID/2=?: TT/3=?: TI/4=?: [MODULE/5=?:] IT/6=?: FD/7=?: [SPEECHTYPE/8=?:] [HI2A/9=?:] [HI2PORT/10=?:] [HI2U/11=?:] [HI2P/12=?:] [HI2LINK/13=?:] [HI3A/14=?:] [SD/15=?:] [ST/16=?:] [ED/17=?:] [ET/18=?:] [NEID/19=?:]`

## 多 TMC 支持

| 华为 | 中兴 |
|------|------|
| 通过 ztlig.dbLeaID 控制 (syn_night bit0=hw) | 通过不同端口实现 (不同 LEA 不同 port) |

## 告警代码 (共用)

| alarm-id | 等级 | 含义 |
|----------|------|------|
| 504 | 2 (Major) | X1 认证失败 (用户名/密码/Net ID) |
| 512 | 1 (Warning) | X1 通道通信中断 |

## LICENSE 项

| 华为 | 中兴 |
|------|------|
| `hw_ne` | `zte_lis_v3_v4` |

## 排障要点 (共用)

当 X1 认证失败时，过滤 2 口对接端口，NE 会向该端口吐报错信息。
