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

#### HW/ZTE (ASN.1 BER 厂商)

当需要通过 X2 接口 PCAP 抓包验证 ZTLIG 解码是否完整时：
1. 在 LIG 上对 X2 端口抓包：`tcpdump -i any port {x2_port} -w x2.pcap`
2. 用 ETSI-ASN1-Assistant 解码 PCAP（选对应的厂商模式，如 hw-ims）
3. 从 ZTLIG 日志中提取对应时间段/目标的 Kafka JSON CDR
4. 对比 PCAP 中 SIP 消息原始字段 vs ZTLIG CDR 输出字段
5. 常见发现：ZTLIG 遗漏 Wlan-ue-local-ip、UE IP/Port、SBC 域名等 PANI 字段
6. 详细交叉验证案例见 `references/ztlig-cdr-pcap-cross-validation.md`

#### Mavenir (XML/SOAP，非 ASN.1)

Mavenir 使用 XML+SOAP 架构（interfaceType=3），X2 IRI 以 `hi2-uag` XML 格式输出，SIP 信令放在 `<Payload>` CDATA 中。**不能用 ETSI-ASN1-Assistant 解码**，直接用文本工具：

1. 在 LIG 上抓包：`tcpdump -i em2 -w voltelog-X2.pcap`
2. 用 `tcpdump -A` + `strings` + `grep -oa` 直接提取 XML 和 SIP 原文
3. 从 ZTLIG 日志提取对应 Correlation-id 的 LigCdr JSON
4. 对比 Call-ID、Correlation-id、IMSI 等关键字段
5. 存在双 li-tid 现象（同一 SIP 消息发给两个监听目标）
6. 可通过 `grep -oa` 检查 SMS（`application/vnd.3gpp.sms`）
7. 详细 Mavenir 分析 SOP、命令模板、已知风险见 `references/ztlig-mavenir-analysis.md`

### ZTLIG1 X1 日志分析增强 (V4.0.1)

ETSI-ASN1-Assistant V4.0.1 的 X 接口日志分析模块对 ZTLIG1 日志进行了大幅增强（集成在主页面三列布局最右侧 🔬）：

**14 种命令识别（覆盖率 78%）：**
process_init / set_target / del_target / kafka_add_target / kafka_del_target / x1_send_cmd / hi1_queue / list_target_rsp / query_target / link_check / link_error / ne_no_response / location_report / etsi_liid_check / db_query / redis_sync

**提取字段：** cmd / liid / neid / vneid / sub_module / account / result / reason

**三种日志格式兼容：**
- 格式 A: `[时间][LEVEL][ztlig1:port][INFORM][ztlig-1_hwne][func]:body`
- 格式 B: `[时间][LEVEL][ztlig1:port][ztlig-1_hwne]:body`
- 格式 C: `[时间][LEVEL][ztlig1:port]:body`

**子模块(5种)：** ztlig-1_web(73%) / ztlig-1_hwne(20%) / ztlig1-db(5%) / ztlig-1(2%) / ztlig-1_etsi(0.7%)

**使用方式：** 主页第三列上传 → 自动识别文件类型 → 点击分析 → 双栏展示

**知识库经验文档：** `~/knowledge/telecom/lawful_interception/ztlig1-x1-log-analysis.md`

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

## 十三、ETSI-ASN1-Assistant V4 X 接口日志分析

ETSI-ASN1-Assistant V4.0.1 的 X 接口日志分析集成在主页面三列布局最右侧（🔬 图标），支持上传和分析 SSF/RVF/ZTLIG1/ZTLIG2 四种日志，双栏分栏展示（左=解析结果，右=原始日志），实时过滤 LIID/CIN/关键词/ERROR 级别。独立 `/x-interface` 路由仍向后兼容。

| 日志类型 | 接口 | 关键提取字段 | 日志头格式 |
|---------|------|------------|-----------|
| SSF | X2 (SIP 信令) | LIID, CIN, callId, SIP 方法 | `[时间][级别][ssf:端口][函数]` |
| RVF | X3 (RTP 媒体) | liid, correlationID, rtpSessionId | `[时间][级别][rvf:端口]` |
| ZTLIG1 | X1 (管理面) | 命令, 子模块, LIID, NEID, VNEID, 结果, 原因, 账号, 返回码 | `[时间][级别][ztlig1:端口]` _详见下方_ |
| ZTLIG2 | X2 (IRI/CDR) | LIID, CIN, EventDetail, 内嵌 LigCdr JSON | `[时间][级别][ztlig2:端口]` |

