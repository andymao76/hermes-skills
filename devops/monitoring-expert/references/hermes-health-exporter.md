# Hermes Health Exporter v2

## Overview

Custom Prometheus exporter exposing Hermes-specific health metrics. Runs as a Python HTTP server on port 9800 (systemd user service).

## Architecture

```
                        ┌──────────────────────────────────────┐
                        │  hermes-health-exporter (:9800)       │
                        │  check_system() → load/mem/disk       │
                        │  check_mcp()    → 14 MCP servers      │
                        │  check_providers() → DeepSeek/SF/latency│
                        │  check_apis()   → Gateway/GF/Prom     │
                        │  check_docker() → containers/ratio     │
                        │  check_databases() → SQLite/Doris     │
                        │  check_skills() → total/active ratio  │
                        │  check_knowledge() → kb/enzyme        │
                        │  check_clash()  → nodes/api           │
                        │  check_proxy()  → GUI/kernel/port     │
                        │  check_cron()   → active/failed jobs  │
                        └──────────────┬───────────────────────┘
                                       │ scrape 30s
                          ┌────────────▼───────────┐
                          │     Prometheus :9090    │
                          └────────────┬───────────┘
                                       │ PromQL
                          ┌────────────▼───────────┐
                          │  Grafana health dashboard│
                          └──────────────────────────┘
```

## Exported Metrics (v2)

### System Load
| Metric | Type | Description |
|--------|------|-------------|
| `hermes_load1/5/15` | gauge | System load averages |
| `hermes_mem_avail_bytes` | gauge | Available RAM |
| `hermes_mem_total_bytes` | gauge | Total RAM |
| `hermes_disk_avail_bytes` | gauge | Available root disk |
| `hermes_disk_total_bytes` | gauge | Total root disk |

### MCP Monitoring (NEW in v2)
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `hermes_mcp_server_up` | gauge | `server={csdn,db-query,...,linear}` | 1 if MCP server is up |
| `hermes_mcp_server_enabled` | gauge | `server={...}` | 1 if MCP server is enabled |
| `hermes_mcp_ratio` | gauge | - | Online rate % (up / total × 100) |
| `hermes_mcp_cli_reachable` | gauge | - | 1 if `hermes mcp list` works |

### Provider HTTP (latency added in v2)
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `hermes_provider_up` | gauge | `provider={deepseek,siliconflow,siliconflow_cn}` | 1 if API reachable |
| `hermes_provider_http_code` | gauge | `provider={...}` | Last HTTP status code |
| `hermes_provider_latency_seconds` | gauge | `provider={...}` | Response latency in seconds |

### Internal API (NEW in v2)
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `hermes_api_up` | gauge | `api={gateway,openwebui,prometheus,grafana,clash_api}` | 1 if API endpoint reachable |
| `hermes_api_latency_seconds` | gauge | `api={...}` | Response latency in seconds |

### Docker
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `hermes_docker_up` | gauge | - | 1 if dockerd is running |
| `hermes_docker_container_running` | gauge | - | Running containers count |
| `hermes_docker_container_total` | gauge | - | Total containers count |
| `hermes_docker_container_ratio` | gauge | - | Running/Total ratio % |
| `hermes_docker_container_up` | gauge | `name={prometheus,grafana,node_exporter,cadvisor}` | 1 if specific container running |

### Database (NEW in v2)
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `hermes_db_bytes` | gauge | `db={Hermes会话,查询缓存,知识索引,记忆存储,历史会话}` | SQLite file sizes |
| `hermes_db_reachable` | gauge | `db={...}` | 1 if SQLite file opens `SELECT 1` |
| `hermes_db_doris_reachable` | gauge | - | 1 if Doris MCP tool responds |

### Skill Activity (NEW in v2)
| Metric | Type | Description |
|--------|------|-------------|
| `hermes_skills_total` | gauge | Total skill count |
| `hermes_skills_modified_7d` | gauge | Skills modified in last 7 days |
| `hermes_skills_active_ratio` | gauge | (modified_7d / total) × 100 |
| `hermes_skills_inactive_7d` | gauge | Total - modified_7d |

### Knowledge Base
| Metric | Type | Description |
|--------|------|-------------|
| `hermes_kb_files` | gauge | Markdown file count |
| `hermes_kb_bytes` | gauge | Total size of markdown files |
| `hermes_enzyme_db_bytes` | gauge | enzyme.db size |
| `hermes_enzyme_age_hours` | gauge | Hours since last enzyme refresh |

### Clash / Proxy / Cron
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `hermes_clash_api` | gauge | - | 1 if Clash API responds |
| `hermes_clash_total_proxies` | gauge | - | Total proxy nodes |
| `hermes_cron_active_jobs` | gauge | - | Active Hermes cron jobs |
| `hermes_cron_failed_jobs` | gauge | - | Jobs with delivery failures |

### Composite
| Metric | Type | Description |
|--------|------|-------------|
| `hermes_up` | gauge | 1 if: proxy + MCP>50% + provider + Docker all OK |

## Deployment

### Service File
`~/.config/systemd/user/hermes-health-exporter.service`:
```ini
[Unit]
Description=Hermes Health Exporter v2 (Prometheus metrics)
After=network.target

[Service]
Type=simple
ExecStart=/home/andymao/.hermes/hermes-agent/venv/bin/python3 /home/andymao/projects/ops-monitor/hermes_health_exporter.py
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
```

### Commands
```bash
systemctl --user daemon-reload
systemctl --user enable --now hermes-health-exporter
systemctl --user status hermes-health-exporter
journalctl --user -u hermes-health-exporter -f
```

### Restart After Update
```bash
systemctl --user restart hermes-health-exporter
curl -s http://localhost:9800/metrics | head -5
```

## Grafana Dashboard (via API Import)

```bash
curl -s -X POST http://admin:admin@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @hermes-dashboard-v2.json
```

Dashboard rows:
1. **综合健康** — health stat + load/memory/disk gauges + MCP/Provider/Container/Skill
2. **系统负载** — CPU/memory/disk time series
3. **MCP 监控** — server bargauge + online rate + detail table
4. **Provider + API** — bargauge + latency + API status
5. **Docker 监控** — daemon + ratio + containers + stats
6. **数据库** — file sizes + reachability + Doris
7. **Skill 活跃比** — gauge + stats + trend
8. **知识库** — files + size + enzyme DB + age

## Project Files
```
/home/andymao/projects/ops-monitor/
├── docker-compose.yml
├── prometheus.yml
├── hermes_health_exporter.py    # v2 exporter
└── grafana/provisioning/
    ├── datasources/prometheus.yaml
    └── dashboards/ (node-exporter-full.json)
```

## Pitfalls

1. **Host network + Docker scrape**: Prometheus in Docker reaches host exporter via `172.18.0.1:9800` (Docker bridge gateway), NOT `localhost`.
2. **sqlite3 CLI**: `hermes_db_reachable` uses `sqlite3 SELECT 1` — install: `sudo apt install sqlite3`.
3. **Prometheus reload**: `curl -X POST localhost:9090/-/reload` or `docker compose restart prometheus`.
4. **CACHE_TTL**: 30s default. Export time is fast (~0.3s) but cache avoids overloading CLI.
5. **CLI dependency**: MCP/cron metrics rely on `hermes mcp list` and `hermes cron list` being fast. If they time out (>15s), those metrics fall back to 0.
