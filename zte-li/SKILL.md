---
name: zte-li
description: ZTLIG 合法监听网关系统 — 进程架构、ztlig.cfg 全量配置（NE/VNE/GLOBAL/LICENSE）、巡检排障、升级部署。注意：ZTLIG 厂商为 Sinovatio（中新赛克），非 ZTE。skill 名为历史命名，内容已全部修正。
category: telecom
---

# ZTLIG 合法监听网关系统

ZTLIG(Sinovatio) 是标准合法监听网关系统，对接华为/中兴/爱立信/NSN/UTIMACO 等厂商网元，完成 X1/X2/X3 接口的设控管理、信令处理、媒体还原。

当用户提及 ZTLIG、ztlig1、ztlig2、ztlig3、ssf、rvf、LIG 部署、合法监听网关、LI 网关运维时触发。

---

## 一、触发条件

- ZTLIG、ztlig1/2/3、ssf、rvf、cmf
- LI 网关部署、升级、巡检
- ztlig.cfg 配置（NE/VNE/GLOBAL/LICENSE）
- Kafka 设控 topic（TARGET_INFO / OWLS_TMC）
- 语音文件（Liid.cin.operatorid.neid.direction）
- HI2 对接、2口/3口抓包
- 多 TMC 模式、三方同步

## 二、系统架构

### 进程说明

| 进程 | 接口 | 功能 |
|------|------|------|
| **cmf** | 内部 | 配置管理框架 — 持久化/进程间同步 |
| **ztlig1** | HI1 / X1 | 设控管理 — Kafka 设控消息 → 网元指令 → 响应推送 |
| **ztlig2** | HI1 / X2 | 信令面 — NE 的 IRI 报告（TLV 编码）→ JSON CDR → Kafka |
| **ztlig3** | EPC / DPDK | EPC 流量转接 → 剥离头 + 三码/位置 → DPDK → SICMS |
| **ssf** | SIP-I | SIP-I 会话管理：SIP 解析 → 三码/SDP/位置提取 |
| **rvf** | RTP | 媒体面：RTP 流量 → 语音文件 (.0 + .fin) |
| **psm** | TCP | 抓包管理 |
| **psm_ass** | TCP | 抓包辅助（FFmpeg 解码）|

### 数据流

```\n     cmf（配置中心）\n        |\nKafka 设控 → ztlig1 → NE\n                    NE X2 → ztlig2 → CDR JSON → Kafka(实时+离线)\n                    NE SIP-I → ssf → voiceCtrl → rvf → 语音文件\n                    psm → 抓包(pcap)\n```

## 三、ztlig.cfg 配置参考

### NE-COM（物理网元通用配置）

关键配置项：vendor/version、x1_ip/port/user/pwd、x2_transtype/x2_ip、x3_transtype/x3_ip、trace_type

### VNE-COM（虚拟网元通用配置）

| 配置项 | 关键说明 |
|--------|---------|
| vne_type | MSCs/MSCe/SGSN/GGSN/PDSN/iHLR/HLRe/HSS/MME/SGW/PGW/VOLTE/IMS/GSM/LTE |
| speechtype | 0=合并, 1=分离, 5=分割两个话单(ZTE V4 LIS特有) |
| incptType | 1=IRI, 2=CC, 3=IRI+CC（AGCF/SBC配3, IMS/GTAS配1）|
| ulicver | Ericsson LI-IMS/zte_v3_lis/nsn_lis 需配置 |

### GLOBAL（全局配置）

| 配置项 | 说明 |
|--------|------|
| ztlig.x_ftp.usr/pwd | X2/X3 FTP/SFTP 登录用户名密码（必配）|
| ztlig.dbLeaID | 多 TMC 模式开关（0=关, >0=开）|
| ztlig.kafka_operations_topic/brokers | 进程信息推送（可选）|

### LICENSE（许可证控制）

17 项许可证控制项：max_target/max_lea/max_vne + 各厂商接口开关（hw_ne/zte_lis_v3_v4/eric_lis_v1_v2dot1/nsn_ne/utimaco_ne 等）