日志头正则: `\\[(\\d{4}-\\d{2}-\\d{2}\\s+\\d{2}:\\d{2}:\\d{2})\\]\\[(\\w+)\\s*\\]\\[(\\w+):(\\d+)\\](?:\\[([^\\]]*)\\])?`

### ZTLIG1 日志三种格式（A/B/C）

LOG_HEADER_RE 统一处理后，ZTLIG1 日志 body 有三种变体：

| 格式 | 典型行 | LOG_HEADER 第5组 | body 开头 |
|------|--------|-----------------|-----------|
| A | `[时间][DEBUG][ztlig1:300][INFORM][ztlig-1_hwne][func]:body` | `INFORM`(日志级别) | `[ztlig-1_hwne][func]:body` |
| B | `[时间][INFO][ztlig1:300][ztlig-1_hwne][func]:body` | `ztlig-1_hwne`(子模块) | `[func]:body` |
| C | `[时间][INFO][ztlig1:300]body` | `None` | `body` |

识别方法：
- **格式 A**：LOG_HEADER 第5组是日志级别标记（`INFORM`/`ERROR`/`WARNING`/`ALARM`/`DEBUG`）→ 从 body 开头提取子模块名 `^\[([^\]]+)\]`
- **格式 B**：LOG_HEADER 第5组是有效的子模块名 → 直接用第5组
- **格式 C**：LOG_HEADER 第5组为空 → 无子模块

**X1 解码器设计中需同时处理三种格式，否则子模块名会错取为日志级别或函数名。**

### ZTLIG1 body 子模块分布

| 子模块 | 占比(%) | 说明 |
|--------|---------|------|
| `ztlig-1_web` | ~73 | Kafka 设控消息处理、Redis 目标同步、Web 界面操作 |
| `ztlig-1_hwne` | ~20 | 华为网元 X1 通信（设控/停控/查询/连接检查） |
| `ztlig1-db` | ~5 | 数据库查询（License/目标记录） |
| `ztlig-1` | ~2 | 进程消息、通知、DB 停控确认 |
| `ztlig-1_etsi` | ~1 | ETSI LIID + TT + TI 合法性校验 |

### ZTLIG1 综合分析报告

上传 ztlig1 日志后，系统自动生成综合分析报告，包含：
- 概览: 时间范围、总行数、ERROR 数、LIID 数
- 子模块负载分布: web/hwne/db/etsi 占比(默认展开)
- X1 操作统计: 14 种命令出现次数
- LIID 统计: Top 15 LIID 及频率
- 设控/停控: Kafka 消息次数 + 去重 LIID 数
- 网元通信故障: 连接失败/链路错误/无响应 + 故障 NE Top(红色高亮)
- 关键样本: 8 类重要日志原文(Kafka/DB/网元/X1/Hi1 等)
- ERROR 样本: 全部 ERROR 级别日志原文

后端 `generate_ztlig1_report(parsed_lines)` 生成，API 的 `report` 字段返回。
前端 `buildReportHTML(report)` 渲染在 stats 栏下方、双栏上方。

### ZTLIG1 已知解析盲点

| 盲点 | 问题 | 影响 |
|------|------|------|
| `link_check`/`link_error` 的 `ne:31` 格式 | NEID_RE 的 `(?:tneID\|tneid\|ne_id\|neid)[=:](\d+)` 不含裸 `ne:`，无法匹配 `check connection to ne:31 fail!` 中的 `ne:31` | link_check/link_error 的 NE 字段为空。需额外匹配 `to ne:(\d+)` |
| 格式 C body 前导冒号 | `check connection to ne:31 fail!` 的 body 以 `:` 开头，LOG_HEADER 吃完模块端口后留下 `:check...` | 解析器 body 字段带前导 `:`，显示不美观 |
| `set_target`/`del_target` 二义性 | Kafka 接收 `recv an add target message` 和华为响应 `hw msc ne add target succ` 都被归为 `set_target` | 无法区分"收到设控指令"和"网元已执行设控"两个阶段 |
| `ne_no_response` 无 result | `not receive ne response in 3 seconds` 中无 success/fail 关键字 | result 字段为空，只能通过 ERROR 级别判断为异常 |

