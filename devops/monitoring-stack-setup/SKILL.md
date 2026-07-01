---
name: monitoring-stack-setup
description: Deploy a Docker-based monitoring stack — Prometheus, Grafana, node_exporter, cadvisor — with auto-provisioning and best-practice scrape targets. Use when setting up host + container monitoring from scratch on a Linux Docker host.
---

# Monitoring Stack Setup (Docker Compose)

Deploy a Prometheus + Grafana + node_exporter + cadvisor stack via Docker Compose, with Grafana datasource and dashboard auto-provisioning.

## Stack Architecture (Base)

```
node_exporter (host:9100) ───┐
                              ├──► Prometheus (:9090) ──► Grafana (:3000)
cadvisor (host:8080) ────────┘          │
                                   (self :9090)
```

## Stack Architecture (Extended — LI platform + DGX + Spark)

```
node_exporter (host:9100) ─────────┐
cadvisor (host:8080) ─────────────┐├──┐
DCGM Exporter (DGX:9400) ────────┤│  │
Spark PushGateway (host:9091) ───┤├──┼──► Prometheus (:9090) ──► Grafana (:3000)
AlertManager (:9093) ─────────────┤│  │
Hermes Health (host:9800) ───────┘├──┘    │
                                    │  AlertManager (:9093) ──► Webhook (:9802)
                                    │       ├── 飞书 Bot
                                    │       └── Telegram Bot
```


## Extended Docker Compose (with DCGM/PushGateway/AlertManager/Webhook)

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports: ["9090:9090"]
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./alert_rules.yml:/etc/prometheus/alert_rules.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--web.enable-lifecycle'
    restart: always

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
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: cadvisor
    network_mode: host
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    privileged: true
    devices: [/dev/kmsg]

  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    ports: ["9093:9093"]
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--log.level=debug'

  alert-webhook:
    build:
      context: .
      dockerfile: Dockerfile.webhook
    container_name: alert-webhook
    ports: ["9802:9802"]
    env_file:
      - /home/andymao/.hermes/.env
    restart: always

  spark-pushgateway:
    image: prom/pushgateway:latest
    container_name: spark-pushgateway
    ports: ["9091:9091"]
    restart: always

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports: ["3000:3000"]
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin   # change on first login
    restart: always

volumes:
  prometheus_data:
  grafana_data:
```

This extended stack adds:
- **AlertManager** — manages alert routing, grouping, inhibition, silencing
- **Alert Webhook** — custom Flask service (port 9802) forwarding to 飞书 + Telegram
- **Spark PushGateway** — receives Spark application metrics via Prometheus PushGateway protocol
- **DCGM Exporter** — deployed separately on NVIDIA DGX (port 9400), scraped remotely
- **Hermes Health Exporter** — runs as systemd user service on host (port 9800)

## Prometheus Scrape Config (Extended)

```yaml
scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node_exporter'
    static_configs:
      - targets: ['172.18.0.1:9100']   # Docker bridge gateway

  - job_name: 'cadvisor'
    static_configs:
      - targets: ['172.18.0.1:8080']

  - job_name: 'nvidia-dcgm'
    scrape_interval: 15s
    static_configs:
      - targets: ['<DGX-IP>:9400']     # DGX node running DCGM Exporter

  - job_name: 'spark-pushgateway'
    honor_labels: true
    static_configs:
      - targets: ['spark-pushgateway:9091']

  - job_name: 'hermes_health'
    scrape_interval: 30s
    scrape_timeout: 30s                 # exporter response ~20s
    static_configs:
      - targets: ['172.18.0.1:9800']

  - job_name: 'alertmanager'
    static_configs:
      - targets: ['alertmanager:9093']
```

**Note on scrape addresses:** node_exporter, cadvisor, and hermes_health use `network_mode: host` or run directly on host, so they're reached via Docker bridge gateway IP. Container-based services (alertmanager, spark-pushgateway) are reached by compose service name.

## Prometheus Config (prometheus.yml)

```yaml
scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node_exporter'
    static_configs:
      - targets: ['172.18.0.1:9100']    # Docker bridge gateway — host IP from container

  - job_name: 'cadvisor'
    static_configs:
      - targets: ['172.18.0.1:8080']    # same gateway IP
