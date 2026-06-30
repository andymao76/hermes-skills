# Telecom 目录安全拆分记录

## 背景

`knowledge/telecom/` 原本混合了 LEVEL 1 公开通信技术和 LEVEL 5 LI 数据，需要按安全规则拆分。

## 拆分操作（2026-06-17）

### 迁移的 LEVEL 5 内容（→ `knowledge/li/`）

| 源路径 | 目标路径 | 文件数 |
|--------|---------|--------|
| `telecom/lawful_interception/` | `li/lawful_interception/` | 30 份 |
| `telecom/a1-project/` | `li/a1-project/` | 8 份 |
| `telecom/international_project/` | `li/international_project/` | 55 份 |
| `telecom/OWLS Operation Manual.md` | `li/` | 1 份 |
| `telecom/ZTLIG目标同步逻辑.md` | `li/` | 1 份 |

### 保留的 LEVEL 1 内容（telecom/）

- `2G_3G呼叫流程与排障指南.md`、`3GPP_TS_24.008.md`、`5G传输网…`
- `Diameter完整消息库速查手册.md`、`GTP_PFCP完整消息库速查手册.md`
- `IMS_SIP信令流程与排障指南.md`、`ims-volte-technical-guide.md`
- `free5gc-5g-core.md`、`关于5G标准中文版的说明（必看）.md`
- `中兴交换机/`、`core_network/`、`fusionsphere/`
- `ima-articles/`（118 文件）、`ima-qa/`（6 文件）
- `me60/`、`mssoftx3000/`、`sip/`、`sip_rtp/`、`wireshark/`
- `README.md`

### 更新的 README

- `knowledge/telecom/README.md` — 标注 LEVEL 1 安全等级，列出已迁移内容
- `knowledge/li/README.md` — 新增子目录结构表、关联技能，引用 RULE③/RULE⑨

## 语义索引重建

```bash
cd ~/knowledge && kb-index
# 输出：Entity changes: + 华为, - 00_inbox, - worklog, - 编程规范, 27 unchanged
```

## 审计脚本适配

`security-audit.py` 的 `scan_sensitive_in_dir()` 已配置：
- LEVEL 1 目录列表包含 `telecom`、`public` 等 15+ 个目录
- 协议标准文件（3GPP_TS/Diameter/GTP_PFCP/2G_3G等）跳过 IMSI/MSISDN 扫描
- 误报过滤：media_id、UUID、测试号码、掩码号码
