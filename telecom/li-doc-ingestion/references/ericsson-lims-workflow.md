# 爱立信 LI-IMS 集成 — ZTLIG 工作流快捷参考

完整文档: `li/Ericsson/LIMS_Workflow_and_Maintenance.md`
目标管理数据流: `li/Ericsson/ZTLIG_TargetManagement_Flow.md` (由 `ztlig-workflow.png` 经 Qwen3-VL 识别)

## 总体架构：ZTLIG + Ericsson LI-IMS

```
Web UI → Kafka → ztlig1 → Ericsson LI-IMS (SOAP/HTTPS, 8443)
   ↑         ↓        ↓
   |     ztlig2 ← Ericsson X2 (IRI报告)
   |     SSF/RVF ← Ericsson X3 (通话内容)
   ↓         ↓        ↓
Kafka(TMC_REALTIME + TMC_OFFLINE)
   ↓
Flink(Realtime + Afterwards) → Web展示
```

## HI1 目标管理数据流（补充视图）

```                   Kafka 消息总线
               ┌─────────────────────────────┐
               │ TMC_TARGET_INFO_lis (请求)   │
               │ TARGET_INFO_STATUS_lis (响应)│
               └──┬──────────────┬───────────┘
     WEB → Kafka ─┤              ├─ Kafka → WEB
      ↓           │              │      ↓
    RediStore──ZTLIG──LI Server    GreenPlum
    (缓存)        (核心)    (网元)     (持久化)
```

详见 `ZTLIG_TargetManagement_Flow.md`

## 三大进程

| 进程 | 日志 | 功能 |
|------|------|------|
| ztlig1 (300) | `/home/admin/LISTENER_V1.0/ztlig1.300.txt` | HI1: Kafka设控→爱立信LI-IMS→回Kafka |
| ztlig2 (460) | `/home/admin/LISTENER_V1.0/ztlig2.460.txt` | HI2: 接收并解析爱立信IRI报告 |
| SSF (1300) | `/home/admin/LISTENER_V1.0/ssf.1300.txt` | SIP/ISUP信令分析 |
| RVF (1400) | `/home/admin/LISTENER_V1.0/rvf.1400.txt` | RTP媒体解码分析 |

## 厂商对应

| 运营商 | debug命令 | 系统 |
|--------|----------|------|
| **MTN (主)** | `debug ztlig1 300 ericlis24 on` | **爱立信 LI-IMS** |
| Airtel | `debug ztlig1 300 zeel on` | Zeel LIG |
| Glo | `debug ztlig1 300 utimaco on` | Utimaco LIMS |

## 调试命令

```bash
ztsh  # 登录 ZTLIG shell
debug ztlig1 300 ericlis24 on   # 启用爱立信HI1调试
write ztlig1 300 logfile on     # 启用日志文件
capture ztlig2 460 msg on 100 100  # 抓取HI2 IRI报文
```

## 关键日志模式

| 日志 | 含义 |
|------|------|
| `recv kafkamsg (...) isDel:0` | Web发来设控指令 |
| `eric_lis_add` | 发往爱立信LI-IMS |
| `ne response success. liid[XX]` | 爱立信返回成功 |
| `encode_kafka_rsp msg ret:0` | 结果写回Kafka(成功) |
| `encode_kafka_rsp msg ret:1` | 结果写回Kafka(失败) |
