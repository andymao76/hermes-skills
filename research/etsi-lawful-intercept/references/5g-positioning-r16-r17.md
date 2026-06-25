# 5G 定位技术要求（R16/R17）

知识库: `~/knowledge/research/5G_定位技术_R16_R17.md`

## R16 定位精度要求（TR 38.855）

| 指标 | 监管用 | 商业用 |
|------|--------|--------|
| 水平精度(80%UE) | < 50m | < 3m(室内) / < 10m(室外) |
| 垂直精度(80%UE) | < 5m | < 3m |
| 端到端延迟 | < 30s | < 1s |

## R17 目标（TR 38.857）
- 亚米级（厘米级）精度
- 面向工业物联网场景
- 与TSN/URLLC并列

## 6 种定位方案
1. **DL-TDOA**: 下行到达时间差（类似4G OTDOA），UE测量PRS的RSTD
2. **UL-TDOA**: 上行到达时间差，gNB测量SRS的UL RTOA
3. **DL-AoD**: 下行离开角度，UE测量波束RSRP
4. **UL-AoA**: 上行到达角度，gNB测量到达角
5. **Multi-RTT**: 多站往返时间，≥3站，Rx-Tx时间差
6. **E-CID**: 增强小区ID，单站RTT+角度

## UE上报测量量
- 每波束/gNB的DL RSRP
- 下行参考信号时间差(DL RSTD)
- UE RX-TX时间差

## gNB上报测量量
- 上行到达角(UL-AoA)、UL-RSRP
- UL-RTOA、gNB RX-TX时间差
