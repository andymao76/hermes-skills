# ZTLIG 二进制程序结构分析指南

> 分析目标：ZTLIG 程序目录，识别二进制角色、协议插件、架构映射
> 分析方法：`file` → `ldd` → `strings` → 按厂商/接口分类

## 一、目录结构

```
ZTLIG/
├── ztlig2          ← X2 处理主程序 (360KB, ELF64, not stripped)
├── ztlig3          ← X3 处理主程序 (126KB, ELF64, not stripped)
├── libwebhi1.so    ← X1 (HI1) Web/SOAP 接口库 (236KB)
├── lib/            ← 静态链接库
│   ├── libgsoapssl++.a     ← gSOAP SSL++ (SOAP over HTTPS)
│   ├── libcurl.a           ← libcurl HTTP 客户端
│   └── lib_s10entry.a      ← S10 入口
└── tmp_so/         ← 动态库插件 (~120个 .so, 主要体积来源)
```

## 二、二进制角色分析

### ztlig2 — X2 (HI2) 拦截数据处理器

```
file ztlig2 → ELF 64-bit LSB executable, x86-64, dynamically linked,
              interpreter /lib64/ld-linux-x86-64.so.2, for GNU/Linux 2.6.32,
              with debug_info, not stripped
```

**功能**: 汇聚所有厂商 X2 IRI 数据 → ASN.1/BER 解码 → 事件转换 → JSON CDR → Kafka/SFTP 输出

**ldd 显示的依赖层级**：依赖 libpthread + libssh2 + libcrypto + 大量找不到的 so（运行时通过 LD_LIBRARY_PATH 加载 tmp_so/）

**strings 印证的关键函数**：
- `ALU_X2_TcpRcvTh` — 每个厂商独立 TCP 接收线程
- `Eric_limsProc` — 爱立信 LIMS 数据处理
- `DecE101HI2`, `DecZTEX2`, `DecX2NSNAsn1` — 各厂商解码器
- `FillHI2_MsgProc`, `Trans_UmtsEvent` — 事件填充与转换
- `Lig2IriContentPrint` — IRI 内容输出
- `Lig2ProcRealtimeLocation` — 实时位置处理
- `LigFindSpecialTarget` — 特殊目标查找

### ztlig3 — X3 (HI3) 内部监控数据处理器

```
file ztlig3 → ELF 64-bit LSB executable, x86-64, dynamically linked,
              interpreter /lib64/ld-linux-x86-64.so.2, for GNU/Linux 2.6.32,
              with debug_info, not stripped
```

**功能**: X3 RCE 内部协议处理，DPDK 高速收包，超时管理，数据转 ztlig2 输出

**strings 印证的关键函数**：
- `Hi3SessionTimeoutTh` — HI3 会话超时线程
- `Lig3TransHi2Msg` — X3→X2 消息转发
- `DPDK init`, `g_ztlig3_dpdkSndPortId` — DPDK 快速数据面
- `g_ztlig3_config`, `g_ztlig3_global_info` — 全局配置结构
- `acSicmsSendMac`, `acSicmsRecvMac` — SICMS 对接

### libwebhi1.so — X1 (HI1) 设控接口库

**功能**: 承载所有厂商 X1 设控协议（SOAP/HTTPS/TCP），提供统一设控入口

## 三、tmp_so/ 分类分析

### 按接口分类

| 接口 | 数量 | 用途 |
|------|:----:|------|
| **X1 (HI1)** — 设控命令 | ~10 | 各厂商 X1 设控协议适配 |
| **X2 (HI2)** — 拦截数据 | ~20 | 各厂商 X2 IRI 数据解码 |
| **X3 (HI3)** — 内部监控 | ~8 | MSC 内部 RCE 协议处理 |
| 基础设施 | ~30 | 通信/编解码/存储/加密 |
| 音频编解码 | ~25 | 媒体面解码 |
| 网络传输 | ~15 | TCP/UDP/SIP/RTMP/DPDK |

### 按厂商分类

