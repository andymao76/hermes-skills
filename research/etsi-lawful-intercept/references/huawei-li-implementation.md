# 华为 LI X 接口实现 — 中文翻译标准文档

> 来源：`/home/andymao/LI/华为LI标准协议翻译.zip`（2025-07/08 编写）
> 知识库入口：`~/knowledge/research/华为LI标准协议翻译.md`

## 文档结构

解压后包含（8个核心 ASN.1 + 2个 docx + 2个 diff HTML）：

| 文件 | 说明 |
| `华为5GC LI协议标准.docx`（~5MB） | 5GC 场景 X1/X1M/X2/X3 接口规范（中文翻译） |
| `华为CS LI协议标准.docx`（~5.8MB） | CS 场景（MSC/HLR/NGN/IMS）X1/X2/X3 接口规范（中文翻译） |
| `asn/hw_5gc_x1.asn`（694行） | 5GC X1 ASN.1—LIG格式（LIGX1模块） |
| `asn/hw_5gc_x2.asn`（1197行） | 5GC X2 ASN.1—HWIriReport格式（含5GS特定参数） |
| `asn/hw_cs_x1.asn`（931行） | CS X1 ASN.1—X1Message-ETSI |
| `asn/hw_cs_x2.asn`（1054行） | CS X2 ASN.1—X2Message-ETSI-CS |
| `asn/hw_cs_ims_x1.asn`（965行） | CS+IMS X1（含StartLEA/CloseLEA/ExitLEA消息） |
| `asn/hw_cs_ims_x2.asn`（1113行） | CS+IMS X2（含IMS特定IRI参数） |
| `asn/hw_sae_x1.asn`（521行） | SAE X1—3G R8 LIG格式 |
| `asn/hw_sae_x2.asn`（513行） | SAE X2—EPS HWIriReport格式 |
| `diff_cs_vs_ims_x1.html` | CS vs CS+IMS X1差异对比 |
| `diff_cs_vs_ims_x2.html` | CS vs CS+IMS X2差异对比 |

**新增（HW目录根层，4个ASN.1文件）：**

| 文件 | 行数 | 场景 | 标准参考 |
|------|------|------|---------|
| `HI2Operations_hw.asn` | 1131 | ETSI HI2标准核心模块（华为修改版） | TS 101 671 / 3GPP TS 33.108, OID hi2 version11 |
| `UmtsCS-HI2Operations_hw.asn` | 260 | UMTS CS域HI2（R16） | 3GPP TS 33.108, OID hi2CS r16 |
| `hw_epc.asn` | 512 | SAE/EPC X1接口（LIG格式, 67种消息类型） | 华为私有（SAE R8） |
| `hw_epc_x2.asn` | 81 | EPC X2接口（EPS IRI上报, GTPV2参数） | 3GPP TS 33.108 EPS HI2 R16 |

**4个新增文件的关键特征：**
- `HI2Operations_hw.asn`：华为修改版（isup-parameter 解码修正，OCTET STRING tag 0x04→0x81），含完整 IRIContent/Begin/End/Continue/Report、IRI-Parameters（tag 0~255）、PartyInformation/Location/通信标识子结构
- `UmtsCS-HI2Operations_hw.asn`：18种CS事件枚举（call-establishment→ims-Gen-IRI-Report）+ Change-Of-Target-Identity（新旧MSISDN/IMSI/IMEI跟踪）
- `hw_epc.asn`：MessageType枚举（67种：Echo→连接→Target CRUD→查询→告警→时间同步）+ 24种Cause值 + TargetId类型（IMSI/MSISDN/MEID/NAI）+ EPSLocationInfo
- `hw_epc_x2.asn`：EPS-GTPV2-SpecificParameters（PDN地址分配/APN/RAT类型/UE本地IP/UDP端口/TWAN标识），编码参照TS 29.274