## 四、现场巡检命令

| 进程 | 命令 | 正常指标 |
|------|------|---------|
| ztlig1 | `show ztlig1 {id} mainframe stat` | 设控/停控正常 |
| ztlig2 | `show ztlig2 {id} kafka stat` ×2 | sendFailNum=0, sendSuccNum增长 |
| ztlig3 | `show ztlig3 {id} nic stat` ×2 | oerrors=0, obytes变动 |
| ssf | `show ssf {id} stat` ×2 | RecvNum增长 |
| rvf | `show rvf {id} stat` ×2 | RecvTotalMsgLen/CurSessionNum增长 |
| OpenVox | `show rvf 1400 kafka stat` | sendsucc正常 |

排障日志：
```bash
# 使用通配符 ztlig2*.* 匹配所有版本和端口日志（含 .txt / .old / .1 .2 等）
cat ztlig1.*.txt* | grep -i \"error\"
cat ztlig2*.* | grep EncodeToJson > hi2_all.txt
cat ztlig2*.* | grep \"LIID\\\\\\\":\\\\\\\"18041\\\" > liid-18041.txt
cat ztlig2*.* | grep \"CIN\\\\\\\":\\\\\\\"2491250814467\\\" > cin-xxx.txt
# grep -a 强制按文本处理二进制日志文件（避免只输出"Binary file matches"）
cat ztlig2*.* | grep -a \"psdpcscf02.191\" > cid-target.txt
```

### ztlig2 Kafka JSON CDR 字段说明

ZTLIG 将 X2 接口的 IRI 报告解码后推送到 Kafka topic `OWLS_TMC_REALTIME` 和 `OWLS_TMC_OFFLINE`，JSON 消息格式：

| 字段 | 说明 | 示例 |
|------|------|------|
| `LIID` | 拦截目标 ID | `"10331"` |
| `CidNum` | 话单 ID（CS 域 = 序号, IMS 域 = ChargingID） | `"95138331"` / `"psdpcscf02.191..."` |
| `OperID` | 运营商 ID（含 MCC+MNC） | `"63407"` (MCC=634 Sudan, MNC=07 ZAIN) |
| `NeidType` | 网元类型 | `0`=CS, `2`=IMS |
| `Neid` | 网元标识（含国家码） | `"2491250814470"` |
| `VneID` | 虚拟网元 ID | `"2"` |
| `Vendor` | 厂商 | `"hw"` |
| `NetworkType` | 网络类型（`11`=CS 域, `13`=IMS/VoLTE/VoWiFi） | `11` |
| `EventDetail` | 事件类型（见下表） | `10`=呼叫发起 |
| `EventDirection` | 事件方向 | `1`=主叫 |
| `MSISDN` | 用户号码 | `"249123022580"` |
| `CallingNum` | 主叫号码 | `"249123022580"` |
| `CalledNum` | 被叫号码 | `"249918312362"` |
| `CcLid` | HI3 关联 ID（CS 域） | `"95138331"` |
| `CallDuration` | 通话时长（BYE 时携带） | `"000007"` (7秒) |
| `IMSI` | 国际移动用户标识 | `"634070144056633"` |
| `SsCode` / `SsSubCode` | 补充业务码（REGISTER 时） | 可选 |

### EventDetail 对照表

| EventDetail | CS 域含义 | IMS 域含义 |
|-------------|----------|-----------|
| `10` | 呼叫发起 (Setup/INVITE) | INVITE |
| `11` | 应答 (Connect/200 OK) | 200 OK |
| `12` | 进展 (Alerting/Progress) | ACK/PRACK |
| `13` | 释放 (Release/BYE) | BYE |
| `14` | 前转 (Forward) | — |
| `15` | 切换 (Handover) | — |
| `17` | 位置更新/注册 (REGISTER) | REGISTER |
| `18` | 去注册/关机 (Deregister) | Deregister |

### ztlig2 LigCdr JSON 提取工具