| 厂商 | X1 | X2 | X3 | 前缀模式 |
|------|:--:|:--:|:--:|----------|
| **爱立信 Ericsson** | 3 | 1 | - | `ericlis`, `eric_x2` |
| **中兴 ZTE** | 2 | 4 | 3 | `ztev3lis`, `ztev4lis`, `zte_x2`, `x3zte` |
| **华为 Huawei** | 1 | 6 | 2 | `hw_`, `hw_5gc`, `hw_epc`, `hw_msc`, `hw_ngn` |
| **诺基亚 NSN** | 1 | 2 | 1 | `nsn`, `nokia_lispro` |
| **阿尔卡特 ALU** | - | 1 | - | `alu_csx2` |
| **Mavenir** | - | 1 | - | `mavenir_x2` |
| **VoLTE** | - | 1 | - | `volte_x2` |
| **ETSI 标准** | 1 | - | 1 | `etsihi1`, `etsihi3` |
| **Utimaco** | 1 | - | - | `utimacox1` |
| **Zeel** | 1 | - | - | `zeelx1` |
| **Group2K** | 1 | - | - | `group2kx1` |
| **UAG** | 1 | - | - | `uagx1` |
| **E33108** | - | - | 1 | `x3e33108` |

### 基础设施库

| 类别 | .so 文件 | 用途 |
|------|---------|------|
| **ASN.1/BER** | `libber.so`, `libe102232.so`, `libe101671.so` | 协议解码 |
| **Kafka** | `librdkafka.so`, `libkafka.so` | 消息队列输出 |
| **Redis** | `libhiredis_vip.so` | 目标缓存/状态 |
| **SFTP** | `libsftpclient.so`, `libsftpserver.so` | 文件传输 |
| **JSON** | `libcJSON.so` | JSON 序列化 |
| **SOAP** | 静态 `libgsoapssl++.a` | SOAP over HTTPS |
| **SSL** | `libwebsockets.so`, `libssh2.so` | 加密通信 |
| **加密** | `libdes.so`, `libencrypt.so`, `libpspcencrypt.so`, `libgjencrypt.so` | 数据加密 |
| **SIP** | `libpjsip.so`, `libdecsip.so` | SIP 协议分析 |
| **RTP/语音** | `librtp.so`, `librtpDec.so`, `libsendRtp.so`, `libsendVoic.so` | 语音流处理 |
| **DPDK** | `libdpdkfwd.so`, `libdpdkfwdtsps.so` | 高速数据面 |
| **RTMP** | `librtmp.so`, `librtmppusher.so` | 流媒体推送 |
| **FTP** | `libftp.so` | 文件传输 |
| **XML** | `libmxml.so` | XML 解析 |
| **ETL** | `libxyetl.so` | ETL 数据处理 |
| **线程池** | `libthreadpool.so` | 多线程管理 |
| **公共通信** | `libztligcomm.so`, `liblig1comm.so` | ZTLIG 内部通信 |
| **网络** | `libsocket.so`, `libipv6.so` | TCP/UDP/IPv6 |
| **Agent/Target** | `libagent.so`, `libtarget.so` | 管理 |
| **Shell/Debug** | `libztsh.so`, `libcomdbg.so` | CLI 调试接口 |

### 音频编解码

| 编解码 | .so 文件 |
|--------|---------|
| G.711 A/μ-law | `libg711.so` |
| G.721 | `libg721.so` |
| G.722 / G.722.1 | `libg722.so`, `libg7221.so` |
| G.723.1 | `libg723.so`, `libg7231.so` |
| G.729 | `libg729.so` |
| AMR-NB / AMR-WB | `libamrnb.so`, `libamrwb.so` |
| GSM FR / HR / EFR | `libgsmfr.so`, `libgsm_hr.so`, `libgsmefr.so` |
| SILK (Skype) | `libSKP_SILK_SDK.so`, `libsilkDecode.so` |
| Speex | `libspeex.so` |
| EVS (4G/5G) | `libevs.so` |
| FFmpeg 全家桶 | `libavcodec.so`, `libavformat.so`, `libavutil.so`, `libavdevice.so` 等 |
| 自定义解码 | `libffmpegDec.so` |

## 四、分析 SOP

### Step 1: 目录概览

