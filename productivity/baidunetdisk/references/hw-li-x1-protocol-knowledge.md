# 合法监听 X1/X2/X3 协议知识库（华为/中兴/爱立信）

来源: 百度网盘 parsed/LI-HW.md (华为 CS ETSI X接口规范 V5.03, 259页)
     + parsed/HW_NGN_X1X2.md (华为 NGN X1X2 接口协议 v1.43)
     + parsed/NGN_XPTU.md (NGN XPTU 接口规范)
     + 用户实际部署经验补充

## 一、X1 报文帧头（CS ETSI 新版，14字节）

| 偏移 | 字节数 | 字段 | 说明 |
|------|--------|------|------|
| 0 | 1 | Synchronization byte | 固定 0xAA |
| 1 | 1 | Protocol suit(bit7-6)=00 + Resv(bit5)=0 + Version(bit4-0)=5 | 0x05 |
| 2 | 1 | NE type | 网元编号 |
| 3 | 1 | Encrypt mode(bit7-6) + Algorithm(bit5-0) | 00不加密/01固定/11会话; 算法:DES/AES |
| 4-5 | 2 | Effective data length | Big-endian |
| 6-7 | 2 | Data length | 不加密=明文长度 |
| 8 | 1 | LEAID | 0x01-0xFE |
| 9-13 | 5 | Reserved SPARE | 全 0xFF |
| 14~n | 可变 | Data area | 可DES/AES加密 |

## 二、NE type 编码表

| DEC | HEX | 网元 | 域 |
|-----|-----|------|----|
| 1 | 0x01 | MSCserver/MSC | WCDMA/GSM |
| 2 | 0x02 | HLR | WCDMA/GSM |
| 3 | 0x03 | SMSC | WCDMA/GSM |
| 4 | 0x04 | SGSN | WCDMA/GSM |
| 5 | 0x05 | GGSN | WCDMA/GSM |
| 6 | 0x06 | GMLC | WCDMA/GSM |
| 31 | 0x1F | cMSC | CDMA |
| 32 | 0x20 | cHLR | CDMA |
| 33 | 0x21 | cSMC | CDMA |
| 34 | 0x22 | PDSN | CDMA |
| 37 | 0x25 | AAA | CDMA |
| 81 | 0x51 | MSE | WCDMA/GSM |
| 91 | 0x5B | NGN | 固网 |
| 101 | 0x65 | P-CSCF | IMS |
| 102 | 0x66 | I-CSCF | IMS |
| 103 | 0x67 | S-CSCF | IMS |
| 104 | 0x68 | HSS | IMS |
| 105 | 0x69 | CCTF | IMS |
| 106 | 0x6A | MGCF | IMS |
| 111 | 0x6F | IMS | IMS |
| 121 | 0x79 | TAS | IMS |
| 123 | 0x7B | AGCF | IMS |
| 151 | 0x97 | SBC | IMS |

## 三、NGN 版 X1 帧头（8字节）

```c
typedef struct X1Frame {
    BYTE  nPreamble;    // 0xAA
    BYTE  nCmdCode;     // 命令码
    WORD  nLEAID;       // LEA ID
    DWORD dwLength;     // pData长度
    BYTE  pData[];      // 数据区(DES加密)
} X1FRAME, *LPX1FRAME;
```

命令码: 0x10=CONNECT, 0x18=RSP, 0x20=SETOBJECT, 0x28=RSP, 0x30=DELOBJECT,
0x38=RSP, 0x40=MODIOBJECT, 0x48=RSP, 0x50=QUERYOBJECT, 0x58=RSP,
0x60=LISTOBJECT, 0x68=RSP, 0xA0=STARTLEA, 0xA8=RSP, 0xB0=CLOSELEA,
0xB8=RSP, 0xC0=EXITLEA, 0xC8=RSP, 0xF0=X1SHAKEHAND

NGN版pData加密: 尾部补4字节reserve, 再补到8的整数倍, 然后DES加密。密钥由XPTU分配。

## 四、CS vs IMS X1 差异

X1层完全一致。差异在X2和X3:
- X2: CS有12种IRI事件(call-establishment/answer/release/...)；
  IMS仅1种iMS-Gen-IRI-Report(含完整SIP消息)
- X3: CS用ISUP/PRA复制媒体；IMS用RTP复制媒体
- IMS必须设SpeechOutputMode=SplitedOptionA

## 五、X2-X3 关联

核心关联标识: LIID + CIN [+ CCLID]

Option A (标准): LIID + CIN 关联，每个通话独立2条CC链路
Option B (复用): LIID + CIN + CCLID，整进程只建2条CC链路
Option C (节省): LIID + CIN，只报上行CC链路

X3通道中关联参数填充位置:
- Calling Number = NEID
- Calling Party Subaddress = LIID + Direction
- Called Party Subaddress = CIN + CCLID
- 字段分隔符 = 0xF

Direction: 0=合路, 1=来自目标, 2=发往目标

## 六、HEX 码流示例

X1帧头: AA 05 01 00 00 24 00 24 01 FF FF FF FF FF [数据]

NEID=19861365551: X1=ASCII 31 39 38... ; X2=逆序BCD 91 68 31 56 55 F1
NEID=192.168.1.100: X1=ASCII 31 39 32 2E... ; X2=4字节 C0 A8 01 64

## 七、ASN.1 (LI-HW.md 第12章)

ROOT: X1.X1Message-ETSI, PROTOCOL: X1, ENDIAN: BIG, PERALIGN: ALIGN
X1 DEFINITIONS IMPLICIT TAGS ::= BEGIN
X1MessageType ::= CHOICE { x1Connect[0], x1ConnectResponse[1], x1SetTarget[2], ... x1ListLeaResponse[29] }

## 八、三家厂商 X1 实现对比

| 维度 | 华为 | 中兴 | 爱立信 |
|------|------|------|--------|
| 传输协议 | TCP私有二进制 | CORBA/SNMP → IIF内部模块 | HTTP + SOAP/XML |
| X1本质 | LIG↔NE独立二进制通道 | IIF接收外部指令，NE内部执行 | ADMF↔NE间XML消息交换 |
| 数据编码 | C结构体 / ASN.1 PER | NE内部自有格式 | XML文档(WSDL定义) |
| 加密 | DES/AES(帧头指定) | IPSec/TLS | HTTPS + WS-Security |
| 命令方式 | nCmdCode字节(0x10~0xF0) | MML命令/Telnet/CORBA RPC | SOAP方法调用 |
| 5G演进 | 沿用私有TCP | 部分转向REST/HTTP | 融入5GC SBA(HTTP/2) |

华为: 帧头0xAA+14字节+DES加密，私有协议自由度高
中兴: NE内置IIF模块，外部通过CORBA/SNMP/MML发指令控制拦截激活
爱立信: XML文档封装SOAP消息走HTTP，遵循3GPP SBA方向
