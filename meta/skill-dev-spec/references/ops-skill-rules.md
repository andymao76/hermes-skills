# 运维 Skill 编写规范

参考: agentskills.io + Hermes 运维实践 + 现网经验
配套: 上级 Skill `skill-dev-spec`

---

## 目录结构与命名规则

```
skill-name/
├── SKILL.md              # 必需
├── scripts/              # 可选：可执行脚本（SQL/Shell/Python）
├── references/           # 可选：配置模板/参数速查表
└── assets/               # 可选：拓扑图/架构图

命名:
  系统类:   {组件}-ops       如 hbase-ops, docker-storage-ops
  SRE类:    {组件}-sre       如 flink-sre-expert, greenplum-sre
  排障类:   {组件}-troubleshooting
  禁止:    fix-X-today, debug-Y-now 等 session 命名
```

## YAML Frontmatter 模板（运维版）

```yaml
---
name: system-ops
description: >
  Use when monitoring, diagnosing, or maintaining {系统}. Covers health
  checks, log analysis, performance tuning, configuration, and incident
  response. Keywords: {系统名}, {关键词}, {关键词}.
metadata:
  version: "1.0.0"
  category: devops|bigdata|li
---
```

## 正文结构模板

```
## Overview              架构图 + 数据流
## Quick Reference       命令速查表（用途|命令|预期输出）
## Health Check          逐项巡检（服务|检查方法|阈值|异常处理）
## Diagnosis Workflow    按根因分类排障步骤
## Common Commands       分类命令集（状态/配置/日志/调优）
## Troubleshooting Table 根因|症状|检查|修复|验证
## Verification          操作后验证方法
```

## 质量要求（Helm 自文档化风格）

每条命令 / 每个步骤包含:
- **what**: 这条命令在做什么
- **why**: 为什么这样做
- **output**: 预期输出是什么（正常 vs 异常）
- **check**: 如何验证结果

### 危险操作规范
- 重启 / 删配置 / 改权限前加 `⚠️` 警示
- 每步操作后必须跟验证命令
- 低自由度任务（备份/迁移/重启）用严格顺序

### 日志分析规范
- 每个 `grep` 给出: 查什么 + 正常输出 + 异常代表什么
- 排障步骤要求采集日志证据（journalctl / grep / dmesg）

### 路径与依赖规范
- 用变量代替硬编码: `${HADOOP_HOME}` 而非 `/usr/hdp/current/`
- 显式声明依赖: `Requires: jq, python3, sudo`
- 涉密信息用 `${VAR}` 变量引用，实际值放 references/ 或知识库

## 四类系统的 Skill 侧重点

### Grafana + Prometheus 监控
- Docker 部署结构 + scrape 配置模板
- 自定义 exporter 端口 9800
- Grafana provisioning YAML 模板
- 常用 PromQL 按中文标签分组
- Troubleshooting: 无数据 / timeout / 权限

### OWLS LI 平台
- API 模板: 请求/响应示例 + 字段说明
- 数据流: Kafka → ztlig1 → NE → ztlig2 → Kafka / ssf → rvf
- ETL 三码补全检查步骤
- ztlig.cfg VNEID 映射速查

### 大数据 HDP
- 组件全景: HDFS/YARN/Hive/HBase/Kafka/Greenplum
- 每组件排障表: 症状|根因|检查命令|修复命令
- Ambari 管理: Blueprint / Restart 顺序 / Alert 调整

### ZTLIG 网关
- 进程: ztlig1/2/3 + ssf + rvf
- 设控排查四步: Kafka → ztlig1 log → NE同步 → ztlig2解码
- 日志 grep 模板: LIID / Call-ID / Correlation ID / 错误
