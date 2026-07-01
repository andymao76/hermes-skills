# Grafana Dashboard Metrics Reference

## System Monitoring (ops-monitor-overview)

| Panel | PromQL | Notes |
|-------|--------|-------|
| CPU Usage | `100 - (avg by(instance)(rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)` | Thresholds: green <70%, yellow <90%, red ≥90% |
| Memory Usage | `(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100` | Thresholds: green <80%, yellow <95%, red ≥95% |
| Disk Usage | `(1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100` | Thresholds: green <85%, yellow <95%, red ≥95% |
| Network Rx | `rate(node_network_receive_bytes_total{device!~"lo|bond.*"}[1m])` | Group by device |
| Network Tx | `rate(node_network_transmit_bytes_total{device!~"lo|bond.*"}[1m])` | Group by device |

## NVIDIA GPU Monitoring (nvidia-dcgm) — DCGM Exporter

| Panel | PromQL | DCGM Metric Name | Notes |
|-------|--------|-------------------|-------|
| GPU Utilization | `DCGM_FI_DEV_GPU_UTIL` | DCGM_FI_DEV_GPU_UTIL | 0-100%, per GPU |
| GPU Temperature | `DCGM_FI_DEV_GPU_TEMP` | DCGM_FI_DEV_GPU_TEMP | °C, threshold 80/90 |
| Framebuffer Memory | `DCGM_FI_DEV_FB_USED / DCGM_FI_DEV_FB_TOTAL * 100` | DCGM_FI_DEV_FB_USED/DCGM_FI_DEV_FB_TOTAL | Percentage used |
| Power Usage | `DCGM_FI_DEV_POWER_USAGE` | DCGM_FI_DEV_POWER_USAGE | Watts |
| PCIe Rx | `rate(DCGM_FI_DEV_PCIE_RX_BYTES[1m])` | DCGM_FI_DEV_PCIE_RX_BYTES | Bytes/s |
| PCIe Tx | `rate(DCGM_FI_DEV_PCIE_TX_BYTES[1m])` | DCGM_FI_DEV_PCIE_TX_BYTES | Bytes/s |
| SM Clock | `DCGM_FI_DEV_SM_CLOCK` | DCGM_FI_DEV_SM_CLOCK | MHz |
| Memory Clock | `DCGM_FI_DEV_MEM_CLOCK` | DCGM_FI_DEV_MEM_CLOCK | MHz |
| ECC Errors | `DCGM_FI_DEV_ECC_SBE_AGG_TOTAL` | DCGM_FI_DEV_ECC_SBE_AGG_TOTAL | Single-bit ECC cumulative |

**DCGM Exporter Deployment:**
```bash
# On DGX node
docker run -d --restart always --gpus all \
  --name nvidia-dcgm-exporter \
  -p 9400:9400 \
  nvidia/dcgm-exporter:latest
```

## Spark on YARN Monitoring (spark-yarn)

| Panel | PromQL (via PushGateway) | Notes |
|-------|--------------------------|-------|
| Available Memory | `yarn_available_mb` | Spark app pushes via Prometheus PushGateway |
| Running Containers | `yarn_running_containers` | |
| Pending Containers | `yarn_pending_containers` | |
| Allocated vCores | `yarn_allocated_vcores` | |
| Active Stages | `spark_stage_count_active` | |
| Shuffle Read | `rate(spark_shuffle_read_bytes_total[1m])` | |
| Shuffle Write | `rate(spark_shuffle_write_bytes_total[1m])` | |
| Executor Count | `spark_executor_count_active` | |
| Task Rate | `rate(spark_task_count_total[5m])` | |
| JVM GC Time | `rate(spark_jvm_gc_time_seconds[1m])` | |

**Spark PushGateway Configuration:**
- Spark 3.x built-in: `spark.metrics.conf.*.sink.prometheus.pushgateway.enabled=true`
- For custom apps, push via Prometheus client library:
  ```python
  from prometheus_client import push_to_gateway
  push_to_gateway('pushgateway:9091', job='spark-app-xxx', registry=registry)
  ```

## AlertManager Overview (alertmanager-overview)

| Panel | PromQL | Notes |
|-------|--------|-------|
| Firing Alerts | `count(ALERTS{alertstate="firing"})` | Threshold: yellow ≥1, red ≥5 |
| Severity Distribution | `count by(severity) (ALERTS{alertstate="firing"})` | PieChart or Stat per severity |
| Alert Timeline | `count by(severity) (ALERTS{alertstate="firing"})` | Timeseries over 24h |
| Active Alerts Table | `ALERTS{alertstate="firing"}` | Table with alertname/severity/instance/startsAt |
| Silenced Alerts | `count(ALERTS{suppressed="silence"})` | Currently silenced |
| Notification Count | `rate(alertmanager_notifications_total[24h])` | Total webhook deliveries |

## Hermes Agent Health (hermes-health)

| Panel | PromQL | Notes |
|-------|--------|-------|
| Agent Online | `hermes_up` | Binary: red=0, green=1 |
| CPU Usage | `hermes_cpu_percent` | Threshold: green<60, yellow<85, red≥85 |
| Memory Usage | `hermes_memory_percent` | Threshold: green<70, yellow<90, red≥90 |
| Disk Usage | `hermes_disk_percent` | Threshold: green<80, yellow<90, red≥90 |
| Active Sessions | `hermes_active_sessions` | |
| Platform Connected | `hermes_platform_connected{platform="feishu"}` | Per-platform: feishu, telegram, discord |
| Request Duration | `hermes_request_duration_seconds` | Per endpoint |
| Token Rate | `rate(hermes_token_count_total[5m])` | Tokens/s |
| Error Rate | `rate(hermes_error_total[5m])` | Per error type |
| Loaded Skills | `hermes_loaded_skills` | |
| MCP Server Status | `hermes_mcp_server_up{server=~".+"}` | Per server |

## Dashboard JSON Grid Layout Rules

- **Stat (binary)**: `w=2, h=2` — compact status bricks
- **Stat (numeric)**: `w=3~4, h=2` — textMode=value_and_name, no background
- **Gauge**: `w=4~5, h=2` — horizontal orientation with thresholds
- **Bar Gauge**: `w=5~14, h=2` — gradient or color-on
- **Timeseries**: `w=12, h=5` — showPoints=never, large trend view
- **PieChart**: `w=8, h=5` — for distribution
- **Table**: `w=24, h=6` — full width for alert details
- Total grid width per row = 24 columns
- Row order: Overview → Infrastructure → Services → Timeseries → Details
- Color palette: green `#27ae60` (healthy), red `#e74c3c` (unhealthy), orange `#f39c12` (warning), grey `#95a5a6` (totals)
