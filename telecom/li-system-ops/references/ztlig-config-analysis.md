# ZTLIG 配置文件分析方法论

## 配置结构概览

ztlig.cfg 约 150+ 配置项，按 10 个章节组织：

1. **NE-COM** (~18项+厂商特有) — 物理网元
2. **VNE-COM** (~10项+厂商特有) — 虚拟网元
3. **LEA** (~22项) — 监听中心(Kafka/Redis/SFTP)
4. **ZTLIG1** (~6项) — 设控进程
5. **ZTLIG2** (~12项) — 信令处理
6. **ZTLIG3** (~13项) — EPC转接(DPDK)
7. **SSF** (~10项) — SIP-I会话
8. **RVF** (~12项) — RTP语音还原
9. **LICENSE** (~17项) — 厂商接口开关
10. **GLOBAL** (~5项) — FTP/多TMC/Kafka

## NE 配置模板

```
[NE_66X]
ztlig.ne.66X.valid_fg      = 1           # 启用
ztlig.ne.66X.tneid         = N           # 网元编号(1-50)
ztlig.ne.66X.vendor        = hw/zte/ericsson/nsn/utimaco/zeel/uag/group2k
ztlig.ne.66X.version       = hw_cs/hw_epc/zte_v3_lis/zte_v4_lis/ericsson_2dot1/...
ztlig.ne.66X.x1_ip         = <IP>       # 设控IP
ztlig.ne.66X.x1_port       = <port>     # 设控端口(华为MSC=6666, SBC=6000/9900)
ztlig.ne.66X.x1_user       = 1          # 用户名(通常固定1)
ztlig.ne.66X.x1_pwd        = <pwd>      # 密码(同一现场通常统一)
ztlig.ne.66X.x1_transtype  = tcp/ftp/https/http
ztlig.ne.66X.x2_ip         = <IP>       # X2数据IP
ztlig.ne.66X.x2_transtype  = tcp/ftp/sftp
ztlig.ne.66X.x3_ip         = <IP>       # X3内部IP  
ztlig.ne.66X.x3_transtype  = udp/tcp/ftp/UDP
ztlig.ne.66X.hw.alias      = <name>     # 网元别名
ztlig.ne.66X.hw.neid       = <id>       # 华为NEID(MSC=15位, SBC=4位)
```

## VNE 配置模板

```
[VNE_76X]
ztlig.vne.76X.tneid        = N           # 归属物理网元
ztlig.vne.76X.vneid        = N           # 虚拟网元编号(1-1000)
ztlig.vne.76X.vne_type     = MSCs/IMS/SBC/VOLTE
ztlig.vne.76X.operid       = 63407       # 运营商ID
ztlig.vne.76X.hi2_neid     = <id>        # X2报告中的网元号(与hw.neid一致)
ztlig.vne.76X.speechtype   = 0/1/5       # 0合并 1分离 5ZTE特有
ztlig.vne.76X.incptType    = 1/3         # 1仅IRI 3 IRI+CC
ztlig.vne.76X.ulicver      = 1           # X3 ULIC版本号
```

## networkType 速查

| 值 | 含义 |
|----|------|
| 1 | CS |
| 2 | PS |
| 3 | EPC |
| 4 | IMS |
| 5 | 5GC |
| 11 | CS_2G |
| 12 | CS_3G |
| 13 | CS_4G |
| 14 | CS_5G |
| 15 | PS_2G |
| 16 | PS_3G |
| 17 | PS_4G |
| 18 | PS_5G |

## 分析流程

1. 先理清 ZTLIG2 实例数 → 知道有多少网元通道
2. 逐一提取 NE 段 → 建立网元拓扑
3. 匹配 VNE → incptType 判断 IRI/CC 模式
4. 查 SSF/RVF → 了解 X3 信令模式和语音落地
5. 查 LEA → Kafka topic 体系/Redis/CC 地址
6. 比对同一运营商 A/B 站点配置可知差异项
