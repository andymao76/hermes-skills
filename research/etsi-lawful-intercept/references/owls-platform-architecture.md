# OWLS 系统 — LJ 平台架构与业务流程

## 来源
17 个 xmind 文件 + 1 个 md 文件，位于 `/home/andymao/OWLS/`
XMind 解析方式: `.xmind` 是 ZIP 包，内含 `content.json` (XMind 2020+) 或 `content.xml` (XMind 8)
知识库: `~/knowledge/research/OWLS_系统架构与业务流程.md`

## 系统概要

OWLS 是一个合法监听(LJ)数据平台，对接三大数据源：
- **A 口（电围/MSIS）**: ZTASig/STCMS → OWLS内部设控，CS域数据
- **LIG（合法监听）**: ZTLIG → TMC(OWLS)，ZTLIG前端设控
- **MIMC（移动互联网）**: DFX/SICMS → OWLS内部+前端设控

## 核心模块

### TMC (合法监听中心)
- 前端: ZTLIG（Sinovatio 中新赛克 LIG），接收CS域HI2报告
- 设控方式: 2/3/4G Target，ZTLIG前端执行
- HI2字段: LIID/NeidType/NetworkType/ReportType/EventDetail/IMSI/MSISDN/IMEI等
- 4G Target生成规则: MSISDN + MSISDN@域名 + IMSI@域名
- PS域关联: HI2(关联号+三码) → Redis → HI3(IP+关联号) → 补全三码 → 入库

### CSPETL 通用处理（22步）
1. 字段校验 → 2. 协议过滤 → 3. 字段映射 → 4. 默认值 → 5. Telegram特殊处理
   → 6. IMSI/IMEI长度 → 7. 去国家码 → 8. IP补号(关闭) → ... → 14. 白名单 → 18. VOIP字段处理

### OTT通联（VOIP关联方案）
- 通用: SSRC_CTOS==SSRC_STOC，10秒窗口
- Telegram: CRC碰撞，N%可配
- 权重公式: weightThreshold = min(29, 3*min) + Math.min(max, 20)

### SICMS2.0 sourceno协议号体系
DST_017031(HTTP), 017033(EMAIL), 017037(VOIP), 017008(SNS),
017045(VPN), 017097(IPDR), 017096(RADIUS), 017051(DNS) 等
