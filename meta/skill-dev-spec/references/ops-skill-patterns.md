# 运维 Skill 开发模式参考

> domain: devops, bigdata, li
> 适用: Grafana+Prometheus / OWLS LI / 大数据HDP / ZTLIG网关

## 一、运维 Skill 分类与命名

| 类型 | 命名模板 | 示例 |
|:----|:---------|:-----|
| 系统运维 | {系统名}-ops | hbase-ops, ztlig-ops |
| 专家排障 | {系统名}-expert | ambari-expert, hdfs-expert |
| SRE | {系统名}-sre | greenplum-sre, flink-sre-expert |
| 专项工具 | {工具名}-ops | docker-storage-ops |

YAML Frontmatter 模板:
```yaml
---
name: system-ops
description: >
  Use when operating, monitoring, or troubleshooting {系统名称}.
  Covers: health check, configuration, log analysis, incident
  response, and performance optimization.
  Triggers: {关键词1}, {关键词2}, {关键词3}.
metadata:
  version: "1.0.0"
  category: devops|bigdata|li
  related_skills:
    - ambari-expert
    - hdfs-expert
---
```

## 二、正文结构模板（运维通用）

```
## Overview
  系统概述 + 架构图 + 数据流

## Quick Reference
  命令速查表（用途 | 命令 | 预期输出）

## Health Check
  逐项巡检（服务 | 检查方法 | 正常阈值 | 异常处理）

## Diagnosis Workflow
  按根因分类（HDFS/YARN/Hive 或 ztlig1/ztlig2/ssf/rvf）
  每类: 症状 → 检查命令 → 日志 grep → 修复命令 → 验证

## Common Commands
  分类命令集（状态查看 / 配置管理 / 日志分析 / 性能调优）
  命令必须是完整可复制的（含路径、参数、示例）

## Troubleshooting Table
  根因 | 症状 | 检查方法 | 修复命令 | 验证方法

## Verification
  操作成功确认: curl + grep + status check

## References
  配置文件路径、日志路径、知识库交叉引用
```

## 三、Grafana + Prometheus 监控栈

### 架构
```
ops-monitor/
├── docker-compose.yml
├── prometheus/
│   └── prometheus.yml          # scrape_configs + alerting rules
└── grafana/
    └── provisioning/
        ├── datasources/        # auto-register Prometheus DS
        └── dashboards/         # auto-import dashboard JSONs
```

### 端口规范
| Exporter | 端口 |
|----------|------|
| node_exporter | 9100 |
| cAdvisor | 8080 |
| 自定义 exporter | 9800 |

### 常见坑
- Grafana 容器 uid=472，provisioning 文件需 644 权限
- DNS 解析: Grafana 需解析 prometheus 主机名
- scrape_timeout 默认10s，复杂检查设30s
- 看板设计: 用 Stat 彩色方块 / Gauge 二值状态，中文标签

### Prometheus scrape 配置模板
```yaml
scrape_configs:
  - job_name: 'custom_exporter'
    scrape_interval: 30s
    scrape_timeout: 30s
    static_configs:
      - targets: ['host:9800']
```

### 告警规则模板
```yaml
groups:
  - name: {system}.rules
    rules:
      - alert: {AlertName}
        expr: rate(xxx_total[5m]) > threshold
        for: 2m
        labels:
          severity: critical|warning|info
        annotations:
          summary: "{{ $labels.instance }} 异常"
```

## 四、OWLS LI 平台

### 数据流
```
后端/Kafka → ztlig1 (X1设控) → NE网元
                              ├→ ztlig2 (X2信令面) → Kafka/后端
                              └→ ssf → rvf → 语音文件
```

### API 模板
- 接口: POST /targetManagement/queryActiveTargetInfo
- 参数: {"account": "LEA账号"}
- 响应: code=200, data=[{account, type, protocol, ...}]
- SKILL 必须包含: 请求/响应示例 + 字段说明 + 常见错误码 + curl 模板

### 配置管理
- ztlig.cfg: ssf.{id}.interfaceType (1=SIP-I, 2=TS-102232, 3=Mavenir)
- Kafka: ztlig.lea.{id}.kafka_realtime_*
- VNEID 映射: SU(63407) / ZAIN(63401) / MTN(63402)

### 设控排查四步法
1. 查 Kafka 消费: kafka-consumer-groups --describe
2. 查 ztlig1 响应: grep "success\[200\]" / grep "fail\[" 
3. 查 NE 同步: curl http://NE-IP:480/status
4. 查 ztlig2 解码: grep "EncodeToJson" | grep "{LIID}"

## 五、大数据 HDP 平台

### 组件全景
HDFS(存储) / YARN(调度) / Hive(数仓) / HBase(列存) / Kafka(消息)
Greenplum(MPP) / Spark(计算) / Flink(流计算) / ES(搜索) / ZooKeeper(协调)

### 巡检 Skill 结构
每个组件格式:
```markdown
### 服务名
- 状态检查: {命令}
- 关键指标: {指标1} / {指标2}
- 阈值标准: Used% < 85%, Memory < 90%, Region < 50000
```

### 排障 Skill 结构
```markdown
## {组件名} 排障
| 症状 | 根因 | 检查命令 | 修复命令 |
|------|------|---------|---------|
| HDFS SafeMode | NN启动/磁盘满 | hdfs dfsadmin -safemode get | hdfs dfsadmin -safemode leave |
```

每个命令必须包含: 完整命令 + 正常输出 + 异常输出 + 路径变体

## 六、通用质量规则

| 规则 | 说明 |
|:----|:-----|
| 命令可复制 | 每条命令带预期输出，可直接粘贴运行 |
| 标注输出 | 什么是正常/异常，不只说"检查服务" |
| 风险警示 | ⚠️ 危险操作前加警告 |
| 每步验证 | 操作后跟 curl/grep/status 确认 |
| 变量化路径 | ${HADOOP_HOME} 代替硬编码路径 |
| 依赖声明 | Requires: jq, python3, sudo |
| 日志解读 | 每个 grep 后说明: 查什么、正常输出、异常含义 |
| 涉密隔离 | 用 ${VAR} 引用，实际值放 references/ 或知识库 |

### 反模式
- ❌ 只写命令不写输出 — 每个命令后必须有预期输出说明
- ❌ 跳过验证步骤 — 每步操作后跟验证命令
- ❌ 危险操作无警告 — 重启/删数据/改权限前加 ⚠️
- ❌ 硬编码涉密 — 用变量替代 IP/端口/配置
- ❌ 命令不可直接复制 — 检查路径、参数、环境变量完整性