### ZTLIG1 解析器验证方法论

修改 `x_interface_decoder.py` 的 ZTLIG1 解析逻辑后，必须用真实生产日志验证（仅靠单元测试不足）：

```python
# 1) 确保导入无报错
from x_interface_decoder import parse_log_line, parse_log_file, generate_summary

# 2) 3种日志格式的 13 个测试用例覆盖
# 格式A: [时间][LEVEL][ztlig1:300][INFORM][ztlig-1_hwne][func]:body → sub_module从body首[...]提取
# 格式B: [时间][LEVEL][ztlig1:300][ztlig-1_hwne][func]:body          → sub_module用LOG_HEADER第5组
# 格式C: [时间][LEVEL][ztlig1:300]:body                                → 无sub_module
# 关键测试: process_init/set_target/del_target/link_check/link_error/
#           ne_no_response/kafka_add/kafka_del/links/location_report/
#           etsi_liid_check/redis_sync/db_query/list_target_rsp

# 3) 大文件5MB前段解析验证
with open("/path/to/ztlig1.300.txt","rb") as f:
    c = f.read(5*1024*1024).decode("utf-8",errors="replace")
parsed = parse_log_file(c)
# 预期: 总行>25000, 命令识别>20000, LIID提取>100, 子模块覆盖率>95%
# 常见故障: 命令识别<200（ZTLIG1_CMD_RE缺失）、LIID=0（LIID格式不兼容）

# 4) API 端到端验证
curl -X POST http://127.0.0.1:5000/x-interface-analyze \
  -H "Content-Type: application/json" \
  -d '{"content":"5MB日志base64或文本","subtype":"ztlig1","interface":"x1","filename":"ztlig1.300.txt"}'
# 检查返回的 stats.liids 数量、parsed[].command 分布
```

注意：`link_check` 和 `ne_no_response` 在 5MB 前段日志中占比很高（数千条），`set_target`/`del_target` 约 100~300 条集中在运行阶段。如果解析结果中只有启动命令（process_init, failed to get license）没有运行命令，说明 ZTLIG1_CMD_RE 缺失了运行阶段的正则。

### ZTLIG1 X1 操作命令分类

| 命令标签 | 匹配模式 | 说明 |
|---------|---------|------|
| `process_init` | `recv start init req\|add succeeded\|failed to get license\|starting\|startup` | 进程启动初始化 |
| `set_target` | `add[\s_]*[Tt]arget\|set[\s_]*[Tt]arget` | 华为设控请求/响应 + Kafka 设控消息 |
| `del_target` | `del[\s_]*[Tt]arget\|delete[\s_]*[Tt]arget` | 华为停控请求/响应 + Kafka 停控消息 |
| `kafka_add_target` | `recv an add target msg` | Kafka 设控消息(精准匹配，不含message后缀) |
| `kafka_del_target` | `recv an del target msg` | Kafka 停控消息 |
| `x1_send_cmd` | `get msgType\[\d+\] success` | X1 命令发送 |
| `hi1_queue` | `put to hi1_que OK\|put to x1_que OK` | HI1/X1 队列入队 |
| `list_target_rsp` | `hua wei msc list target` | 华为列出目标响应 |
| `query_target` | `[Ll]ist[Tt]arget\|subscriber[Ss]tat` | 目标查询/用户状态 |
| `link_check` | `check connection to ne` | 网元连接检查 |
| `link_error` | `the link to ne:\d+ error` | 网元链路错误 |
| `ne_no_response` | `not receive ne response` | 网元无响应 |
| `location_report` | `recv an realtime location\|Lig1SendLocationInfo` | 位置上报 |
| `etsi_liid_check` | `lig1_etsi_check_liid` | ETSI LIID 合法性检查 |
| `db_query` | `ztlig_db_query_record\|ztlig_query_single_record` | 数据库查询 |
| `redis_sync` | `redis_syn_db_handle` | Redis 目标数据同步 |

### ZTLIG1 关键信息提取

