# ZTLIG Binary 结构分析

> 来源：ZTLIG_Bin_X86Centos_20251212_4a5960_a27cfd (LISTENER V1.1.02_LIG_T11)
> 构建：CentOS x86-64, Linux 2.6.32+, 含 debug_info 未 strip

## 进程架构 (8 个可执行文件)

| 可执行 | 大小 | 功能 |
|--------|------|------|
| ztlig1 | 146KB | X1 设控引擎 — 对接厂商 NE X1 协议，维护目标库 |
| ztlig2 | 360KB | X2 拦截数据引擎 — 接收/解码/转换/输出 IRI |
| ztlig3 | 126KB | X3 内部协议引擎 — DPDK 高速收包，HI3 会话管理 |
| cmf | 88KB | 配置管理框架 |
| psm | 71KB | TCP 抓包 (pcap) |
| psm_ass | 192KB | 抓包辅助 |
| rvf | 317KB | 语音文件管理 — RTP 接收/语音落地 |
| ssf | 221KB | 会话管理 — SIP-I 信令/TS 102232-5/CC |

## ztlig2 深度结构

### 主流程 main()
```
LigReadAllConfig() → ztlig_agent_init() → HI2_Init() → tbl_init()
→ SsfTblInit() → LigInitSftp() → tcp_init() → ztsh_init()
→ create_threadpool(N) → 创建常驻线程 → Lig2_Exit()
```

### 线程模型
```
常驻线程:
  LIG1liveTh              — ZTLIG-1 保活心跳
  lig2_live_check         — 自身存活检查
  ThreadCheckTh           — 通用定时检查
  ThreadCheckSsfAliveTh   — SSF 存活表维护

X2 厂商接入 (按需启动):
  TCP: X2_TcpListenTh → X2_TcpRcvTh (X2_TcpRecvNormal/MutiLink)
  UDP: X2_UdpRcvTh
  FTP: X2_FtpSrvListenTh → CtrlTh + DataTh + WatchTh
  SFTP: StartX2SftpProc
  厂商专属: ALU_X2_TcpRcvTh

内部处理:
  X2_MessageAdaptTh — 消息适配/分发
  X2_MsgQueZTENEV3Proc — 中兴 NEV3 队列
  X2_MsgQueZTENEV4Proc — 中兴 NEV4 队列
  X2UtimacoMsgQueProc — Utimaco 队列
```

### X2 数据处理流水线
```
网元 → ASN.1/BER → 厂商解码器(.so) → X2_MessageAdaptTh
→ ProcessX2Msg → Trans_UmtsEvent → X2neid_TransTo_Hi2Vneid
→ FillHI2_MsgProc → Fill_PartyInfoNum → Lig2PushE101671ToHi2
→ Lig2IriContentPrint → LEA 队列 → Kafka/文件输出
```

### 关键全局数据
```
g_ztlig2_config      — 配置结构体
g_ztlig2_lea_info    — LEA 信息表
g_ztlig2_ne_info     — NE 信息表
g_ztlig2_vne_info    — VNE 信息表
g_ztlig2_targetinfo  — 目标信息
g_ztlig2_sessionmanage_resource — 会话管理资源
g_ssfTbl / g_BKSsfTbl  — SSF 表(主/备份)
g_x2_que             — X2 消息队列
g_x2_rspQue          — X2 响应队列
```

## 厂商协议插件清单

### X1 (HI1) — 设控 (10 个)
libericlis1x1.so(爱立信v1), libericlis2dot1x1.so(v2.1), libericlis2dot4x1.so(v2.4)
libhwx1.so(华为), libztev3lisx1.so(中兴v3), libztev4lisx1.so(中兴v4)
libutimacox1.so(Utimaco), libzeelx1.so(Zeel), libgroup2kx1.so(Group2K)
libuagx1.so(UAG/Mavenir), libetsihi1.so(ETSI标准)

### X2 (HI2) — 拦截数据输出 (16 个)
爱立信: liberic_x2limspro.so
中兴: libzte_x2pro.so, libzte_x2lispro.so, libzte_x2v3nepro.so, libztex2.so
华为: libhw_mscx2.so, libhw_gsnx2.so, libhw_epcx2.so, libhw_ngnx2.so
      libhw_pdsnx2.so, libhw_5gcx2.so
NSN: libnokia_lisprox2.so, libnsnlipv1_x2.so
其他: libalu_csx2.so, libmavenir_x2.so, libvolte_x2.so

### X3 (HI3) — 内部监控 (9 个)
中兴: libx3ztev3ne.so, libx3ztev4ne.so, libx3ztev3lis.so, libx3e33108.so
华为: libhwpsnex3.so, libhwepcx3.so
NSN: libnsnx3.so
通用: libetsihi3.so, libhi3pro.so

## 配置体系

### ztlig.cfg 章节结构
- [GLOBAL] — FTP/Kafka/PSM/多TMC
- [ZTLIG1_3xx] — X1 设控进程
- [ZTLIG2_46x] — X2 处理进程 (tneid/networkType/超时)
- [ZTLIG3_48x] — X3 DPDK SICMS
- [NE_66x] — 物理网元
- [VNE_76x] — 虚拟网元
- [LEA_800] — 监听中心
- [SSF_130x] — 会话管理
- [RVF_140x] — 语音落地

### 关键字段速查
- networkType: 1-CS 2-PS 3-EPC 4-IMS 5-5GC 11~18=细粒度
- speechtype: 0=合并 1=分离 5=ZTE V4LIS分割
- incptType: 1=IRI 2=CC 3=IRI+CC
- syn_night: bit0=hw bit1=zte bit2=eric bit3=nsn bit4=utimaco
- X3 interfaceType: 1=SIP-I 2=TS-102232 3=Mavenir 4=ims/imsbase

## 安装布局
```
/usr/local/lib/ztlig/ ← .so 安装目录
ztlig.cfg              ← 主配置文件
bin/shell/             ← 安装脚本 + systemd保活
bin/shell/conf/        ← 进程 INI (管理命令定义)
```
