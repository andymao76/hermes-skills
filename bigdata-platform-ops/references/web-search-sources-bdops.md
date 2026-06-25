# 大数据平台运维技能 — 网络搜索来源

本章节记录了 `bigdata-platform-ops` 第 18 章「生产环境核心经验」中网络搜索补充内容的来源。用于后续追溯验证或深入阅读。

---

## 来源一：腾讯云大规模Hadoop集群管理

- **URL**: https://cloud.tencent.com/developer/article/2567289
- **标题**: 大规模Hadoop集群管理：运维经验与监控策略
- **作者**: Jimaks
- **日期**: 2025-09-12
- **提取到第 18 章的内容**:
  - 故障三态模型（瞬时/间歇/持久）与分级响应
  - 三七法则（70% 自愈 / 30% 人工）
  - 参数调优黄金法则（spark maxExecutors ≤ 节点数×3, MR 内存 1:1.5, NM 预留 20%）
  - 四维调优法（计算/存储/网络/OS）
  - 扩容三段论（预测→预检→预热）与三大门槛
  - 监控四层立体化（L1-L4）
  - LSTM 磁盘预测、知识图谱根因定位、混沌工程

## 来源二：Running Flink in Production — Streamkap Production Guide

- **URL**: https://streamkap.com/resources-and-guides/flink-production-guide
- **标题**: Running Flink in Production: The Operations Guide
- **来源**: Streamkap Engineering
- **日期**: 2026-02-25
- **提取到的内容**（补充到 flink-sre-expert）:
  - Flink TaskManager 五大内存池详解
  - Barrier 机制（Chandy-Lamport 分布式快照）
  - Checkpoint vs Savepoint 六维对比表
  - Consumer Lag + Checkpoint Duration 作为#1监控指标
  - Prometheus Reporter 配置

## 来源三：Hadoop Monitoring — OpenLogic

- **URL**: https://www.openlogic.com/blog/hadoop-monitoring-tools-observability
- **标题**: Hadoop Monitoring: Tools, Metrics, and Observability
- **作者**: Rajesh Krishnamurthy
- **日期**: 2024-12-05
- **状态**: 内容与现有技能有重叠（HDFS/YARN/ZK监控指标已在各组件技能中覆盖），未提取新内容

## 来源四：阿里云 HDFS 运维白皮书

- **URL**: https://developer.aliyun.com/article/719483
- **标题**: hadoop日常运维白皮书
- **状态**: 内容与 hdfs-expert 已覆盖（Safe Mode/HA/FSImage/磁盘均衡），未提取新内容

## 来源五：Flink Checkpoint Troubleshooting (AWS)

- **URL**: https://repost.aws/knowledge-center/msaf-checkpoint-fail
- **状态**: 厂商定制版内容，未提取

## 已跳过来源（不相关）

| 来源 | 原因 |
|------|------|
| 2026 AIOps厂商选型指南 (canway.net) | 厂商营销，非可执行技能 |
| 2026 数字化转型现状 (TEKsystems) | 管理咨询报告 |
| 华为 Agentic AI 白皮书 | 厂商趋势，非实操 |
| 美团技术博客 | AI 模型相关，非运维 |
| 2026 国际AI安全报告 | 无关 |
| awesome-ops GitHub 列表 | 项目目录，非技能 |
| Hadoop 安装教程 (厦大数据库) | 入门级，非高级运维 |