`~/PCAP/20260623-A1-VOWIFI/extract_ligcdr.py` 从 ZTLIG2 日志中批量提取 LigCdr JSON 记录，支持 EventDetail/LIID/MSISDN/CIN/时间范围过滤、去重、统计、交互菜单，以及 ijq 或 JSON Crack 可视化。适用于对数 GB 级别日志进行结构化分析。

支持文件格式：.txt/.log/.gz/.tar.gz/.tgz/.zip（自动识别）。
**注意**：`A1-ztlig/` 下有 `.gz` 后缀但实际是纯文本的假 gzip 文件（如 `ztlig2.460.gz`），会被 `gzip.open()` 误判为 `BadGzipFile`。用 `list_input_files` 扫描目录时建议排除 `.gz` 文件，或只传 `.txt` 文件路径。
V1.2 新增：非 JSON 日志行文本匹配筛选（`P-Charging-Vector`、SIP 消息头等关联行输出到 `raw_matches_filtered.txt`）、EventDetail/Vendor/Neid 过滤实际生效、时间输入标准化（同时支持 `YYYYMMDDHHMMSS` 和 `YYYY-MM-DD HH:MM:SS`）。

详尽的用法示例和参数说明见 `references/ztlig2-ligcdr-extraction.md`。

**ijq 安装**：`ijq`（ijq 交互式 jq）通过下载 GitHub release 二进制到 `~/.local/bin/` 安装：
```bash
# ijq v1.3.0，项目已迁移到 codeberg.org/gpanders/ijq
curl -sL "https://codeberg.org/gpanders/ijq/releases/download/v1.3.0/ijq-1.3.0-linux-amd64.tar.gz" -o /tmp/ijq.tar.gz
cd /tmp && tar xzf ijq.tar.gz && cp ijq-*/ijq ~/.local/bin/ && chmod +x ~/.local/bin/ijq
# 验证：ijq -V → "ijq 1.3.0"
# 需要 ~/.local/bin/ 在 PATH 中
```

### ztlig2 日志分析速查

```bash
# CS 域日志特点：大量 REGISTER(17)+INVITE(10)+BYE(13)，无 PANI/SSF/RVF
# IMS 域日志特点：含 P-Access-Network-Info、小区 ID、Wlan-ue-local-ip

# 统计 EventDetail 分布
grep -oP 'EventDetail":\d+' ztlig2*.* | sort | uniq -c | sort -rn

# 统计 NetworkType 分布
grep -oP 'NetworkType":\d+' ztlig2*.* | sort | uniq -c | sort -rn

# 提取所有 IMSI
cat ztlig2*.* | grep -a "IMSI" | grep -oP 'IMSI":"[^"]+' | sort -u

# 按 LIID 查话单量
grep -oP 'LIID":"\d+' ztlig2*.* | sort | uniq -c | sort -rn | head -20

# 查看每天消息量
grep -oP '\d{4}-\d{2}-\d{2}' ztlig2*.* | sort | uniq -c | sort -n
```

### PCAP → ZTLIG CDR 交叉验证方法

当需要通过 X2 接口 PCAP 抓包验证 ZTLIG 解码是否完整时：
1. 在 LIG 上对 X2 端口抓包：`tcpdump -i any port {x2_port} -w x2.pcap`
2. 用 ETSI-ASN1-Assistant 解码 PCAP（选对应的厂商模式，如 hw-ims）
3. 从 ZTLIG 日志中提取对应时间段/目标的 Kafka JSON CDR
4. 对比 PCAP 中 SIP 消息原始字段 vs ZTLIG CDR 输出字段
5. 常见发现：ZTLIG 遗漏 Wlan-ue-local-ip、UE IP/Port、SBC 域名等 PANI 字段
6. 详细交叉验证案例见 `references/ztlig-cdr-pcap-cross-validation.md`

