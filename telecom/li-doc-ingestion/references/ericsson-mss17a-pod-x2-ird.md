# Ericsson MSS17A POD (X2) — 快捷参考

文档位置：`~/knowledge/hi2/厂商对接/Ericsson_MSS17A_POD_X2_IRD_ASN1_RCEFILE1.md`
原始文件：`~/knowledge/li/Ericsson/MSS17A/POD (X2)/`

## 两文档概览

| 文档 | Ref | 类型 | 页数 | Printout Block |
|------|-----|------|------|---------------|
| IRD 输出结果 | 1/190 83-CNT 233 251/3 Uen | ASN.1 形式化描述 | 28 | RCEOUTM |
| RCEFILE1 输出 | 1/190 83-CNT 233 256/3Uen | 文件输出字段定义 | 127 | RCEOUTF |

## 关键速查

### EventInformation（25 种事件）

0=originatingCall, 1=terminatingCall, 2=callCompletion, 3=shortMessage, 5=handover, 6=exception, 7=callAnswer, 8=callRedirection, 9=ccOpen, 10=ccClose, 11=ccAssociation, 12=uuService, 13=locationData, 14=servingSystem, 15=cRSS, 16=digitExtraction, 17=networkSignal, 19=uSSD, 20=cISS, 21=ectDisconnect, 22=ooBDTMFReport, 23=mSCLocationUpdate, 24=pRBT, 25=reserved

### CALLID 格式 `xxxxx-yy-zz`

- `xxxxx` = Monitored Call ID (0-65535, 已废弃, 由 EXTENDEDMONCALLID 替代)
- `yy` = Intercept ID - monitored object (H'00-H'99)
- `zz` = Intercept ID - non-monitored object (H'00-H'99)

### NODE 值

0=GMSC, 1=MSC/VLR, 2=Undefined

### TYPE (监控对象类型)

0=MONB, 1=IMEI, 2=IMSI, 3=EBNR, 4=RESERVED, 5=CA

### RCEFILE1 Record Type 速查

| Type | 含义 | 典型大小 |
|------|------|---------|
| 1 | Originating Call | ~1059 |
| 2 | Terminating Call | ~1040 |
| 3 | Call Completion | ~239 |
| 4 | SMS | ~718 |
| 5 | Handover | ~241 |
| 6 | Call Answer | ~302 |
| 7 | Call Redirection | ~978 |
| 8 | Content Channel Open | ~166 |
| 9 | Content Channel Close | ~141 |
| 10 | Call Identity Association | ~391 |
| 11 | UUS | ~1028 |
| 12 | Location Data | ~179 |
| 13 | Serving System Update | ~113 |
| 14 | USSD | ~505 |
| 15 | Dialled Digits | ~199 |
| 16 | CISS | ~1250 |
| 17 | CRSS | ~1624 |
| 18 | Network Signalling | ~685 |
| 19 | ECT Disconnection | ~229 |
| 20 | Out of Band DTMF | ~201 |
| 21 | MSC Location Update | ~247 |
| 22 | PRBT | ~152 |
| 23 | RESERVED | ~1680 |

### 卫星定位字段（大多数记录包含）

LONG (8) = ddd-mm-ss-di, LAT (7) = dd-mm-ss-di, SHAPE (1) 0=矩形/1=圆形, RADIUS (3) 0-255km, ANGLEIND (3) ×1.4=degrees from north, HALF LENGTH (2) 0-31km, HALF WIDTH (1) 0-7km

### CLI 命令

RCSUI=Mobile Subscriber Initiate, RCSUC=Mobile Subscriber Change, RCMCI=Monitoring Centre Initiate, RCHMI=HLR Monitoring Initiate