| 字段 | 正则 | body 示例 |
|------|------|-----------|
| LIID | `liid(?:\[|=)(\d+)\]?` | `liid=10066` 或 `liid[10066]` |
| NEID | `(?:tneID\|tneid\|ne_id\|neid)[=:](\d+)` | `tneid=1` 或 `ne:31` |
| VNEID | `(?:vneID\|vneid)[=:](\d+)` | `vneid=6` |
| 账号 | `"account":"([^"]+)"` | `"account":"249123694629"` |
| 结果 | `(?:success\|succ\|R_OK)` / `(?:fail\|error\|abnormal)` | `succ` / `fail` |
| 原因 | `(?:reason\|cause)[:=]\s*([^,\]]+)` | `reason:failed to get license` |

### X1 设控全流程日志 trace

```
Kafka 消息接收:
  [ztlig-1_web][WebProcKafkaHi1msgSingle]:recv an add target message,lea=1,vne=8,sessionID=3

Web 模块队列入队:
  [ztlig-1_web][lig1_webadd_handle]:put to hi1_que OK.rsp=...

ETSI LIID 合法性检查:
  [ztlig-1_etsi][lig1_etsi_check_liid_TtTi]:liid+tt+ti is the same

华为网元设控发送:
  [ztlig-1_web][lig1_webhi1_send_th]:get msgType[1] success, sessionId[0] leaId[1] virneID[8] ...

华为网元设控响应:
  [ztlig-1_hwne][hwmsc_x1_addTargetRsp]:hw msc ne add target succ,tneid=1,liid=10066

DB 通知:
  [ztlig-1][lig1_notify_del2db]:notify db to del target success! liid=10066
```

注意：X1 日志中 LIID 格式为 `liid=XXXXX`（hwne 响应中）或 `liid[]`（空，web 模块发送时可能未携带），与 X2 日志的 `"LIID":"XXXXX"`（JSON 字段）格式不同。X1 解码器的 LIID 正则需同时兼容 `liid[XXX]` 和 `liid=XXX` 两种格式。

### 页面结构与标题规范

当前版本采用双页面布局：

| 页面 | 路由 | 功能 |
|------|------|------|
| HI2 解码 | `/` | PCAP 上传 + IRI 文本上传 + 解码模式 + 过滤条件 |
| X 接口日志 | `/x-interface` | SSF/RVF/ZTLIG1/ZTLIG2 四种日志分析 |
| 导航 | 顶部标签 | `📡HI2解码`(当前) / `🔬X接口日志`(链接) |

标题规范：`ETSI ASN.1 Assistant` 为主标题，`<span>` 内为功能名称（不含版本号）。版本号仅在右上角 badge 和页脚显示。

**V4.0.1 移除项：**
- 主页面解码模式：移除 x3（已移至 X 接口日志 RVF）和 hi1（已移至 X 接口日志 ZTLIG1），从 12 种减为 10 种
- 接口类型选择：移除 Auto 自动识别，必须手工选择 X1/X2/X3

### 四类日志综合分析报告（V4.0.1 新增）

ETSI-ASN1-Assistant 对全部四种日志类型生成综合分析报告，后端统一通过 `generate_report(subtype, parsed_lines)` 分发：

| 日志 | 报告函数 | 报告标题 | 独有指标 |
|------|---------|---------|---------|
| ZTLIG1 | `generate_ztlig1_report()` | ZTLIG1 X1 管理面综合分析报告 | 子模块/14种命令/设控停控/网元故障/8类样本 |
| ZTLIG2 | `generate_ztlig2_report()` | ZTLIG2 X2 信令面分析报告 | EventDetail/LigCdr数/呼叫方向/主被叫Top10/NetworkType/Vendor |
| SSF | `generate_ssf_report()` | SSF SIP 信令分析报告 | SIP方法分布(含占比)/CallID数 |
| RVF | `generate_rvf_report()` | RVF RTP 媒体面分析报告 | CorrelationID/RTP会话数/媒体类型 |

前端 `buildReportHTML(report)` 根据报告中的字段自适应展示：ZTLIG1 显示独有章节（子模块/设控停控/网元故障），其他类型按各自指标显示对应 badges 和表格。SIP方法表自动计算每行占总行数的百分比。

报告下方新增 **🔍 关键发现** 自动生成区：基于数据分析自动输出观察结论（活跃LIID占比、高401响应率、INVITE呼叫量、SSF心跳失败检测、ERROR总数）。

统计栏新增：**分析耗时**(analysis_time)、**⚠️大文件** 标签。