日志打包：
```bash
# 打包所有 ztlig2 日志（归档名在前，通配符在后）
# 忽略"file changed as we read it"警告（正在写入的活动文件末尾可能不完整）
tar czf ztlig2_$(date +%Y%m%d_%H%M%S).tar.gz ztlig2*.* --warning=no-file-changed

# 排除当前活动文件，只打包已轮转的旧日志
tar czf ztlig2_history_$(date +%Y%m%d_%H%M%S).tar.gz --exclude="ztlig2.460.txt" ztlig2*.*

# 只打包 .old 和带序号的历史日志
tar czf ztlig2_old_$(date +%Y%m%d_%H%M%S).tar.gz ztlig2*.old ztlig2*.*.1 ztlig2*.*.2 2>/dev/null
```

## 五、抓包命令

| 进程 | 模式 | 命令 |
|------|------|------|
| ztlig2 | TCP/UDP | `tcpdump -i {网卡} port {x2_port}` |
| ztlig2 | FTP | `tcpdump -i {网卡}`（不指定端口） |
| ssf | SIP-I/IMS-base | `tcpdump -i any port {sipUdpPort}` |
| rvf | sdpport | `tcpdump -i any port "20000 or 20002 or 20004"` |
| rvf | x3port | `tcpdump -i any port {x3port}` |

## 六、ztlig_target.txt 字段

23 字段（多 TMC 模式 25 字段）：

| # | 字段 | 说明 |
|---|------|------|
| 1-2 | leaID, liid | LEA ID + LIID |
| 3 | targetType | 3=IMEI, 4=TEI, 5=IMSI, 6=MSISDN, 7=E.164, 8=SIP-URL, 9=TEL-URL |
| 4 | targetID | 布控目标 |
| 6 | incptType | 1=IRI, 2=CC, 3=IRI+CC |
| 8 | speechType | 0=合并, 1=分离 |
| 15-18 | startDay/Time/endDay/Time | 布控时间段 |
| 19-20 | virneID, neID | 虚拟/物理网元 ID |
| 21 | hw_lioid | 华为专用（lioid ↔ liid 映射）|
| 24-25 | tmcid, mcliid | 多 TMC 模式 |

## 七、版本升级

```bash
sh psm_uninstall.sh
pkill ssf; pkill rvf; pkill ztlig3; pkill ztlig2; pkill ztlig1; pkill cmf
mv bin/ dak_bin_$(date +%Y%m%d%H%M%S)
tar -xvf ZTLIG_Version_xxxxxx.tar.gz
cd bin/shell && sh ztlig_install.sh
cp ../bin_bak/ztlig_lic.key ./ && cp ../bin_bak/ztlig.cfg ./
./cmf -d y
```

## 八、常见报错

| 报错 | 原因 | 处理 |
|------|------|------|
| `LeaIdx invalid` | 1口 LEAID 与实际不符合 | 检查 ztlig_target.txt 和 cfg |
| `the ne is unlawful` | 新增网元 tneid 未加到 2口配置 | 配置 ztlig.ztlig2.{id}.tneid |
| `get actneID fail` | vneid 不存在 | 检查 vne/ne 配置 |
| `vneid[0] not support` | hi2_neid 未配置 | 通过日志确认 hi2_neid |
| alarm-id=504 | X1 认证失败 | 核对用户名/密码/NEID |
| alarm-id=512 | X1 通道中断 | 检查网络/防火墙 |

## 九、文件存储

```
语音文件：/data01/voice/{运营商}/{rvf进程号}/{日期}/{LIID}.{CIN}.{OperID}.{Neid}.{Direction}
完成标记：同名 .fin 文件（0字节）
Direction：0=混合, 1=上行, 2=下行
```

## 十、SIP 小区位置字段映射（LocationType/Location）与已知问题

ZTLIG 从华为 IMS/VoLTE SIP 的 `P-Access-Network-Info` 头域提取小区位置信息，映射到 OWLS TMC JSON 的 `LocationType` + `Location` 字段。详见 `references/ztlig-sip-location-mapping.md`。

| LocationType | 含义 |
|---|---|
| `1` | 通话中小区位置（SIP INVITE → PANI） |
| `4` | 注册/附着位置（SIP REGISTER → PANI） |

Location 值编码格式：`MCC MNC CELL_ID_HEX`（十六进制拼接），如 `6340704523F4C`。

### 已知问题：ZTLIG 遗漏 Wlan-ue-local-ip（公网 IP）解码

