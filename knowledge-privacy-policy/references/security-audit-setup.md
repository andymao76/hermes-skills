# 自动化安全审计系统

## 架构概览

```
llm_data_governance.skill.md  ← 规则层：分级体系、敏感词模式、审计策略
         │
security-audit.py             ← 执行层：Python 脚本，每日 08:30 自动运行
         │
audit-reports/security-audit-YYYY-MM-DD.md  ← 报告层：Markdown 报告，保留最近 30 份
```

## 组件位置

| 组件 | 路径 |
|------|------|
| 治理规则文件 | `knowledge/_system/security/llm_data_governance.skill.md` |
| 审计脚本 | `~/.hermes/scripts/security-audit.py` |
| Cron 任务 | `Hermes Knowledge Security Audit` (每日 08:30, no-agent 模式, job_id: `5aed4747594c`) |
| 报告输出 | `knowledge/_system/security/audit-reports/security-audit-YYYY-MM-DD.md` |
| 保留策略 | 最近 30 份，自动裁剪 |

## 审计脚本工作流程

### 1. 目录隔离检查
扫描 LEVEL 1 目录（telecom/, public/ 等），检查是否混入了 LEVEL 5 子目录名：
- `lawful_interception`, `a1-project`, `international_project`, `ZTLIG`, `OWLS`, `SICMS`, `SECPASS`

### 2. 扫描范围
审计脚本扫描以下 LEVEL 1 目录（已审计过滤后视为 LEVEL 1）：
```
public, telecom, bigdata, linux, hermes,
ai, flink, kafka, hadoop, hbase, greenplum,
wireshark, ima-articles, ima-qa,
baidu-netdisk, articles_baidu        # 百度网盘导入内容需过滤后使用
```

### 3. 敏感词扫描模式
```python
SENSITIVE_PATTERNS = {
    "IMSI_DATA":     r'IMSI\s*[=:]\s*["\']?\d{14,16}',
    "MSISDN_DATA":   r'MSISDN\s*[=:]\s*["\']?\d{10,15}',
    "LIID_VALUE":    r'LIID\s*[=:]\s*\S+',
    "PASSWORD_LINE": r'(?:password|passwd|pwd)\s*[=:]\s+(?!(?:v\d[a-z0-9]{2,4}|提取码))[^\s]{6,}',
    "TOKEN_LINE":    r'(?:token|api_key|apikey|secret)\s*[=:]\s*\S{8,}',
    "PRIVATE_KEY":   r'-----BEGIN.*PRIVATE KEY-----',
    "PHONE_11":      r'(?<!\d)1[3-9]\d{9}(?!\d)',
    "IMSI_RAW":      r'(?<!\d)\d{15}(?!\d)',
}
```

### 4. 误报过滤机制（6 层）

| 过滤层 | 触发条件 | 跳过类型 | 说明 |
|--------|---------|----------|------|
| 协议标准文件豁免 | 文件名含 `3GPP_TS`, `TS_24`, `TS_23`, `Diameter`, `GTP_PFCP`, `2G_3G呼叫流程` 等 | IMSI_DATA, MSISDN_DATA, PHONE_11, IMSI_RAW | 3GPP/ETSI 标准中 IMSI/MSISDN 是字段名 |
| 协议章节上下文 | 上下文含 `subclause`, `procedure`, `detach`, `attach` 等 | IMSI_DATA, MSISDN_DATA | 非标准文件中的协议引用 |
| media_id 过滤 | 上下文 200 字符内含 `media_id`/`uuid` | PHONE_11 | 文件 ID 中的 hex 数字 |
| 掩码号码过滤 | 上下文含 `****` 或 `xxx` | PHONE_11 | 已脱敏的示例号码 |
| 测试数据过滤 | 15 位数字以 `46000`/`46001`/`46002` 开头且含 `1234567890` | IMSI_RAW | 公开文章中的测试 IMSI |
| Markdown 图像尺寸 | 上下文含 `width=`/`height=`/`in}` | IMSI_RAW | `{width="4.811835083114611in"}` 格式 |

### 5. 迁移建议
| 敏感词类型 | 建议迁移目标 |
|-----------|-------------|
| IMSI_DATA, MSISDN_DATA, LIID_VALUE, IMSI_RAW | → `li/` |
| PASSWORD_LINE, TOKEN_LINE, PRIVATE_KEY | → `secrets/` |
| PHONE_11（真阳性） | → `li/` 或 `customers/` |

### 6. RAG 索引风险评估
检查 Qdrant 集合，确认 customers/li/secrets 路径未被意外索引（curl -s http://localhost:6333/collections/knowledge | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'向量数: {d[\"result\"][\"vectors_count\"]}')")。

### 7. 过期报告清理
```bash
find ~/knowledge/_system/security/audit-reports/ \
  -type f -name "security-audit-*.md" | sort | head -n -30 | xargs -r rm
```

## 手动触发

```bash
# 本地执行
python3 ~/.hermes/scripts/security-audit.py

# 远程执行（腾讯云）
ssh tencent 'python3 ~/.hermes/scripts/security-audit.py'
```

退出码：
- `exit 0` — 安全状态良好
- `exit 1` — 发现安全问题（隔离违规或敏感词命中）

## 扩展指南

### 新增敏感词模式
编辑 `~/.hermes/scripts/security-audit.py` 中 `SENSITIVE_PATTERNS` 字典。

### 新增协议文件豁免
编辑 `SAFE_PROTOCOL_FILES` 列表，添加文件名关键字。

### 新增审计目录
编辑 `LEVEL1_DIRS` 列表，添加新目录名。

### 调整保留策略
编辑 `MAX_REPORTS` 变量（默认 30）。

## 关联规则

RULE10 — 调用外部 LLM 前遵守 `knowledge/_system/security/llm_data_governance.skill.md`。每日 08:30 自动执行安全审计。

RULE11 — 百度网盘下载的文档需经安全审计分类：LI/项目文档 → `li/`，客户数据 → `customers/`，密码密钥 → `secrets/`。分类完成前不得用于 RAG 检索。
