# Docker Prometheus 监控栈 — Host 网络模式目标采集坑

## 问题

Prometheus 运行在 Docker 桥接网络（如 `ops-monitor_default`，网关 `172.18.0.1`），而 `node_exporter` 和 `cadvisor` 使用 `network_mode: host`。从 Prometheus 容器内无法通过容器名解析 host 网络模式的容器。

## 解决方案

使用 Docker 桥接网关 IP 替代容器名作为 scrape target：

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'node_exporter'
    static_configs:
      - targets: ['172.18.0.1:9100']   # ← 网关 IP, 非容器名

  - job_name: 'cadvisor'
    static_configs:
      - targets: ['172.18.0.1:8080']   # ← 网关 IP, 非容器名
```

### 工作原理

| 组件 | 网络模式 | 从 Prometheus 容器的可达地址 |
|------|---------|---------------------------|
| Prometheus | `ops-monitor_default` (172.18.0.x) | localhost:9090 (自身) |
| node_exporter | host (宿主机 0.0.0.0:9100) | **172.18.0.1:9100** (桥接网关 = 宿主机) |
| cadvisor | host (宿主机 0.0.0.0:8080) | **172.18.0.1:8080** (桥接网关 = 宿主机) |
| Grafana | `ops-monitor_default` (172.18.0.x) | prometheus:9090 (容器名, 同网络) |

### 验证连通性

```bash
# 从 Prometheus 容器内测试
docker exec prometheus wget -q -O- --timeout=3 http://172.18.0.1:9100/metrics | head -3

# 查看 Prometheus targets
curl localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'
```

## Grafana Provisioning 权限问题

Grafana 容器内部以 uid 472 (grafana) 运行。宿主机创建的文件（uid 1000+）默认不可读。

**症状：** Grafana 容器反复重启，日志显示 `permission denied` on provisioning files。

**解决：**
```bash
chmod -R 644 grafana/provisioning/datasources/*.yaml
chmod -R 644 grafana/provisioning/dashboards/*.yaml
chmod -R 644 grafana/provisioning/dashboards/*.json
chmod 755 grafana/provisioning
chmod 755 grafana/provisioning/datasources
chmod 755 grafana/provisioning/dashboards
docker compose restart grafana
```

## 完整 docker-compose.yml 参考

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports: ["9090:9090"]
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command: ['--config.file=/etc/prometheus/prometheus.yml', '--web.enable-lifecycle']

  node_exporter:
    image: prom/node-exporter:latest
    container_name: node_exporter
    network_mode: host
    pid: host
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--path.rootfs=/rootfs'

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: cadvisor
    network_mode: host
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
    privileged: true
    devices: [/dev/kmsg]

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports: ["3000:3000"]
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

## Grafana Provisioning 文件结构

```
ops-monitor/
├── grafana/provisioning/
│   ├── datasources/
│   │   └── prometheus.yaml     # 自动注册 Prometheus 数据源
│   └── dashboards/
│       ├── dashboards.yaml     # 文件 provider 声明
│       └── node-exporter-full.json  # ID: 1860
├── docker-compose.yml
└── prometheus.yml
```

## 关键命令速查

```bash
docker compose pull              # 拉取镜像
docker compose up -d             # 启动栈
docker compose restart <svc>     # 重启服务
curl -X POST localhost:9090/-/reload  # Prometheus 热加载配置
curl localhost:9090/api/v1/targets     # 查看采集目标
curl localhost:3000/api/health         # Grafana 健康检查
```