通过 PCAP 抓包 HI2 X2 接口数据与 ZTLIG Kafka JSON CDR 对比发现：

**SIP PANI 中实际存在的字段：**
```
IEEE-802.11;
  sbc-domain=psdpcscf02.ims.mnc007.mcc634.3gppnetwork.org;
  ue-ip=10.201.24.98;
  ue-port=5060;
  Wlan-ue-local-ip=196.202.142.135;   ← 实际存在于SIP消息中
  Wlan-ue-local-port=16567
```

**ZTLIG 的 Kafka JSON CDR 输出（OWLS_TMC_REALTIME/OFFLINE）中缺失：**

| ZTLIG CDR 包含 | ZTLIG CDR 缺失（SIP PANI 中实际存在） |
|---|---|
| LIID, CidNum | **Wlan-ue-local-ip**（WiFi 侧公网 IP） |
| MSISDN, CallingNum, CalledNum | **utran-cell-id-3gpp**（小区 ID） |
| EventDetail, EventDirection | **UE IP/Port**（10.201.24.98:5060） |
| CaptureTime | **SBC 域名** |
| CallDuration (BYE 时) | **接入类型**（IEEE-802.11 / UTRAN-FDD） |

**根因分析：** ZTLIG 的 HW IMS 解码模块（ssf 或 ztlig2 的华为插件）在解析 `P-Access-Network-Info` 头域时，只提取了 `LocationType` + `Location`（小区 ID 映射）写入 JSON CDR，**没有将 `Wlan-ue-local-ip` 这个 WiFi 侧公网 IP 字段解码输出到 Kafka 消息中**。

**影响：** OWLS TMC 界面上只能看到 VisitedNID/MSC 级位置，看不到 VoWiFi 用户真实的 WiFi 出口公网 IP，丢失了关键定位信息。

**排查/修复方向：**
1. 检查 `ztlig.cfg` 中 SSF/VNE 的 PANI 位置字段提取开关
2. 检查 ztlig2 的 HW IMS 解码插件版本是否支持 `Wlan-ue-local-ip` 字段
3. 如需在 CDR 中补全，需修改 SSF 的 SIP PANI 解析逻辑或升级解码插件版本
4. 对应过滤命令（在 LIG 上执行，加 `-a` 避免 Binary file 警告）：
   ```bash
   # 按 IMS ChargingID 过滤
   cat ztlig2*.* | grep -a "psdpcscf02.191" > cid-target.txt
   # 查原始 PANI 日志
   cat ztlig2*.* | grep -a "Wlan-ue-local-ip" > wifi_public_ip.txt
   cat ztlig2*.* | grep -a "P-Access-Network-Info" > pani_raw.txt
   ```

## 十一、关联知识

### 本地知识库笔记

- `huawei-hi2` — 华为 CS/IMS LI 协议及 X1/X2/X3 接口解码
- `etsi-lawful-intercept` — ETSI LI 标准体系
- `hw-li` — 华为 LI 全栈及多厂商对接

### ZTE CS LI 三接口规范

`~/knowledge/hi2/厂商对接/ZTE_CS_LI_HI1_HI2_HI3_三接口规范.md`

**HI1 — CLI 命令接口（Telnet/SSH，端口 23/22）**：
- 65xx 命令集：ADD LITGT(6505)/DEL LITGT(6506)/MOD LITGT(6507)/SHW LITGT(6508)/SHW TGTINF(6510)/SET BARRING(6529)
- 三级用户：260(NE超级) / 261(LEA管理) / 262(LEA操作)
- TT 参数：5=IMSI, 6=MSISDN, 3=IMEI, 8=SIP-URI, 20=ECGI 等
- SPEECHTYPE 6种语音模式：0~5（Combined A/B, Separated A/B/C/D）
- 反馈格式：`CMD=6505;RESULT=0:Succeed.;`
- 示例：`ADD LITGT: MCID=1: LIID=1: TT=5: TI=460030927640001: IT=3: FD=0:`

