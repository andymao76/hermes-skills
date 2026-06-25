# Ericsson MSS17A X1/X2/X3 完整操作 SOP 索引

> 完整 24KB SOP 文档位于系统知识库：
> `/home/andymao/knowledge/li/Ericsson/Ericsson_MSS17A_X1_X2_X3_SOP.md`
>
> 本文档为快速索引，详见上述主 SOP。

## 文档来源

`/home/andymao/knowledge/li/Ericsson/MSS17A/` (MSS17A.7z, 48文件/4文件夹)
- `COD (X1)/` — 28 个 X1 接口命令说明书
- `POD (X2)/` — 2 个 X2 输出格式 (RCEOUTM + RCEFILE1)
- `IWD (X3, HI3)/` — 10 个 X3 协议文档

## 架构速览

| 接口 | 功能 | 协议 | 传输 |
|------|------|------|------|
| X1 (HI1) | 设控/解控/配置/查询/审计 | COD (Command Output) | TCP CLI 或 SOAP/HTTPS |
| X2 (HI2) | 拦截数据输出 (IRI/RCEFILE1) | POD (Printout Output) | MSC → LIG / Kafka |
| X3 (HI3) | 内部监控数据协议 | IWD (Internal Work Data) | MSC 内部 |

## 核心设控流程

### MSC 命令行 (COD)

```
RCMUI:MUID=LEA01,CO=1;
RCMCI:MONB=8613800123456,MCNB=861090001234,CO=1,DT=AVF-1,MUID=LEA01;
RCSUI:MUID=LEA01,CO=1;
RCSUP:MUID=LEA01,CO=1;
```

### SOAP API (LIMS V2.3)

```
Login → CreateWarrant(warrantID=-1) → GetWarrantList → Terminate → sleep 3s → Delete
```

### Kafka TMC_TARGET_INFO

添加 (isDel=0) / 删除 (isDel=2)

## 关键文档一览 (按文档编号)

| 文档编号 | 内容 |
|----------|------|
| 1_19082_CNT233171_1 | RCARI 监控区域 Initiate |
| 2_19082_CNT233171_1 | RCARC 监控区域 Change |
| 3_19082_CNT233171_1 | RCARE 监控区域 End |
| 4_19082_CNT233171_1 | RCARP 监控区域 Print |
| 9/10/11/12_19082_CNT233242_1 | RCMUI/E/P/C |
| 13/14_19082_CNT233242_1 | RCMCI/C |
| 22/24/25_19082_CNT233242_1 | RCPWI/C/P |
| 1/2/3/21_19082_CNT233262_1 | RCSUE/I/P/C |
| 17/18/19/20_19082_CNT233262_1 | RCMUI(CA)/RCHMI/E/P |
| 1/2/3_19082_CNT233245_1 | RCSAI/S/E/C/P |
| 1/2/3_19082_CNT233251_2 | RCMRI/E/P |
| 155_19_FAY102067_17Uen.A | X3 监控数据输出协议 v17 |
| 1_102 62_FAY102067_17Uen.A | X3 元素列表协议 v17 |
| 155_19_FAY102123_12Uen.A | X3 监控业务协议 v12 |
| 15519_FAY102150_6Uen-A | X3 RCE 集群内部通信 V32 |
| 2_15519_APR10139_21Uen.A | X3 RES 事件协议 v21 |