### 每日分析结论（V4.0.1）

所有报告类型新增 `daily_analysis` 字段（自然语言描述），按天总结行数/ERROR/LIID/设控/网元故障等指标：

- **ZTLIG1**: `_ztlig1_daily_analysis()` — 每日行数、ERROR、LIID、设控/停控次数、网元故障及Top故障NE
- **通用(SSF/ZTLIG2/RVF)**: `_generic_daily_analysis()` — 每日行数、ERROR、LIID数

示例输出：`2025-12-22: 共4699行；6个ERROR；3个LIID活跃；设控10次；停控1次；网元故障: 连接检查失败925次, 链路错误231次, 网元无响应126次 (主要: NE=3(14), NE=29(14), NE=30(14))`

前端「📅 每日统计」默认折叠，>1天数据时显示分析结论行（date+summary），下方保留数字表格。

### ZTLIG2 LigCdr 全字段解析（V4.0.1）

ZTLIG2 日志解析从嵌入的 LigCdr JSON 中提取以下新增字段，用于生成报告：

| 字段 | LigCdr JSON 键 | 用途 |
|------|---------------|------|
| `calling_num` | CallingNum | 主叫号码 TopN |
| `called_num` | CalledNum | 被叫号码 TopN |
| `msisdn` | MSISDN | 用户号码 |
| `network_type` | NetworkType | 网络类型分布(11=CS/13=IMS) |
| `vendor` | Vendor | 厂商分布 |
| `event_direction` | EventDirection | 呼叫方向(1=发起/2=终结) |
| `report_type` | ReportType | 报告类型 |
| `vneid` | VneID | 虚拟网元ID |

报告新增章节：「🔀 呼叫方向分布」「📞 主叫 Top 10」「📞 被叫 Top 10」。左栏摘要按 EventDetail 分组（而非按命令），显示 LIID/主叫/被叫号码。

ZTLIG2 报告生成器 `generate_ztlig2_report()` 的 `formatParsed()` 和 `buildParsedSummary()` 已适配新字段。

输出报告功能：分析完成后统计栏右侧显示「📥 输出 Markdown 报告」按钮（V4.0.1 已移除 HTML 导出，仅保留 Markdown）。Markdown 为纯文本表格格式可直接存入知识库或 Obsidian。

### 前端加载状态与进度反馈（V4.0.1）

选择文件并点击分析后，加载流程如下：

```
按钮: ▶ 分析 → ⏳ 分析中... → 📤 上传分析中... → ▶ 分析(恢复)
                        ↓
页面: 文件读取进度步骤(⏳ → ✅)
  step0: 📂 文件读取中... (大文件显示10MB/total)
  step1: 📤 上传分析中...
  step2: 🔄 后端全量处理中 (大文件显示行数预估)
  step3: 📊 生成报告...
```

按钮在处理期间被 `disabled=true` 防止重复提交。

### 前端大文件处理（10MB 截断）

浏览器读取大文件（>23MB）时使用 `FileReader.readAsText()` 而非 `Blob.text()` API，因为后者在某些浏览器版本中兼容性不佳（曾导致点击按钮无反应）。

```javascript
// 大文件: 读取前 10MB (足够全面分析)
var blob = file.size > 10 * 1024 * 1024 ? file.slice(0, 10 * 1024 * 1024) : file;
const reader = new FileReader();
reader.onload = function(e) { ... };
reader.onerror = function() { alert('文件读取失败'); };
reader.readAsText(blob, 'utf-8');
```

注意：后端无 5MB 截断，全量处理收到的内容。后端根据 `len(content) > 5MB` 设置 `is_large` 标志，决定返回数据量。

### 前端页面加载失败排查

X-interface 页面按钮点击无反应时，按以下顺序排查：

**1. JavaScript 语法错误（最常见的根因）**
检查 `x_interface.html` 中 `<script>` 块的花括号/圆括号是否平衡。一个多余的 `}` 会导致整个 JS 脚本不执行：

```bash
python3 -c "
import re
f=open('x_interface.html').read()
s=re.findall(r'<script[^>]*>(.*?)</script>',f,re.DOTALL)[0]
print(f'{{}}: {s.count(\"{\")}/{s.count(\"}\")}')
print(f'(): {s.count(\"(\")}/{s.count(\")\")}')
"
```

