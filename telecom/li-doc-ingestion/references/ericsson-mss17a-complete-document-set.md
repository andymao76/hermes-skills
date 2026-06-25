# Ericsson MSS17A 完整文档集快捷参考

来源：`~/knowledge/li/Ericsson/MSS17A/` (MSS17A.7z 解压所得 48 文件/4 文件夹)

## 接口层总览

| 接口 | 目录 | 文件数 | 功能 |
|------|------|--------|------|
| X1 (HI1) | COD (X1) | 28 | 远程控制命令: RCARI/RCMUI/RCMCI/RCSUI/RCSAI/RCHMI 等 |
| X2 (HI2) | POD (X2) | 2 | IRD ASN.1 + RCEFILE1 文件格式 |
| X3 (HI3) | IWD (X3, HI3) | 10 | 监控数据输出协议/RCE集群通信/RES事件协议 |

## 对接经验文档（根目录 5 篇）

- **埃塞爱立信对接相关经验分享** — LIMS 14B→V2.3 升级, X1 端口 65211→8443, cer→jks, Kafka TMC_TARGET_INFO
- **爱立信1口对接调试文档** — WSDL+XSD+properties 构建请求消息
- **爱立信对接问题整理** — license(eric_lis_v2dot1=1), openssl 1.0.0+, session invalid, GGSNMonitoring=0, sleep 3s
- **爱立信CURL对接整理** — Login→Add/Delete, sessionID 5min 生命周期, warrantID=-1
- **爱立信-HI1结构一览及其构造-详细** — createWarrant 字段详解 (warrantItem/DtlWarrantNeTypeItem/supplementaryInfo/targetTypeID)

## COD (X1) 关键命令

- **RCMCI** — 监控中心初始化: MONB/IMEI/IMSI/EBNR/CA 标识, MCNB, DT(VCE-1/DFA-2), CO
- **RCMUI** — 监控用户初始化: MUID, CO, CUG+NI
- **RCARI** — 监控区域初始化: MA(1-7字母数字)
- **RCSUI** — 移动用户设控 Initiate
- **RCSAI** — 手动审计和同步
- **RCPWI/RCPWC/RCPWP** — 密码管理

## POD (X2) 关键格式

详见主笔记 → `hi2/厂商对接/Ericsson_MSS17A_POD_X2_IRD_ASN1_RCEFILE1.md`

## IWD (X3, HI3) 协议文档

- FAY102067 v16/v17 — 监控数据输出协议
- FAY102123 v12 — 监控业务协议
- FAY102150 v6 — RCE集群内部通信协议 V32
- APR10139 v21 — RES 事件协议
