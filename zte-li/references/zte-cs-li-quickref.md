# ZTE CS LI 三接口命令速查

见 `knowledge/hi2/厂商对接/ZTE_CS_LI_HI1_HI2_HI3_三接口规范.md`

## HI1 — CLI 命令 (Telnet/SSH)

### 目标管理
```
ADD LITGT: MCID=1: LIID=1: TT=5: TI=460030927640001: IT=3: FD=0: NENo=1:
  TT: 2=MSISDN前缀, 3=IMEI, 5=IMSI, 6=MSISDN, 8=SIP-URI, 20=ECGI
  IT: 1=IRI only, 2=CC only, 3=All
  SPEECHTYPE: 0=CombinedA, 1=SeparateC, 2=SeparateA, 3=SeparateB, 4=SeparateD, 5=CombinedB
DEL LITGT: MCID=1: LIID=1:
MOD LITGT: MCID=1: LIID=1: IT=3: HI3A=4510008:
SHW LITGT: MCID=1:LIID=1:
SHW TGTINF: TT=5:TI=460030912345678:
DLB LITGT: MCID=1: DELMODE=0:  (0=过期, 1=ALL)
SET BARRING:MCID=1:LIID=use1:BARRING=1:
CON CC:MCID=1:NENo=20:CIN=00121234:SPEECHTYPE=4:LIID=20130000250:HI3A=911:
```

### 操作员管理
```
ADD OP: OP=use1: PWD=12345678: CFM=12345678: CG=261: MCID=1: NENo=54:
  CG: 260=NE超级, 261=LEA管理, 262=LEA操作
DEL OP: OP=use1:
MOD OPPWD: OP=use1: OLD=12345678: NEW=111111: CFM=111111:
MOD OPCG: OP=use1: CG=262:
SHW OP: [MCID=1:] [NENo=54:]
```

### IP/日志
```
ADD HI1IP: IP=10.45.105.220:
DEL HI1IP: IP=10.45.105.220:
SHW HI1IP: [NENo=1:] [MCID=1:]
SHW HI1LOG: OP=user1:CNO=6505:
SHW HI1LOG TAB:
DEL HI1LOG:logn=ETSICOMMANDLOG20120926121832:
SHW VERSION:
```

## HI2 — IRI 事件类型

| 值 | 事件 | 记录类型 | 特有字段 |
|----|------|---------|---------|
| 1 | call-establishment | Begin/Continue | PartyInfo |
| 2 | answer | Continue | ringingDuration |
| 3 | supplementary-Service | Continue | — |
| 4 | handover | Continue | locationOfTheTarget |
| 5 | release | End/Continue | release-Reason(Q.850) |
| 6 | sMS | Report | SMS-report(最长270B) |
| 7 | location-update | Report | locationOfTheTarget |
| 8 | subscriber-Controlled-Input | Report | DTMF键(Keypad facility) |
| 9 | switchOffEvent | Report | — |
| 10 | cCLinkStateReportEvent | Report | callContentLinkInformation |
| 11 | switchOnEvent | Report(中兴扩展) | — |

## HI3 — CC 参数

IAM消息: Called=HI3Addr, Calling=NEID
Called Sub: {OperatorID, CIN, CCLID}
Calling Sub: {LIID, Direction, ServiceOctets}