**2. DOM 元素不存在**
`showLoading()` 中调用 `el.querySelector('.card').innerHTML` 但 `#emptyState` 无 `.card` 子元素 → TypeError。修复：改用 `el.innerHTML`。

**3. API 不兼容的 JS API**
- `Blob.text()` 在某些浏览器中不支持（导致 Promise reject）→ 改回 `FileReader.readAsText()`
- `analyzeComplete()` 函数未定义但被 `.catch` 回调引用 → 移除引用

**4. 浏览器缓存**
页面更新后用户浏览器加载的是旧版本 JS。要求 Ctrl+F5 强制刷新。

### ETSI-ASN1-Assistant 常见部署陷阱

| 陷阱 | 现象 | 原因 | 排查 | 修复 |
|------|------|------|------|------|
| **旧进程仍在运行** | 上传测试不通过，修改的代码不生效。curl 返回 HTTP 200 但解析结果仍为旧版本（命令仅 43 条、LIID=0） | 旧 `app_linux_v4.py` 进程仍绑定 5000 端口。新进程因 `Address already in use` 启动失败，静默退出。curl 实际访问的是旧服务 | `lsof -i :5000` 查看 PID，与此前 `ps aux \| grep app_linux_v4` 的结果对照 | `kill <PID>` 杀死旧进程，重新启动新服务。验证：curl API 的 stats 中 `liids` 数量 >100 即新代码生效 |
| **bg process venv 失效** | `background=true` 启动的服务 import 报错 | bg 进程未激活 venv，PATH 不包含 venv/bin | 检查 process log | 用绝对路径 `/path/to/venv/bin/python3 app.py`，设置 `workdir` |
| **port 5000 残留** | 新服务无法启动 | 旧进程未杀干净 | `lsof -i :5000` | `kill <PID>` |

### 大文件处理 (V4.0.1 已实现)

生产日志可达数 GB（如 ztlig1.300.txt 521MB/473万行）。V4.0.1 移除 5MB 截断，改为报告驱动模式（设计文档 8.3 节已实现，非仅规划）：

```
大文件上传 → 后端全量处理(无size限制)
  → 返回: 综合分析报告 + 摘要 + 前1000行原始日志预览
  → 前端: 显示报告 + 左栏摘要(按命令分组) + 右栏预览
  → 完整数据: 通过「输出 Markdown 报告」按钮获取
```

后端 `app_linux_v4.py` 中 `/x-interface-analyze` 端点根据 `len(content) > 5MB` 设置 `is_large` 标志：
- `is_large=True`: 返回 parsed[:5000]（用于摘要）+ raw[:1000]（预览）
- `is_large=False`: 返回 parsed[:10000] + raw[:5000]（向后兼容）

前端 `x_interface.html` 移除 `file.slice(0, 5MB)` 和大文件确认弹窗。大文件时右栏显示 ⚠️ 提示信息。完整解析结果通过「输出 Markdown 报告」按钮获取（无独立 `/x-interface-download` 路由，设计文档中该路由未实现）。

参考: `docs/ETSI_ASN1_Assistant_V4_系统设计文档.md#83-大文件处理方案-v41-规划`

### 验证脚本

`scripts/verify-ztlig1-parser.py` — 可重复运行的 ZTLIG1 解析验证工具：
- 13 个单行测试用例覆盖 A/B/C 三种格式 + 全部 14 种命令
- 可选大文件 5MB 实测验证（传日志路径作为参数）
- 阈值检查：命令识别 >20000、LIID >100、子模块覆盖率 >95%
- 用法: `python3 scripts/verify-ztlig1-parser.py [日志路径]`
- `--unit-only` 仅运行单行测试

## 十四、参考资料

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
- `references/ztlig-mavenir-analysis.md` — Mavenir IMS LI 分析 SOP（XML/SOAP PCAP 解码、Call-ID 对照、RVF 轮询检测、API 符合性检查）
- `references/ztlig-log-analysis-workflow.md` — ZTLIG2 日志全量分析工作流（LIID/MSISDN 扫描→提取→深度分析→报告输出）
- `references/ztlig1-x1-log-parsing.md` — ZTLIG1 X1 日志解析参考：三种日志格式、14种命令类型、LIID双格式提取、子模块表、工具配置
