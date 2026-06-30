# LI 平台 Prometheus + Grafana 自动巡检方案

> 完整设计文档: `/home/andymao/projects/ops-monitor/li-platform-monitoring-design.md`
> Exporter 实现: `/home/andymao/projects/ops-monitor/li_exporter/`

## 架构

Gateway Exporter 模式 — 不在 LI 平台部署任何进程。Hermes 端的 `li_exporter`（端口 9801）通过 SSH 远程执行 ZTLIG CLI 命令和 OWLS 健康检查，统一暴露为 Prometheus `/metrics` 端点。

## 远程服务器清单

| 角色 | 主机名 | 网段 |
|------|--------|------|
| ZTLIG 前台 | LIG01 ~ LIG07 | 站点A 215.152.1.x / 站点B 192.172.16.x |
| OWLS 后台 | rhino01 ~ rhino09 | 同 |

关键端口: OWLS Web 8890, Secpass 8080, Kafka Manager 9000

## 指标速查

### ZTLIG

| Prometheus 指标 | CLI 命令 | 说明 |
|-----------|---------|------|
| `ztlig_process_up{process=ztlig1}` | `ps aux | grep -c '[z]tlig1'` | 进程存活 |
| `ztlig_process_count{process=ztlig1}` | 同上 | 进程实例数 |
| `ztlig_process_up{process=ssf}` | `ps aux | grep -c '[s]sf'` | SSF 存活 |
| `ztlig_process_up{process=rvf}` | `ps aux | grep -c '[r]vf'` | RVF 存活 |
| `ztlig_kafka_produced_total` | `show ztlig2 {id} kafka stat` | 按 topic 累加 |
| `ztlig_kafka_error_total` | 同上 | 错误计数 |
| `ztlig_x2_decoded_ok_total` | `show ztlig2 {id} x2 stat` | 解码成功 |
| `ztlig_x2_decode_error_total` | 同上 | 解码失败 |
| `ztlig_nic_dropped_total` | `show ztlig3 {id} nic stat` | 网卡丢包 |

### OWLS

| Prometheus 指标 | 采集方式 | 说明 |
|-----------|---------|------|
| `owls_web_up{code=200}` | `curl -so /dev/null -w "%{http_code}" :8890/` | Web 可达 |
| `owls_web_response_ms` | `curl -o /dev/null -w "%{time_total}" :8890/` | 响应延迟 |
| `owls_gp_up` | `psql -h localhost -d bigdata -c "SELECT 1" -U daedb` | GP 连通 |
| `owls_hdfs_used_percent` | `hdfs dfsadmin -report \| grep 'DFS Used%'` | HDFS 使用率 |
| `owls_hdfs_missing_blocks` | `hdfs fsck / -list-corruptfileblocks \| wc -l` | 缺失块 |
| `owls_flink_job_running` | `yarn application -list \| grep -c flink` | Flink 作业数 |

## Grafana 仪表盘 (provisioning JSON)

三张仪表盘定义见设计文档 §五:
- `ztlig-overview.json` — 进程健康 + Kafka/X2 管道 + 网元分布 + 错误监控
- `owls-overview.json` — 基础设施健康 + 资源趋势 + 模块进程表
- `li-platform-overview.json` — 全平台联合视图

## 告警规则 (prometheus rules)

详见设计文档 §六。7 条规则覆盖: 进程挂(critical)、解码错误率(warning)、Web 不可达(critical)、HDFS 使用率(critical/warning)、缺失块(warning)、Kafka lag(warning)。

## Exporter 实现要点

```python
class LiCollector:
    def collect(self):
        metrics = []
        for host in self.servers:
            metrics += self._collect_ztlig(host)
            metrics += self._collect_owls(host)
        return metrics

    def _collect_ztlig(self, host):
        # 1. 进程存活
        for proc in ['ztlig1','ztlig2','ztlig3','ssf','rvf','cmf','psm']:
            count = self.ssh.run(host, f"ps aux | grep -c '[{proc[0]}]'{proc[1:]}")
            ...
        # 2. Kafka stat
        raw = self.ssh.run(host, "show ztlig2 300 kafka stat")
        # 解析 ProduceCount 行，按 topic 拆分
        ...
        # 3. X2 stat
        raw = self.ssh.run(host, "show ztlig2 300 x2 stat")
        ...
```

- SSH 连接池: `max_workers=8`, 缓存 TTL=30s, 重试 3 次
- 每个 parser 输出 `parse_success` 指标便于调试
- 使用 Prometheus `prometheus_client` 库的 `start_http_server(9801)`