```

**Scrape address note:** node_exporter and cadvisor use `network_mode: host`, so they are NOT reachable by container name. Prometheus must scrape them via the Docker bridge gateway IP (typically `172.18.0.1` for the first compose network — verify with `docker inspect <container>` and read the NetworkSettings.Gateway field).

## Grafana Provisioning (Multi-Folder Multi-Dashboard)

### Directory Structure
```
grafana/provisioning/
├── datasources/
│   └── prometheus.yaml              # auto-registers Prometheus datasource
└── dashboards/
    ├── dashboards.yaml              # multi-folder provider declarations
    ├── node-exporter-full.json      # Grafana import ID 1860
    ├── ops-monitor-overview.json    # system + ZTLIG + OWLS + HDFS
    ├── nvidia-dcgm.json             # GPU utilization/temp/memory/power/ECC
    ├── spark-yarn.json              # YARN resources + Spark Job/Stage/Task
    ├── alertmanager-overview.json   # firing alerts / severity / timeline
    └── hermes-health.json           # Agent CPU/mem/disk/sessions/latency
```

### Datasource Config (datasources/prometheus.yaml)
```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090     # Docker compose service name
    isDefault: true
    editable: false
    jsonData:
      timeInterval: 15s
      queryTimeout: 60s
```

### Multi-Folder Dashboard Provider Config (dashboards/dashboards.yaml)

Each provider group creates a Grafana folder and loads all JSON files. Grafana auto-assigns dashboards to folders by the `providers[].name` — but since all providers scan the same directory, **every dashboard appears in every folder**. To assign dashboards to specific folders, use one of:
1. **Separate directories per folder** (workaround): create subdirs like `dashboards/system/`, `dashboards/gpu/`, etc., each with its own `dashboards.yaml`
2. **Folder by tags** (not standard provisioning): use Grafana API to move dashboards post-deploy
3. **Naming convention**: prefix dashboard JSONs and let the user reorganize manually

**Recommended approach** — separate provider per folder pointing to same directory (dashboards land in whichever folder the first matching provider creates):
```yaml
apiVersion: 1
providers:
  - name: 'Default'
    orgId: 1
    folder: '系统监控'
    type: file
    editable: true
    options:
      path: /etc/grafana/provisioning/dashboards

  - name: 'AlertManager'
    orgId: 1
    folder: '告警中心'
    type: file
    editable: true
    options:
      path: /etc/grafana/provisioning/dashboards
```

For clean folder separation, use **subdirectory per provider** — this is the production-grade approach:
```
grafana/provisioning/dashboards/
├── dashboards.yaml              # single provider, path set at runtime
├── system/
│   ├── dashboards.yaml          # provider folder='系统监控', path=./system/
│   └── node-exporter-full.json
├── gpu/
│   ├── dashboards.yaml          # provider folder='GPU 推理机', path=./gpu/
│   └── nvidia-dcgm.json
├── bigdata/
│   ├── dashboards.yaml          # provider folder='大数据', path=./bigdata/
│   └── spark-yarn.json
└── agent/
    ├── dashboards.yaml          # provider folder='Agent 健康', path=./agent/
    └── hermes-health.json