```bash
find <DIR> -maxdepth 3 -type f | head
find <DIR> -maxdepth 3 -type d | sort
du -sh <DIR> <DIR>/tmp_so <DIR>/lib
```

### Step 2: 识别主二进制

```bash
file ztlig2 ztlig3
ls -lah ztlig2 ztlig3   # 体积 = 功能复杂度
```

### Step 3: 依赖分析

```bash
ldd ztlig2              # 运行时依赖（not found = LD_LIBRARY_PATH）
```

### Step 4: 功能预览

```bash
strings ztlig2 | grep -iE '版本|version|gcc|build|202' | head  # 构建信息
strings ztlig2 | grep -iE 'proc|thrd|init|recv|send|error|fail' | sort -u | head 50
strings ztlig2 | grep -iE 'zte|hw|eric|nsn|nokia|alu|kafka' | sort -u  # 厂商/平台
```

### Step 5: 分类 .so 文件

按厂商前缀分类（erixxx = Ericsson, hw_xxx = Huawei, zte_xxx = ZTE, nsn_xxx = Nokia）
按接口后缀分类（x1, x2, x3, lis, pro 等）
按功能分类（codec, network, crypt, transport）

### Step 6: 绘制架构

```
核心角色: ztlig2(X2), ztlig3(X3), libwebhi1(X1)
         ↓           ↓            ↓
各厂商插件 → 解码 → 转换 → 输出(Kafka/SFTP)
```

## 五、构建特征

- 目标平台: **Linux x86-64, glibc 2.6.32+**（非常老的内核兼容）
- 调试符号: **with debug_info, not stripped**（可 gdb 直接调试）
- 动态链接: 大部分库运行时通过 `LD_LIBRARY_PATH` 加载到 `tmp_so/`
- 静态链接: gSOAP 和 libcurl 是 `.a` 静态库
- 总大小: ~114MB（FFmpeg 全家桶和音频编解码占大头）

## 六、注意事项

- `not stripped` = 发布的是 debug 版本，生产环境可以考虑 strip 减小体积
- Linux 2.6.32 兼容 = 支持 CentOS 6.x / RHEL 6.x 等老系统
- 大量 `lib*.so => not found` 在 ldd 中是正常的 — 运行时通过环境变量解决
- 如果有多个版本的 so（如 `librdkafka.so` + `librdkafka.so.1`），运行时只会加载 linker 找到的那个

---

## 七、完整发行包结构分析（ZTLIG_Bin_X86Centos）

> 来源：`ZTLIG_Bin_X86Centos_20251212_4a5960_a27cfd.tar.gz`
> 版本：**LISTENER V1.1.02_LIG_T11**
> 构建日期：2025-12-12
> 包大小：316MB(gz) → 628MB(解压)

### 7.1 目录结构

解压后为单一 `bin/` 目录，包含：

```
bin/
├── ztlig1           ← X1 设控引擎 (146KB)
├── ztlig2           ← X2 拦截数据引擎 (360KB)
├── ztlig3           ← X3 内部协议引擎 (126KB)
├── cmf              ← 配置管理框架 (88KB)
├── psm              ← 抓包管理 (71KB)
├── psm_ass          ← 抓包辅助进程 (192KB)
├── rvf              ← 语音文件管理 (317KB)
├── ssf              ← 会话管理 (221KB)
├── ztlig.cfg        ← 主配置（GLOBAL/ZTLIG1/2/3/NE/VNE/LEA/SSF/RVF）
├── psm_cfg.ini      ← 抓包配置
├── numa.h / numaif.h ← NUMA 头文件（编译用）
├── lib/             ← 3个静态库（libgsoapssl++.a, libcurl.a, lib_s10entry.a）
├── lib/             ← 127个动态库.so（同 tmp_so/ 内容一致）
├── soft/            ← 第三方构建工具源码包
│   ├── openssl-1.0.2p.tar.gz
│   ├── gsoap_2.8.119.tar.gz
│   ├── libiconv-1.15.tar.gz
│   ├── rtmpdump-2.3/ (含编译产物)
│   ├── meson-0.56.2/
│   ├── pyelftools-0.31/
│   ├── redis/ (含 redis-3.2.3/7.0.4)
│   ├── ffmpeg-5.1.1.tar.xz
│   ├── dpdk-22.11.4.tar.xz
│   ├── nasm-2.13.03
│   ├── libssh2-1.8.0
│   └── 其他 (libtool/automake/gettext/snmp++/mxml/libuuid 等)
├── OpenVox/         ← OpenVox DAHDI 驱动 + Asterisk 11.25.3
│   ├── asterisk-11.25.3.tar.gz
│   ├── chan_ss7.so （已编译 SS7 通道插件）
│   ├── openvox_dahdi-linux-complete-current.tar.gz
│   └── firmware_package/ (DAHDI 固件 15个)
├── mysql/           ← libzdb 数据库连接库
├── shell/           ← 部署运维脚本（14个sh + 4个exp）
└── scripts/         ← MySQL/Sybase 建表/存储过程脚本
```