**HI2 — IRI 信令接口（ASN.1/BER，FTP 或 ROSE 传输）**：
- OID: `{0 4 0 2 2 4 3 7 1}`
- 记录类型：Begin[1]A1 / End[2]A2 / Continue[3]A3 / Report[4]A4 / Alarm[16]B0
- 中兴扩展事件：switchOnEvent(11), switchOffEvent(9), cCLinkStateReportEvent(10)
- 关键字段：LIID[1] / CID[2] / Timestamp[3] / PartyInfo[9] / Location[8] / SMS-report[14] / release-Reason[11]
- PartyInfo 含 imei/imsi/callingPartyNumber/calledPartyNumber/msISDN/sip-uri

**HI3 — CC 通话内容交付（ISDN/PRI/BICC/SIP-I）**：
- Mono(1路混合) / Stereo(2路上行+下行) 两种模式
- IAM 主叫=NEID，被叫=HI3Address
- **子地址关联 IRI↔CC**：Called Sub={OperatorID, CIN, CCLID}, Calling Sub={LIID, Direction, ServiceOctets}

### Utimaco LIMS RAI v16.1 协议

`~/knowledge/hi2/厂商对接/Utimaco_LIMS_RAI_v16.1_协议规范.md`

**会话层（RAI-SP，TCP 端口 52134）**：
- 7 种二进制 PDU：LOGIN(1) / REJECT(2) / ACCEPT(3) / COMMAND(4) / REPLY(5) / LOGOUT(6) / ABORT(7)
- LOGIN 固定 126 字节：user(21)+pwd(16)+newpwd(16)+version(4)+utcflag(1)
- 密码规则：8-15字符，至少2字母+2数字，无简单序列

**ICD 管理**：
- 生命周期：N(新建)→icdact→P(待处理)→A(活跃)→I(非活跃)→icdreport final→C(关闭)
- icdadd：lea+fileref+doo+start+stop+class 必填
- icdmod：可用 `stop=NOW` 立即停止
- icddel：仅 N 或 C 状态可删
- icdreport：intermediate(随时) / final(仅I状态)

**Target 管理（高频命令）**：
- **tadd**：`tadd icd=UemRefno tno=TargetNo ttype=TargetType liid=LiId net=Networks dtype=DataTypes mc_voice=X mc_iri=X doo=YYYYMMDD`
  返回 `tno_created tno_id=XXX`
- **tlist**：`tlist [icd=UemRefno] [tno=TargetNo]` — 支持 * 通配符
- **tdel**：`tdel tno_id=TargetNoId doo=DateOfOrder` — 仅 2 M 参数，无输出
- **tmod**：`tmod tno_id=TargetNoId [其他可选参数] doo=DateOfOrder`
  关键语义：`doo=M`，所有 `mc_xxx=O`（不传保留，传入替换），`liid=""` 清空，`mc_data=none` 禁用数据MC
- **tstate**：`tstate icd=UemRefno tno=TargetNo doo=DateOfOrder` — 3 M 参数，无输出
- **tnelist**：`tnelist neid=NeIdList` — neid 逗号分隔，输出 `netarget neid=X tno=Y`，Y 可能为 "Communication Error" 或 "Parsing Error"

**MC 管理**：
- **mcadd**：mctype 决定必备参数
  - FTP：ipaddr+user+pwd+dir
  - ISDN：isdn+cugilc+cugdnic
  - FTAM/X25：x25addr+tsel+ssel+psel+aent+user+pwd
  - TCP：ipaddr+port+dataloss+keepalive 等
  - 返回 `mc_created mc=MCId`
- **mcdel**：`mcdel mc=McId` — 被目标引用时返回 630
- **mcmod**：所有参数为 O，取决于 MC 类型允许集
- **mclist**：`mclist [mc=MCId] [lea=LeaId]` — 38 个输出字段

**NE 管理**：
- **nelist**：`nelist [neid=NeId] [provider=ProviderId] [all]`
- **neadd/nedel/nemod/necheck/nepurge**
- necheck 错误码 1~1002 含 Target installed/not installed, ISDN, MC installed 等
- nepurge 需 PURGE_NODE 许可，输出 `nepurgeerror neid=X result="Purge was successful" time="DD.MM.YY HH:MM:SS"`