```

### Dashboard JSON Template (minimal example — hermes-health)

```json
{
  "title": "Hermes Agent 健康状态",
  "uid": "hermes-health",
  "version": 1,
  "schemaVersion": 39,
  "tags": ["hermes", "health"],
  "timezone": "browser",
  "editable": true,
  "refresh": "30s",
  "panels": [
    {
      "title": "Agent 在线",
      "type": "stat",
      "gridPos": {"x": 0, "y": 0, "w": 4, "h": 4},
      "targets": [{"expr": "hermes_up", "legendFormat": "状态"}],
      "fieldConfig": {
        "defaults": {
          "thresholds": {
            "steps": [{"color": "red", "value": null}, {"color": "green", "value": 1}]
          }
        }
      },
      "datasource": "Prometheus"
    },
    {
      "title": "CPU 使用率",
      "type": "gauge",
      "gridPos": {"x": 4, "y": 0, "w": 4, "h": 4},
      "targets": [{"expr": "hermes_cpu_percent", "legendFormat": "CPU %"}],
      "fieldConfig": {
        "defaults": {
          "unit": "percent",
          "min": 0, "max": 100,
          "thresholds": {
            "steps": [{"color": "green", "value": null}, {"color": "yellow", "value": 60}, {"color": "red", "value": 85}]
          }
        }
      },
      "datasource": "Prometheus"
    },
    {
      "title": "API 请求延迟",
      "type": "timeseries",
      "gridPos": {"x": 0, "y": 4, "w": 8, "h": 5},
      "targets": [{"expr": "hermes_request_duration_seconds", "legendFormat": "{{method}} {{endpoint}}"}],
      "fieldConfig": {
        "defaults": {"unit": "s", "custom": {"showPoints": "never"}}
      },
      "datasource": "Prometheus"
    }
  ]
}
```

See `templates/` for full dashboard JSONs for each domain.

### Multi-Domain Dashboard Design Patterns

| Domain | Dashboard UID | Key Metrics | Panel Types |
|--------|--------------|------------|-------------|
| **System** | ops-monitor-overview | CPU/Mem/Disk gauge, network timeseries, ZTLIG/OWLS/HDFS stat | Gauge + Stat + Timeseries |
| **GPU** | nvidia-dcgm | DCGM_FI_DEV_GPU_UTIL, _FB_USED, _GPU_TEMP, _POWER_USAGE, _ECC_SBE_AGG_TOTAL | Gauge + Timeseries |
| **Spark** | spark-yarn | yarn_available_mb, spark_stage_count, spark_shuffle_read/write_bytes, spark_executor_count | Gauge + Stat + Timeseries |
| **Alerts** | alertmanager-overview | ALERTS{alertstate="firing"}, alertmanager_notifications_total | Stat + PieChart + Table |
| **Agent** | hermes-health | hermes_up, hermes_cpu/memory/disk_percent, hermes_request_duration_seconds, hermes_token_count_total | Stat + Gauge + Timeseries |

## Common Pitfalls

### ❌ Grafana 看板无数据（DNS 无法解析 Prometheus）

**现象：** Grafana 看板打开显示无数据，Prometheus targets 全部 UP，Prometheus API 查询正常。

Grafana datasource 探针返回：
```
Post "http://prometheus:9090/api/v1/query_range":
dial tcp: lookup prometheus on 8.8.8.8:53: no such host
```

**根因：** Grafana 和 Prometheus 不在同一个 Docker 网络。`docker run` 重建 Grafana 时默认连 `bridge` 网络，而 Prometheus 在自定义网络（如 `ops-monitor_default`）上，容器名 DNS 解析不通。

**修复：**

```bash
# 方案 A：将 Grafana 连接到 Prometheus 所在网络（推荐）
docker network connect ops-monitor_default grafana
docker restart grafana

# 方案 B：重建时指定网络
docker run -d --name grafana --network ops-monitor_default -p 3000:3000 ...

# 验证
curl -s 'http://admin:admin@localhost:3000/api/ds/query' \
  -X POST -H 'Content-Type: application/json' \
  -d '{"queries":[{"datasource":{"type":"prometheus","uid":"PBFA97CFB590B2093"},"expr":"hermes_up","refId":"A"}],"from":"now-5m","to":"now"}'
```

**预防：** 重建容器后检查同网络连接：`docker inspect grafana --format '{{json .NetworkSettings.Networks}}'`

### ❌ Grafana 端口映射损坏 — 容器运行但无法访问

Grafana 容器状态 Up 但宿主机无法访问 localhost:3000。检查：

```bash
docker port grafana        # 空输出 → 端口未映射
docker inspect grafana --format '{{json .NetworkSettings.Ports}}'
# 返回 {} 或含 invalid IP → 端口映射损坏
```

**修复：** 删除容器重建（保留数据卷）：

```bash
docker rm -f grafana
docker run -d \
  --name grafana \
  --restart always \
  -p 3000:3000 \
  -v ops-monitor_grafana_data:/var/lib/grafana \
  -v /home/andymao/projects/ops-monitor/grafana/provisioning:/etc/grafana/provisioning \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  grafana/grafana:latest
