# Hermes Health Exporter 参考

Systemd 用户服务，将系统健康检查暴露为 Prometheus 指标，端口 9800。

## 服务管理

```bash
# 启动/停止/重启
systemctl --user start hermes-health-exporter
systemctl --user stop hermes-health-exporter
systemctl --user restart hermes-health-exporter

# 状态
systemctl --user status hermes-health-exporter

# 日志
journalctl --user -u hermes-health-exporter -f
```

## 服务文件

`~/.config/systemd/user/hermes-health-exporter.service`

```ini
[Unit]
Description=Hermes Health Exporter (Prometheus metrics)
After=network.target

[Service]
Type=simple
ExecStart=/home/andymao/.hermes/hermes-agent/venv/bin/python3 /home/andymao/projects/ops-monitor/hermes_health_exporter.py
Restart=always
RestartSec=10
Environment=HERMES_EXPORTER_PORT=9800

[Install]
WantedBy=default.target
```

## 源代码

`/home/andymao/projects/ops-monitor/hermes_health_exporter.py`

检查函数：`check_proxy()` `check_providers()` `check_services()` `check_docker()` `check_processes()` `check_cron()` `check_mcp()` `check_knowledge()` `check_system()` `check_clash()`

## 部署路径

- 项目目录：`/home/andymao/projects/ops-monitor/`
- Prometheus 配置：`/home/andymao/projects/ops-monitor/prometheus.yml`
- Docker Compose：`/home/andymao/projects/ops-monitor/docker-compose.yml`