**这些文件形成 ETSI标准层 → 华为设备层的完整 ASN.1 定义链**：
```
ETSI TS 101 671
  └── HI2Operations_hw.asn (标准IRI定义, v11)
        ├── UmtsCS-HI2Operations_hw.asn (CS域扩展, R16)
        ├── hw_epc_x2.asn (EPS X2特定参数, R16)
        └── hw_epc.asn (EPC X1控制面, 华为私有)
              └── hw_5gc_*.asn (5GC X1/X2, 华为LIG格式)
```

## 关键发现（与标准之差异）

## 关键发现（与标准之差异）

### 5GC X1 接口特点（huawei 5GC LI 协议标准）

- **X1 不是 ETSI TS 103 221 的 XML/SOAP 方式**，而是华为私有 TCP 二进制协议
- 消息头固定 12 字节（非 CS 版的 14 字节），使用 ASN.1 BER 编码
- X1 连接请求携带 NEID（IP地址）+ UserName + PassWord 认证
- ADMF 作为 TCP 客户端主动连接 NE（NE 作为 TCP 服务器）
- **LIOID 机制**：32 位无符号整数，每个 LI Target 唯一标识；同意不同 LEA 对同一用户的不同标识（SUPI vs GPSI）分配不同 LIOID
- **FUNCType**：位掩码标识 NE 内含的功能实体（GGSN/P-GW/S-GW/MME/SGSN），用于集成 NE 场景下的 IRI/CC 上报
- **TNEType**：5GC 六种 NE 类型——UDM/HSS/UNC(AMF+SMF+SMSF+MME+SGSN)/UDG(UPF)/USN(MME+SGSN)/UGW(S-GW+P-GW)
- DF2/DF3 地址由 ADMF 通过 SetDfInterface 消息在 X1 接口下发
- X2/X3 使用 Correlation Number（Charging ID + IP）做 IRI 和 CC 的关联

### CS X1 接口特点（huawei CS LI 协议标准）

- 固定 14 字节消息头，前导同步字节 **0xAA**
- 支持 **DES/AES-128/192/256 加密**，ECB 模式，通过消息头第4字节指定
- 数据区分明文长度和密文长度两个字段
- NE type 第3字节编码：MSC=1, HLR=2, GMLC=10, MSE=11, NGN=12, IMS=111
- 命令通过 nCmdCode 字节标识（0x10~0xF0）
- NEID 在 X1 用 ASCII，在 X2 用逆序 BCD 或二进制 IP

### IMS 布控两种模式

1. **ETSI CS 模式**：按呼叫事件（BEGIN/END/CONTINUE/REPORT）逐条上报
2. **IMS 模式**：通过 `iMS-IRI-Report` 封装完整的 SIP 消息，LIG 自行解析 SIP 信令提取主叫/被叫/SDP

### CS+IMS 与 CS 的差异

- X1：IMS 版新增 StartLEA/CloseLEA/ExitLEA 三个消息（tag 14-15-16）
- X2：IMS 版新增 IMS 特定 IRI 参数
- X3：CS 模式用 ISUP/PRA/SIP-I 复制媒体，IMS 模式用 RTP 复制

## 用法：在 LI 排错场景中引用

当用户提及华为 LI 配置/连接问题时：

1. **检查 X1 连接** → 查看华为 5GC/CS X1 的认证流程（NEID+UserName+PassWord）
2. **检查 X2 IRI 事件** → 查阅 5GC 40+ 种 IRI 事件列表（文档第 2.5 节）
3. **检查 X3 IDP 格式** → 注意 Correlation Number 字段与 Charging ID 的对应关系
4. **CS vs 5GC 差异** → CS 用 0xAA 帧头+DES/AES 加密，5GC 用 ASN.1 BER+TLS
5. **IMS 布控消息盲解析** → 如果收到 iMS-IRI-Report，需要 SIP 协议栈支持（文档 1.3 节）
6. **错误码查表** → 外层 LIG Return Code 和 内层 EPC Cause 见 `references/huawei-li-error-codes.md`
7. **pcap 解码时的两个错误码层**：LIRP 响应中 EPC Cause=128=成功，LIG Return Code=0=成功，不要混淆
