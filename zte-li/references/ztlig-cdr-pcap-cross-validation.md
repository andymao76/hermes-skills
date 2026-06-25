# PCAP ↔ ZTLIG CDR 交叉验证方法

## 背景

当需要验证 ZTLIG 是否完整解码了 X2 接口的 IRI 报告时，可以在 LIG 侧抓 PCAP，用离线 ASN.1 解码工具解码后，与 ZTLIG Kafka JSON CDR 输出做对比。

## 验证流程

### 1. LIG 侧抓包

```bash
# 在 LIG 上对 X2 端口抓包
tcpdump -i any port {x2_port} -w x2_ir_capture.pcap
# 或指定网卡
tcpdump -i eth0 port 8890 -w x2_hw_ims.pcap
```

### 2. PCAP 离线解码

使用 ETSI-ASN1-Assistant V3 或 ber-tag-analyzer：

```bash
# 通过 Web UI 上传
# http://127.0.0.1:5000
# 选择对应厂商模式解码：
#   hw-ims   → 华为 IMS (VoLTE/VoWiFi)
#   hw-cs    → 华为 CS
#   zte-cs   → 中兴 CS
#   hw-5gc   → 华为 5GC
#   etc.
```

注意：ETSI-ASN1-Assistant 的 ASN.1 规范文件在 `src/asnfile/` 下，需确保 `current_path` 指向 `src/` 而非项目根目录（否则规范加载失败）。

### 3. ZTLIG 日志提取

```bash
# 按 IMS ChargingID 过滤
cat ztlig2*.* | grep -a "psdpcscf02.191" > cid-target.txt

# 按 MSISDN 过滤
cat ztlig2*.* | grep -a "120120415" | grep "2026-06-23" > target-20260623.txt

# 按 LIID 过滤（注意使用 -a 避免 Binary file 警告）
cat ztlig2*.* | grep -a "LIID\":\"18041" > liid-18041.txt

# 提取所有 Kafka JSON CDR
cat ztlig2*.* | grep -a "ZtligKafkaProduceMsgByKey" > all_cdr.txt
```

### 4. 对比分析

关注 PCAP 中 SIP 消息存在的字段在 ZTLIG CDR 中是否完整：

| 字段 | PCAP 中位置 | ZTLIG CDR 是否包含 |
|------|------------|-------------------|
| LIID | HI2 IRI record | ✅ |
| IMS ChargingID | imsChargingID / P-Charging-Vector | ✅ (CidNum) |
| MSISDN | partyInformation | ✅ |
| Calling/Called Num | partyInformation / SIP From/To | ✅ |
| Call Duration | ImsGenIRIReport | ✅ (BYE 时) |
| **utran-cell-id-3gpp** | **P-Access-Network-Info** | **⚠️ 有时缺失** |
| **Wlan-ue-local-ip** | **P-Access-Network-Info (IEEE-802.11)** | **❌ 始终缺失** |
| **UE IP/Port** | **P-Access-Network-Info** | **❌ 始终缺失** |
| **SBC 域名** | **P-Access-Network-Info** | **❌ 始终缺失** |

### 5. 字段值对比示例

PCAP 解码得到的 SIP PANI：
```
P-Access-Network-Info:
  IEEE-802.11;
  sbc-domain=psdpcscf02.ims.mnc007.mcc634.3gppnetwork.org;
  ue-ip=10.201.24.98;
  ue-port=5060;
  Wlan-ue-local-ip=196.202.142.135;   ← 公网 IP
  Wlan-ue-local-port=16567
```

ZTLIG 对应 CDR（仅含 LocationType+Location）：
```json
{
  "LIID": "18041",
  "LocationType": 4,
  "Location": "6340700210E52"
}
```

Location 编码格式 = MCC(3) + MNC(2/3) + CELL_ID_HEX(余下)
如 `6340700210E52` → MCC=634, MNC=07, Cell=00210E52

## 已知缺失

ZTLIG 的 HW IMS 解码模块未从 PANI 提取以下字段到 Kafka CDR：
- Wlan-ue-local-ip（WiFi 侧公网 IP）
- Wlan-ue-local-port
- sbc-domain（SBC/P-CSCF 域名）
- ue-ip / ue-port（IMS 核心网私网地址）

这些字段存在于原始 SIP 消息中，但被 ztlig2 的 JSON 编码器丢弃。

## 案例：A1 项目 ZAIN Sudan VoWiFi 验证

### 数据源
- **PCAP**: `~/PCAP/20260623-A1-VOWIFI/`
  - `a8b0f01b.pcap` (34k 包, 18:08:36~18:08:48)
  - `c8381c8b.pcap` (52k 包, 18:04:33~18:04:51)
- **ZTLIG 日志**: `ztlig2.467.txt` (及 460~466)
- **目标号码**: +249120120415 (masked: +249****0415)

### 对比结果

| 项目 | PCAP 解码 | ZTLIG CDR |
|------|----------|-----------|
| LIID | 18041 (PCAP1+2) | 18041 (465/466 TargetAdd) |
| CidNum | psdpcscf02.191.36d4... | 467 中有 3 条设控记录 |
| MSISDN | +249****0415 | 249120120415 |
| CallingNum | +249****0415 | 249120120415 |
| CalledNum | 0123123638 | 0123123638 |
| Wlan-ue-local-ip | **196.202.142.135** | **缺失** |
| 小区 ID | 6340700210E52 | 6340700210E52 (Location) |
| UE IP | 10.201.24.98:5060 | 缺失 |
| 接入类型 | IEEE-802.11 | 仅 LocationType=4 |

### 设控时间线（ztlig2.465 + 466）

```
12:03:10  TargetAdd  LIID=18041  VNE=6/17  → 布控成功
12:11:10  TargetDel  LIID=18041             → 删除
13:17:16  TargetAdd  LIID=18044             → 再次布控
13:19:09  TargetDel  LIID=18044             → 删除
```

PCAP 中 IMS CDR 对应的实际通话在 18:04~18:08 (UTC+2)，与布控时间差约 6 小时，这是由于抓包时间与 ZTLIG 日志使用不同时区（UTC vs UTC+2）。