```

数据卷 ops-monitor_grafana_data 保留，重建后配置和数据不丢失。

### ❌ Grafana fails to start — permission denied on provisioning files
Grafana container runs as uid **472** (grafana user). Files mounted via bind volume inherit the host's UID/GID. If files are owned by UID 1000, Grafana cannot read them.

**Fix:**
```bash
chmod -R 644 grafana/provisioning/datasources/*.yaml
chmod -R 644 grafana/provisioning/dashboards/*.yaml
chmod -R 644 grafana/provisioning/dashboards/*.json
chmod 755 grafana/provisioning/datasources
chmod 755 grafana/provisioning/dashboards
```

This makes files world-readable, bypassing the UID mismatch.

### ❌ Prometheus targets show "unknown" for node_exporter/cadvisor
First scrape may take up to the `scrape_interval` (default 1 minute). Wait 60s or check `lastScrape` field in the targets API — if it's `0001-01-01T00:00:00Z`, the first scrape hasn't occurred yet.

### ❌ Reload didn't take effect after config change
Verify the container actually has the new config:
```bash
docker exec prometheus cat /etc/prometheus/prometheus.yml
```
If the file is stale, the compose bind mount may not have synced. Use `docker compose restart prometheus` instead of relying on `POST /-/reload`.

## Design Report Generation (HTML → PDF)

For delivering monitoring design documents, use HTML-first rendering to PDF with wkhtmltopdf. This gives full control over layout (gradient headers, info/success/warning callout boxes, badges, TOC, code blocks, tables).

### Pipeline

```bash
# 1. Design report as a single HTML file with embedded CSS
# 2. Convert to PDF:
wkhtmltopdf --encoding UTF-8 --enable-local-file-access --page-size A4 \
  --margin-top 25mm --margin-bottom 25mm --margin-left 20mm --margin-right 20mm \
  --no-stop-slow-scripts --javascript-delay 1000 \
  report.html /tmp/design_report.pdf
```

### CSS Patterns for Professional Reports

```css
/* Cover page with gradient accent bar */
.cover::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 8px;
  background: linear-gradient(90deg, #667eea, #764ba2);
}