**86 种 Target Type / 20 种 Network / Flags 体系**：详见知识库笔记。

### ASN.1/BER/PER 编解码参考

HI2 接口使用 ASN.1/BER 编码。Dubuisson ASN.1 教材的 Tagging/Constructed types/Extensibility (Ch12)、BER (Ch18)、PER (Ch20) 核心要点提炼见 `references/dubuisson-asn1-tagging-ber-per.md`。

包含：四种 tag class 编码、EXPLICIT/IMPLICIT/AUTOMATIC TAGS 模式对比、BER TLV 结构（T 字段单字节/多字节、L 字段三种格式）、各类型 BER 编码规则、PER 四种变体及编码量估算公式、HI2 实际应用场景解析。

## 十二、厂商LI文档入库工作流

当用户使用「学习」关键字逐段分享厂商LI原始文档时，遵循以下流程。

### 极低颗粒度逐段分享模式

此用户采用极低颗粒度逐段分享方式，文档内容按章节/命令逐步呈现，颗粒度可细到**单个单词甚至单字符**。典型流程：

1. **触发**: 用户发「学习」+ 文档名称/片段
2. **响应节奏**: 用户逐段发（"Description", "Syntax", "Arguments", "Status", "Output", "Examples", "Name M/", "O", "?"），每次回复简短确认（"已更新", "继续"），**不得催促或建议整段粘贴** — 耐心等待每段内容逐步呈现
3. **解析阶段**: 立即识别文档类型（HI1命令/HI2 ASN.1/HI3 CC/RAI协议），开始构建YAML frontmatter
4. **增量更新**: 每次收到新内容后用 `patch` 工具增量更新知识库笔记，必须**精确匹配原文英文措辞**，不改写不缩写
5. **参数表处理**: 每个参数逐行录入（Name + M/O + Description），MC参数等语义一致字段统一匹配英文原文
7. **入库阶段**: 写入 `knowledge/hi2/厂商对接/` 目录
8. **patch 上下文唯一性陷阱**：同样字符串（如 `| 0 | 成功 |`）可能在多个命令的状态码表中重复出现。必须包含更多上下文行（章节标题+完整表头行）确保唯一匹配，否则 patch 报 `Found 2 matches` 错误
7. **确认节奏**: 用户简短确认（"好的", "OK", "继续"）或继续贴更多内容即授权继续，不需要额外请示

## 十三、参考资料

- `知识/telecom/lawful_interception/ZTLIG运维手册.md`
- `知识/telecom/lawful_interception/华为CS_X接口说明与ZTLIG部署实战.md`
- `references/zte-epc-field-mapping.md` — ZTE EPC (EpsHI2Operations) ASN.1 字段映射 vs ETSI 标准
- `references/ztlig-sip-location-mapping.md` — ZTLIG SIP PANI 小区位置字段映射
| `references/ztlig-binary-structure-analysis.md` | ZTLIG 二进制程序结构分析指南（ztlig2/ztlig3/libwebhi1 角色、tmp_so/ 插件全分类、分析 SOP、发行包完整分析、进程架构、配置体系、BuildID 验证）|
| `references/ztlig-debug-flow.md` | ZTLIG 调试流程与问题排查方法论（5步排查法、分场景排障、ztsh CLI 命令、常见错误速查）|
- `references/utimaco-rai-commands.md` — Utimaco LIMS RAI 命令速查表（ICD/Target/MC/状态码）
- `references/utimaco-rai-quickref.md` — Utimaco LIMS RAI 常用命令模板
- `references/zte-cs-li-quickref.md` — ZTE CS LI HI1/HI2/HI3 命令速查表
- `references/ztlig2-ligcdr-extraction.md` — ZTLIG2 LigCdr JSON 提取工具（extract_ligcdr.py）用法参考
- `references/ztlig-log-analysis-workflow.md` — ZTLIG2 日志全量分析工作流（LIID/MSISDN 扫描→提取→深度分析→报告输出）
