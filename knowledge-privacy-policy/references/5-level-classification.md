# 五级数据分类参考

源自 `knowledge/_system/security/LLM-Data-Governance_Privacy_Protection`，与物理目录 `knowledge/{public,internal,customers,li,secrets}/` 一一对应。

## 速查表

| 级别 | 名称 | 物理目录 | RAG策略 | 风险 |
|------|------|---------|---------|------|
| LEVEL 1 | 公开知识 | `public/`, `telecom/`, `bigdata/` | ✅ 允许检索 | 🟢 低 |
| LEVEL 2 | 内部经验 | `internal/` | ⚠️ 脱敏后检索 | 🟡 中 |
| LEVEL 3 | 企业机密 | `customers/` | ❌ 禁止检索 | 🔴 高 |
| LEVEL 4 | 敏感数据 | `secrets/` | ❌ 绝对禁止 | 🔥 致命 |
| LEVEL 5 | LI数据 | `li/` | ❌ 绝对禁止 | 🔴 绝密 |

## 全部 5 级详细说明

### LEVEL 1 — 公开知识
允许发送到：DeepSeek、Qwen、Claude、GPT、Gemini、OpenRouter、SiliconFlow

包括：
- 2G/3G/LTE/5GC/IMS 架构
- VoLTE/VoNR 流程
- Diameter/SIP/MAP/CAP 协议
- HDFS/Kafka/Flink/Spark/Hive/ES
- Ubuntu/CentOS/OpenWrt/Docker/K8s
- Hermes/MCP/Skill/RAG/Agent Framework

### LEVEL 2 — 内部经验
脱敏样例：
- ❌ "客户A网络发生故障" → ✅ "Customer_A网络发生故障"
- ❌ "苏丹NISS项目" → ✅ "Project_A"
- ❌ "南京中新赛克" → ✅ "Vendor_A"

### LEVEL 3 — 企业机密
包括：商业合同、商务报价、招投标文档、产品源代码、内部架构图、财务数据、客户名单
处理方式：仅本地存储。

### LEVEL 4 — 敏感数据
包括：password/token/apikey/secret、AWS/Azure/Google Key、.env/config.yaml、DB Password、SSH Private Key、WireGuard/OpenVPN Key
处理方式：绝对不进入知识库。

### LEVEL 5 — LI数据
包括：HI1/HI2/HI3、IMSI/IMEI/MSISDN、LIID/CC Data/IRI Data、Call Trace/CDR/Location Data、手机号/身份证/邮箱
处理方式：必须脱敏（如 `8613812345678` → `86138xxxx678`）。

## Hermes 执行策略

默认策略：`PUBLIC_ONLY`
当发现 IMSI/MSISDN/LIID/PASSWORD：自动切换 `LOCAL_ONLY`，不调用外部模型。

## 最终原则

- 公开知识：允许发送
- 经验知识：脱敏后发送
- 客户知识：默认禁止
- 密码数据：绝对禁止
- LI数据：绝对禁止
- 遵循：Need To Know / Least Exposure / Zero Trust
