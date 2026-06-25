---
name: monitoring-stack-setup
description: Deploy a Docker-based monitoring stack — Prometheus, Grafana, node_exporter, cadvisor — with auto-provisioning and best-practice scrape targets. Use when setting up host + container monitoring from scratch on a Linux Docker host.
---

# Monitoring Stack Setup (Docker Compose)

Deploy a Prometheus + Grafana + node_exporter + cadvisor stack via Docker Compose, with Grafana datasource and dashboard auto-provisioning.

## Stack Architecture

```
node_exporter (host:9100) ───┐
                              ├──► Prometheus (:9090) ──► Grafana (:3000)
cadvisor (host:8080) ────────┘          │
                                   (self :9090)
```

## Docker Compose Template

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--web.enable-lifecycle'    # enables POST /-/reload for config hot-reload
    restart: always

  node_exporter:
    image: prom/node-exporter:latest
    container_name: node_exporter
    network_mode: host              # needed to see host /proc /sys
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
    restart: always

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
    devices:
      - /dev/kmsg
    restart: always

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
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

## Grafana Provisioning

### Directory Structure
```
grafana/provisioning/
├── datasources/
│   └── prometheus.yaml
└── dashboards/
    ├── dashboards.yaml
    └── node-exporter-full.json    # dashboard ID 1860
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
```

### Dashboard Provider Config (dashboards/dashboards.yaml)
```yaml
apiVersion: 1

providers:
  - name: 'Default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    editable: true
    options:
      path: /etc/grafana/provisioning/dashboards
```

## Common Pitfalls

### ❌ Grafana fails to start — "permission denied" on provisioning files
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

## Dashboard Sources

| Dashboard | ID | Load Command |
|-----------|:--:|-------------|
| Node Exporter Full | 1860 | `curl -o node-exporter-full.json "https://grafana.com/api/dashboards/1860/revisions/latest/download"` |

## Verification

After stack startup:

```bash
# All containers running
docker ps

# Prometheus targets all up
curl -s http://localhost:9090/api/v1/targets | python3 -c "
import json,sys
for t in json.load(sys.stdin)['data']['activeTargets']:
    print(f'{t[\"labels\"][\"job\"]:20s} {t[\"health\"]}')
"

# Grafana datasource provisioned
curl -s http://admin:admin@localhost:3000/api/datasources

# Grafana dashboards provisioned
curl -s http://admin:admin@localhost:3000/api/search
```

## Custom Exporter: Hermes Health Exporter (systemd)

For host-level health checks (proxy, provider, services, cron, MCP, knowledge), prefer a **systemd user service** rather than Docker:

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

**Scrape config** — uses Docker bridge gateway IP (host from container perspective):

```yaml
  - job_name: 'hermes_health'
    scrape_interval: 30s
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

When creating/provisioning dashboards:

- **Stat binary status** (color-background): `w=2, h=2` — compact bricks
- **Stat numeric values**: `w=3~4, h=2` — no background, textMode=value_and_name
- **Gauges**: `w=4~5, h=2` — horizontal orientation
- **Bar gauges**: `w=5~14, h=2` — color-on or gradient
- **Time series**: `w=12, h=5`
- Panels fill exactly 24 grid columns per row
- Row order: Overview → Infrastructure → Services/MCP → Cron/Snap → Knowledge → Time series
- Colors: green `#27ae60` (healthy), red `#e74c3c` (unhealthy), orange `#f39c12` (warning), grey `#95a5a6` (totals)