### 7.2 进程架构与进程间通信

```
                 cmf（配置管理框架:88KB）
                /    |    \       \
          ztlig1  ztlig2  ztlig3   ssf（会话管理:221KB）
            |       |       |       |
            |       +---rvf（语音落地:317KB）←── RTP
            |       +---psm（抓包:71KB）
            |       +---psm_ass（抓包辅:192KB）
            |
      Kafka ──→ Kafka brokers → OWLS 消费
```

| 进程 | 大小 | 功能 | 关键端口 |
|------|:----:|------|:--------:|
| **ztlig1** | 146KB | X1 设控引擎 — Kafka 设控消息 → 各厂商 NE X1 指令 | X1:50000, TCP:10300 |
| **ztlig2** | 360KB | X2 信令面 — NE IRI → ASN.1/BER → JSON CDR → Kafka | X2:8460, TCP:10460 |
| **ztlig3** | 126KB | X3 协议引擎 — DPDK 高速收包 → SICMS 输出 | X3:8480, TCP:10480 |
| **ssf** | 221KB | SIP-I 会话管理 — SIP 解析 + 三码/SDP/位置提取 | SIP:8480, TCP:11300 |
| **rvf** | 317KB | RTP 媒体面 — 语音文件落地(.0+.fin) | RTP:20000-20011, TCP:11400 |
| **cmf** | 88KB | 配置管理框架 — 持久化/进程间配置同步 | - |
| **psm** | 71KB | TCP 抓包管理 | - |
| **psm_ass** | 192KB | 抓包辅助进程（FFmpeg 解码） | - |

### 7.3 BuildID 验证

包内二进制与现有 tmp_so/ 相同构建版本：

| 文件 | BuildID (SHA1) |
|------|----------------|
| `ztlig2` | `4df2b7b37cab032357a7780c1944cb2e08ea4db5` |
| `ztlig3` | `af3edf96effa6bfd23266e5aaaae5a141d9fd4ce` |

结论：**现有 `tmp_so/` 部署的就是此发行包**。不需要重复替换。

### 7.4 ztlig.cfg 配置体系

配置分 4 层，每层有独立的配置段落：

| 段落 | 序号范围 | 示例 | 用途 |
|------|:--------:|------|------|
| `[GLOBAL]` | - | ftp 密码、kafka brokers、psm 路径 | 全局默认值 |
| `[ZTLIG1_300]` | 300+ | X1 端口、DB IP、夜间同步 | ztlig1 进程参数 |
| `[ZTLIG2_460]` | 460+ | X2 端口、LEA 端口、会话超时 | ztlig2 进程参数 |
| `[ZTLIG3_480]` | 480+ | X3 端口、DPDK 核心、sicms 超时 | ztlig3 进程参数 |
| `[NE_66X]` | 660-670 | IP、厂商、版本、X1/X2/X3 参数 | 物理网元定义 |
| `[VNE_76X]` | 760-770 | vne_type、operid、incptType | 虚拟网元定义 |
| `[LEA_800]` | 800+ | Kafka topic、redis、sftp、语音路径 | 执法机构配置 |
| `[SSF_1300]` | 1300+ | SIP 超时、接口模式 | 会话管理参数 |
| `[RVF_1400]` | 1400+ | RTP 端口范围、编解码 | 语音落地参数 |

关键参数速查：

