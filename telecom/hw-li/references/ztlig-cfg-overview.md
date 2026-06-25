# ZTLIG ztlig.cfg 配置概览

## 章节结构（~150项）
1. **NE-COM** (18+23项): 物理网元 + HW/ZTE/NSN/ERIC/UTIMACO/G2K/ZEEL 特有
2. **VNE-COM** (10+9项): 虚拟网元 + ZTE/ERIC 特有
3. **LEA** (22项): 监听中心(Kafka/Redis/SFTP/码流分享)
4. **ZTLIG1** (6项): 设控进程
5. **ZTLIG2** (12项): 信令处理(tneid/networkType/超时/operid)
6. **ZTLIG3** (13项): EPC转接(SICMS DPDK)
7. **SSF** (10项): SIP-I会话(interfaceType 5种模式)
8. **RVF** (12项): RTP语音还原(clientnum/sdpport/ssfSeq)
9. **LICENSE** (17项): 各厂商接口开关
10. **GLOBAL** (5项): FTP/多TMC/Kafka监控

### 关键速查
- `networkType`: 1-CS, 2-PS, 3-EPC, 4-IMS, 5-5GC, 11~18=细粒度CS/PS+2G~5G
- `syn_night` bit位: bit0=hw, bit1=zte, bit2=eric, bit3=nsn, bit4=utimaco
- `speechtype`: 0=合并, 1=分离, 5=ZTE V4LIS特有分割
- 配置属性: C(必配), M(重要), O(可选)
- ztlig_target 字段速查: `references/ztlig-target-fields.md`
- 3口TLV: IMSI=Type1(8B BCD), MSISDN=Type2(8B BCD), IMEI=Type3(8B BCD)
- ISUP信令: IAM→ACM→ANM→REL→RLC
