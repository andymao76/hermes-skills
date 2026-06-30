# VoWiFi WLAN-ue-local-ip 数据模型缺口分析

## 背景

A1 项目 ZAIN 网络中，VoWiFi 呼叫的 PCAP 分析确认 `P-Access-Network-Info` SIP 头域包含 `Wlan-ue-local-ip=196.202.142.135`，但 OWLS (Deep Insight) 后台 CDR 界面不显示该 IP。

## 协议分层

```
抓包层 (tcpdump/PCAP)
  └─ IP 层: 10.171.103.92 → 10.55.2.11 (华为 SBC 内部网络)
       └─ SIP 载荷 (UDP/TCP 5060/9900)
            └─ P-Access-Network-Info: IEEE-802.11;
                 "sbc-domain=atbpcscf01.ims.mnc007.mcc634.3gppnetwork.org";
                 "ue-ip=10.201.212.200";"ue-port=5060";
                 "Wlan-ue-local-ip=196.202.142.135";"Wlan-ue-local-port=21238"
                 ↑ 这是 HI2 X2 IRI 报告级别的数据

ZTLIG2 → Kafka 层
  └─ LigCdr JSON (23 字段):
       {"LIID":"18041","CidNum":"atbpcscf01.192.1439.20260629125657",
        "MSISDN":"249120120415","CallingNum":"249120120415",
        "CalledNum":"0123123638","NetworkType":13,...}
       ↑ 没有 WlanUeLocalIp 字段
```

## 关键数据点 (2026-06-30 PCAP 分析)

| 参数 | 值 |
|------|-----|
| PCAP 文件 | `88776738-7cb4-422a-8ded-5d7b9139bc09.pcap` |
| WLAN IP 出现次数 | 9 次 (P-Access-Network-Info 中) |
| UE 内部 IP:Port | `10.201.212.200:5060` |
| WLAN 本地 IP:Port | `196.202.142.135:21238` |
| P-CSCF 域名 | `atbpcscf01.ims.mnc007.mcc634.3gppnetwork.org` |
| 站点 | ATB (Atbara, B站) |
| 运营商 | ZAIN Sudan (MCC=634, MNC=007) |
| 终端类型 | iPhone (User-Agent: iOS/26.5 iPhone) |
| CidNum (IMS Charging ID) | `atbpcscf01.192.1439.20260629125657` |
| MSISDN (Deep Insight) | `120120415` (= `249120120415` 去掉国家码) |

### Wireshark 截图帧 7345

第一张截图（`微信图片_2026-06-30_085936_606.jpg`）显示：
- 帧 7345 选中状态
- 源 IP: `10.171.103.92` (华为设备 `HuaweiTechno_71:7b:dd`)
- 目的 IP: `10.55.2.11` (超聚变设备)
- 协议: RTP (G.711 PCMA 语音流)
- hex dump 底部明文: `Wlan-ue-local-ip=196.202.142.135`

### Deep Insight 截图

第二张截图（`微信图片_2026-06-30_085948_100.jpg`）显示：
- 系统: Deep Insight (OWLS Web UI)
- URL: `215.152.1.11:8890/listener/#/targetQueryResult`
- CID NO: `atbpcscf01.192.1439.20260629125657`
- Target Number: `120120415`
- 运营商: Sudatel (苏丹电信)
- **无 WLAN IP 字段显示**

## 历史案例 (2026-06-23 对比)

| 对比项 | 2026-06-23 | 2026-06-30 |
|--------|:-----------:|:-----------:|
| PCAP | a8b0f01b.pcap + c8381c8b.pcap | 88776738-...pcap |
| WLAN IP | `196.202.142.135:16567` | `196.202.142.135:21238` |
| UE IP | `10.201.24.98:5060` | `10.201.212.200:5060` |
| LIID | 18041 | (Deep Insight 显示 MSISDN=120120415) |
| 终端 | iPhone iOS/26.5 | iPhone iOS/26.5 |
| P-CSCF | psdpcscf02 (PSD站) | atbpcscf01 (ATB站) |
| 运营商 | ZAIN (634/007) | ZAIN (634/007) |
| 接入类型 | IEEE-802.11 (VoWiFi) | IEEE-802.11 (VoWiFi) |
| WLAN IP 在 OWLS | 不显示 | 不显示 |

**关键结论:** 同一 WLAN IP（同一部 iPhone）在不同站点、不同日期的 PCAP 中均被确认，但 OWLS 始终不显示，说明不是偶发故障，而是 LigCdr 数据模型的**系统级缺口**。

## 相关分析工具和命令

```bash
# 从 PCAP 提取 WLAN IP
strings <pcap> | grep -o 'Wlan-ue-local-ip=[^";]*' | sort -u

# 从 PCAP 提取 P-Access-Network-Info 头域
strings <pcap> | grep "IEEE-802.11" | head -10

# 从 PCAP 提取 IMS Charging ID (CidNum)
strings <pcap> | grep -oP 'icid-value="[^"]*"' | sort -u

# 查找 P-Charging-Vector 完整内容
strings <pcap> | grep "P-Charging-Vector" | sort -u

# 查看呼叫 Call-ID
strings <pcap> | grep -i "Call-ID:" | sort -u

# 从 PCAP 提取所有 SIP From/To 号码
strings <pcap> | grep -E "From:|To:|P-Asserted-Identity:" | sort -u

# 终端类型
strings <pcap> | grep "User-Agent:" | sort -u

# 查看 PCAP 基本信息
capinfos <pcap>
```

## 源文件

- PCAP: `/home/andymao/PCAP/20260630-A1-VOWIFI/88776738-7cb4-422a-8ded-5d7b9139bc09.pcap`
- 截图1 (Wireshark): `/home/andymao/PCAP/20260630-A1-VOWIFI/微信图片_2026-06-30_085936_606.jpg`
- 截图2 (Deep Insight): `/home/andymao/PCAP/20260630-A1-VOWIFI/微信图片_2026-06-30_085948_100.jpg`
- 2026-06-23 报告: `/home/andymao/PCAP/20260623-A1-VOWIFI/A1_VoWiFi_HI2_Decode_Report.docx`
- 2026-06-23 V4 报告: `/home/andymao/PCAP/20260623-A1-VOWIFI/A1_VoWiFi_HI2_Decode_Report_V4.docx`