| 参数 | 含义 | 典型值 |
|------|------|--------|
| `vne_type` | 网元类型 | MSCs/MSCe/SGSN/GGSN/IMS/VOLTE |
| `incptType` | 拦截类型 | 1=IRI, 2=CC, 3=IRI+CC |
| `speechtype` | 语音合并模式 | 0=合并, 1=分离, 5=分割 |
| `x2_transtype` | X2 传输方式 | tcp/ftp/sftp |
| `x1_transtype` | X1 传输方式 | tcp/https/http |
| `hi2_neid` | HI2 报告 NEID | 123456789 等 |
| `networkType` | 网络类型 | 1=CS 2=PS 3=EPC 4=IMS 5=5GC |

### 7.5 进程 CLI 命令体系（ztsh shell）

每个进程有专属的 INI 命令定义文件（`shell/conf/*.ini`），通过 ztsh shell 接入 CLT：

| 进程 | INI 文件 | 命令 ID 范围 | 示例命令 |
|------|----------|:------------:|----------|
| ztlig1 | `ztlig1.ini` | 31001-31705 | `show ztlig1 stat`, `syn ztlig1 hwmsc`, `debug ztlig1 ericlis21` |
| ztlig2 | `ztlig2.ini` | 32001-32203 | `show ztlig2 stat`, `show ztlig2 kafka stat`, `capture ztlig2 msg`, `debug ztlig2 ftp` |
| ztlig3 | `ztlig3.ini` | 33001-33010 | `show ztlig3 stat`, `show ztlig3 nic stat`, `write ztlig3 target file` |

支持命令类型：
- `show` — 统计信息（mainframe/hi2/x2/kafka/nic/ne/lea）
- `clear` — 重置统计
- `debug on/off` — 调试开关（ftp/hw x2/zte lis/ericlis/huawei 等）
- `capture on/off` — 抓包控制
- `write` — 写日志/目标文件
- `syn` — 目标同步（各厂商专用）
- `start ... list` — 目标列表同步
- `quit` — 退出进程

### 7.6 部署工具链

| 脚本 | 功能 |
|------|------|
| `ztlig_install.sh` | 主安装 — 配置 ulimit/open-files 限制 |
| `ztlig_uninstall.sh` | 卸载 |
| `PspcAutoStart.sh` | 开机自启配置 |
| `dpdk_setup.sh` | DPDK 大页内存 + 网卡绑定 |
| `psm_install.sh` / `psm_uninstall.sh` | 抓包模块安装/卸载 |
| `ztsh_install.sh` / `ztsh_uninstall.sh` | ztsh shell 安装/卸载 |
| `install_keep_cmf.sh` / `keepautocmon.sh` | CMF 保活 |
| `keeppsmon.sh` / `systemd-keeppsmon.service` | systemd 保活服务单元 |
| `clearVoice.sh` | 语音文件清理 |
| `telnet/telnet_addlea_cs.exp` | Telnet expect 自动化 |

### 7.7 分析 SOP（发行包版）

```bash
# 1. 查看版本
cat bin/shell/version                           # LISTENER V1.1.02_LIG_T11

# 2. 识别所有二进制
file bin/ztlig1 bin/ztlig2 bin/ztlig3 bin/cmf bin/psm bin/psm_ass bin/rvf bin/ssf
ls -lah bin/ztlig* bin/cmf bin/psm bin/psm_ass bin/rvf bin/ssf

# 3. 验证 BuildID（对比现有部署是否同版本）
readelf -n bin/ztlig2 | grep BuildID
# 与现场 ztlig2 对比：相同则无需替换

# 4. 分析配置架构
grep '^\[' bin/ztlig.cfg                         # 列出所有配置段落
grep '^#define' bin/shell/conf/ztlig2.ini        # 列出所有 CLI 命令 ID

# 5. 确认厂商支持
grep 'version' bin/ztlig.cfg | grep -v '^#' | sort -t'=' -k2

# 6. 对比 .so 差异
ls bin/lib/ > /tmp/pkg_so.txt
ls tmp_so/ > /tmp/cur_so.txt
diff /tmp/pkg_so.txt /tmp/cur_so.txt
```