/* Info / Warning / Success callout boxes */
.info-box { background: #eef2ff; border-left: 4px solid #667eea; }
.warn-box { background: #fff3e0; border-left: 4px solid #ff9800; }
.success-box { background: #e8f5e9; border-left: 4px solid #4caf50; }

/* Gradient table headers */
th {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  padding: 8px 10px;
}

/* Dark code blocks */
pre { background: #1e1e2e; color: #cdd6f4; border-radius: 8px; }

/* Badge/tag elements */
.badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 8pt; }
.tag-green { background: #e8f5e9; color: #2e7d32; }
.tag-red { background: #ffebee; color: #c62828; }
.tag-blue { background: #e3f2fd; color: #1565c0; }

/* Page breaks */
h1 { page-break-before: always; }
.toc { page-break-after: always; }
.cover { page-break-after: always; }

/* Footer */
.footer { margin-top: 40px; padding-top: 10px; border-top: 1px solid #ddd; font-size: 9pt; color: #999; }
```

### Report Structure Template

1. Cover page (title, subtitle, version, date, badge)
2. Table of Contents (auto-numbered)
3. Hardware comparison table (if multi-node)
4. System / software environment
5. Architecture diagram (ASCII or SVG)
6. Component configs (Prometheus, AlertManager, Webhook)
7. Alert rules table
8. Docker Compose configuration
9. Grafana provisioning
10. File manifest / directory tree
11. Port mapping table
12. Deployment steps (numbered checklist)
13. Footer

## Verification

Exporter 默认使用 `http://127.0.0.1:8088/health` 检查 Gateway。若 Gateway 实际端口不同（常见 8080），需同步修改 exporter 代码：

```python
'gateway': ('http://127.0.0.1:8080/health', False, 3),
```

同时注意 `/health` 端点可能返回 HTTP 307，需要在 exporter 的允许状态码列表中添加 `'307'`。

## Verification

After stack startup:

```bash
# All containers running
docker ps

# Prometheus targets all up
curl -s http://localhost:9090/api/v1/targets
```

**⚠️ 初始等待：** 首次启动后 Prometheus 需要 30~60 秒完成首轮抓取。`scrape_interval=30s` 是开始间隔，不是首次抓取时刻。立即查 targets 可能显示 `unknown` 是正常行为。

## Hermes Health Exporter (systemd user service)

For host-level health checks (proxy, provider, services, cron, MCP, knowledge), prefer a **systemd user service** rather than Docker:

**依赖项：** exporter 使用 `sqlite3` 命令做数据库连通性测试。未安装时所有数据库显示不可达：

```bash
sudo apt-get install -y sqlite3
```

Service 配置模板：

```
# ~/.config/systemd/user/hermes-health-exporter.service
[Unit]
Description=Hermes Health Exporter (Prometheus metrics)
After=network.target
[Service]
Type=simple
ExecStart=/home/andymao/.hermes/hermes-agent/venv/bin/python3 /path/to/exporter.py
Restart=always
RestartSec=10
Environment=HERMES_EXPORTER_PORT=9800
[Install]
WantedBy=default.target
```

Exposes ~30 metric families on `:9800/metrics` — proxy, API providers, systemd services, Docker containers, system load/memory/disk, cron scripts, Clash airport, knowledge base stats.

**⚠️ PATH pitfall — systemd 用户服务找不到 hermes CLI**

`hermes mcp list` 在 exporter 中用于检测 MCP server 状态。systemd user service 默认 PATH 不包含 `~/.local/bin/`，导致 `hermes` 命令不可用：

```bash
# 查看 exporter 指标 → hermes_mcp_cli_reachable = 0
curl -s http://127.0.0.1:9800/metrics | grep mcp_cli
```

**修复：** 在 service 文件中显式设置 PATH：

```ini
[Service]
Environment=PATH=/home/andymao/.local/bin:/usr/local/bin:/usr/bin:/bin
```

修改后重载并重启：

```bash
systemctl --user daemon-reload
systemctl --user restart hermes-health-exporter
```

**验证：** `curl -s http://127.0.0.1:9800/metrics | grep hermes_mcp_cli_reachable` → 应为 `1`

**⚠️ scrape_timeout 不足 — Prometheus 抓取 exporter 超时**

Hermes Health Exporter 需要执行 `hermes mcp list`、provider API 检测等耗时操作，响应时间约 20 秒。Prometheus 默认 `scrape_timeout` 为 **10 秒**，导致每次抓取都超时：

```bash
# Prometheus targets 显示 down
curl -s http://localhost:9090/api/v1/targets
# hermes_health → down ❌ Get "...": context deadline exceeded
```

**修复：** 在 Prometheus 配置中为 `hermes_health` job 添加 `scrape_timeout: 30s`：

```yaml
  - job_name: 'hermes_health'
    scrape_interval: 30s
    scrape_timeout: 30s    # 匹配 exporter 实际响应时间
    static_configs:
      - targets: ['172.18.0.1:9800']
```

修改后重启 Prometheus：

```bash
docker restart prometheus
```

**Scrape config** — uses Docker bridge gateway IP (host from container perspective):

```yaml
  - job_name: 'hermes_health'
    scrape_interval: 30s
    scrape_timeout: 30s
    static_configs:
      - targets: ['172.18.0.1:9800']
```

Find the IP with: `docker inspect prometheus --format '{{range .NetworkSettings.Networks}}{{.Gateway}}{{end}}'`

## Clash Verge Airport Monitoring (Unix Socket API)

Clash Verge Rev (mihomo) REST API is at `/tmp/verge/verge-mihomo.sock` (external controller typically disabled):

```bash
curl -s --unix-socket /tmp/verge/verge-mihomo.sock http://localhost/proxies
curl -s --unix-socket /tmp/verge/verge-mihomo.sock http://localhost/version
```

`/proxies` response includes:
- **Selector groups** — `now` = current selection, `all` = node list
- **URLTest groups** — `now` = best-latency node
- **Proxies** — type=Shadowsocks/VMess/Trojan/Hysteria2/VLESS

Subscription info (traffic remaining, expire date) lives in the YAML profile as fake proxy nodes. Also extractable from profiles/ directory.

## Grafana Dashboard Design (User Conventions)

See `references/grafana-dashboard-metrics.md` for full PromQL reference and grid layout rules.

When creating/provisioning dashboards:

- **Stat binary status** (color-background): `w=2, h=2` — compact bricks
- **Stat numeric values**: `w=3~4, h=2` — no background, textMode=value_and_name
- **Gauges**: `w=4~5, h=2` — horizontal orientation
- **Bar gauges**: `w=5~14, h=2` — color-on or gradient
- **Time series**: `w=12, h=5`
- Panels fill exactly 24 grid columns per row
- Row order: Overview → Infrastructure → Services/MCP → Cron/Snap → Knowledge → Time series
- Colors: green `#27ae60` (healthy), red `#e74c3c` (unhealthy), orange `#f39c12` (warning), grey `#95a5a6` (totals)

## 排查案例集

`references/monitoring-troubleshooting-cases.md` 收录了以下故障案例：

| # | 问题 | 排查要点 |
|---|------|---------|
| 1 | Grafana 端口不可达 | `docker port grafana` → 重建容器 |
| 2 | 看板无数据 (DNS) | `docker inspect` 网络 → `network connect` |
| 3 | Exporter PATH (MCP 离线) | `hermes_mcp_cli_reachable=0` → 加 `Environment=PATH` |
| 4 | Exporter 抓取超时 | `scrape_timeout: 30s` |
| 5 | 数据库全不可达 | 安装 `sqlite3` + 清理不存在的 DB 监控 |
| 6 | Gateway API 不通 | 端口 8088→8080 + 允许 307 |

排查顺序: Container → Port → Targets → Exporter → Query
