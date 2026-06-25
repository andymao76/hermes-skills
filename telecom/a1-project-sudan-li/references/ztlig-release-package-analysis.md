# ZTLIG 发行包分析（LISTENER V1.1.02_LIG_T11）

> 包名: `ZTLIG_Bin_X86Centos_20251212_4a5960_a27cfd.tar.gz` (316MB→628MB)
> 构建日期: 2025-12-12 | 目标: CentOS x86-64, Linux 2.6.32+
> 路径: `~/projects/A1/202606/ZTLIG/`（已解压）

## 进程架构（8 个二进制）

| 可执行文件 | 大小 | 角色 |
|-----------|------|------|
| **ztlig1** | 146KB | X1 设控引擎 — 对接所有厂商 NE 的 X1 设控协议，维护目标库 |
| **ztlig2** | 360KB | X2 拦截数据引擎 — 接收/解码/转换/输出 IRI 数据（核心进程） |
| **ztlig3** | 126KB | X3 内部协议引擎 — DPDK 高速收包，HI3 会话管理 |
| **cmf** | 88KB | 配置管理框架 |
| **psm** | 71KB | 抓包管理 (pcap) |
| **psm_ass** | 192KB | 抓包辅助进程 |
| **rvf** | 317KB | 语音文件管理 — RTP 接收/语音落地 |
| **ssf** | 221KB | 会话管理 — SIP-I/TS 102232-5/CC |

## 核心进程分析

### ztlig2 — X2 处理引擎

```
main()
 ├── LigReadAllConfig()      — 读取 ztlig.cfg
 ├── HI2_Init()              — HI2 子系统初始化
 ├── create_threadpool()     — 线程池
 ├── 常驻线程:
 │   ├── LIG1liveTh          — ZTLIG-1 保活心跳
 │   ├── lig2_live_check     — 自身存活检查
 │   ├── ThreadCheckTh       — 通用检查
 │   └── ThreadCheckSsfAliveTh — SSF 存活
 └── 厂商 X2 接收线程:
     ├── StartX2TcpProc()    — TCP 协议监听/接收/抓包
     ├── StartX2UdpProc()    — UDP 接收
     ├── StartX2FtpProc()    — FTP 文件接收
     └── StartX2SftpProc()   — SFTP 文件接收
```

**X2 数据流**: 网元(MSC/GGSN/EPC) → TCP/UDP/FTP/SFTP 接收 → 厂商解码器(.so) → 消息适配(X2_MessageAdaptTh) → 事件转换(Trans_UmtsEvent) → HI2 格式化(FillHI2_MsgProc) → LEA 队列 → Kafka/文件输出

### ztlig3 — X3 处理引擎

- 通过 DPDK 高速收包 (libdpdkfwd.so)
- HI3 会话超时管理 (Hi3SessionTimeoutTh)
- SICMS 对接 (acSicmsSendMac/acSicmsRecvMac)
- Lig3TransHi2Msg: X3 数据转发给 ztlig2

## 厂商协议插件（127 个 .so + 3 个 .a）

**X1 设控 (10+ 插件):** Ericsson(3版本) / 华为 / 中兴(2版本) / Utimaco / Zeel / Group2K / UAG / ETSI

**X2 数据输出 (16 插件):** Ericsson / 中兴(4版本) / 华为(6厂商:MSC/GSN/EPC/NGN/PDSN/5GC) / Nokia/NSN(2) / ALU / Mavenir / VoLTE

**X3 内部协议 (9 插件):** 中兴(3版本) / 华为(2) / NSN / ETSI / E33108

## ztlig.cfg 配置结构

| 段落 | 说明 |
|------|------|
| `[GLOBAL]` | FTP 认证、Kafka 监控、多 TMC |
| `[ZTLIG1_300]` | ztlig1 进程 (IP/端口/X1/DB/夜间同步) |
| `[ZTLIG2_460]` | ztlig2 进程 (IP/端口/X2/LEA/会话超时) |
| `[ZTLIG3_480]` | ztlig3 进程 (IP/端口/X3/DPDK/SICMS) |
| `[NE_66X]` | 物理网元 (IP/端口/厂商/版本/认证) |
| `[VNE_76X]` | 虚拟网元 (类型/operid/hi2_neid/speechtype) |
| `[LEA_800]` | 执法机构 (Redis/Kafka/SFTP/SICMS MAC) |
| `[SSF_1300]` | 会话管理 (SIP-I/超时) |
| `[RVF_1400]` | 语音落地 (RTP端口/编解码) |

## 二进制分析技巧

```bash
# 查看 ELF 基本信息
file ztlig2                         # 架构/链接/调试符号
size ztlig2                          # text/data/bss 段大小
readelf -S ztlig2                    # 节头表

# 符号分析
nm -C ztlig2 | grep ' T '           # 所有文本段符号（函数）
nm -C ztlig2 | grep ' D \| B '     # 数据段符号（全局变量）
nm -C ztlig2 | grep ' U '          # 未定义符号（外部依赖）

# 字符串提取
strings ztlig2 | grep -iE 'MSG_|thread|config|error|succ'  # 消息枚举/线程/配置

# 依赖分析
ldd ztlig2                           # 运行时动态库依赖
```
