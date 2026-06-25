# Ops Monitor 栈参考

## 项目目录结构

```
/home/andymao/projects/ops-monitor/
├── docker-compose.yml           # 4 服务: prometheus, node_exporter, cadvisor, grafana
├── prometheus.yml               # scrape 配置 (5 targets)
├── hermes_health_exporter.py    # systemd 自定义 exporter (端口 9800)
├── gen_docx.py                  # Word 文档生成器
├── pngs/
│   ├── arch.png                 # 架构图
│   └── flow.png                 # 配置流程图
├── arch-html/
│   ├── arch.html                # 架构图 SVG
│   └── flow.html                # 流程图 SVG
└── grafana/provisioning/
    ├── datasources/
    │   └── prometheus.yaml      # Prometheus 数据源自动预配
    └── dashboards/
        ├── dashboards.yaml      # 仪表盘 provider
        ├── node-exporter-full.json  # Node Exporter Full (ID 1860)
        └── hermes-health.json   # Hermes 系统健康看板 (V9)
```

## 服务列表

| 容器 | 端口 | 网络模式 |
|------|------|----------|
| prometheus | 9090 | ops-monitor_default |
| node_exporter | 9100 | host |
| cadvisor | 8080 | host |
| grafana | 3000 | ops-monitor_default |
| health_exporter | 9800 | host (systemd) |

## 常用命令速查

```bash
# 部署
docker compose -f docker-compose.yml up -d
docker compose -f docker-compose.yml restart <service>

# 重载 Prometheus 配置
curl -X POST http://localhost:9090/-/reload

# 检查目标
curl -s http://localhost:9090/api/v1/targets | python3 -m json.tool

# 健康检查
curl -s http://localhost:3000/api/health
curl -s http://127.0.0.1:9800/metrics | grep "^hermes_"

# 看板
# http://localhost:3000 (admin/admin)
```

## 架构图

参见 `~/prometheus-grafana-监控架构配置文档.docx` 中的图1（架构图）和图2（配置流程图）。
