# Monitoring Stack Troubleshooting Cases

## Case 1: Grafana 端口映射损坏
**现象：** ERR_CONNECTION_REFUSED，docker ps 显示 Grafana Up。

**诊断：**
```bash
docker port grafana                # 空输出 → 端口未映射
docker inspect grafana --format '{{json .NetworkSettings.Ports}}'
# → {} 或 {"3000/tcp": [{"invalid IP 3000"}]}
```

**修复：** 删除容器重建，指定 `-p 3000:3000`。

## Case 2: Grafana 看板无数据 — DNS 解析失败
**现象：** 看板空白，Prometheus targets 全部 UP。Grafana API 查询报 no such host。

**诊断：**
```bash
docker inspect grafana --format '{{json .NetworkSettings.Networks}}'
docker inspect prometheus --format '{{json .NetworkSettings.Networks}}'
```

**修复：** `docker network connect <prometheus_network> grafana && docker restart grafana`

## Case 3: Exporter MCP 全部离线
**现象：** hermes_mcp_ratio=0, hermes_mcp_cli_reachable=0，手动 hermes mcp list 正常。

**根因：** systemd user service PATH 不包含 ~/.local/bin/。

**修复：** service 添加 `Environment=PATH=/home/andymao/.local/bin:/usr/local/bin:/usr/bin:/bin`

## Case 4: Exporter 抓取超时
**现象：** Prometheus target down, context deadline exceeded。本地 curl :9800/metrics 需 20-30s。

**根因：** Prometheus 默认 scrape_timeout=10s，exporter 响应约 20s。

**修复：** 配置添加 `scrape_timeout: 30s`。

## Case 5: 数据库全不可达
**现象：** 所有 hermes_db_reachable=0，SQLite 文件存在。

**根因：** sqlite3 命令未安装。

**修复：** `sudo apt-get install -y sqlite3`

## Case 6: Gateway API 不可达
**现象：** hermes_api_up{api="gateway"}=0，Gateway 运行正常。

**根因：** Exporter 检查端口 8088，实际 8080。/health 返回 307 不在允许列表。

**修复：** 改 8088→8080，状态码列表加 '307'。

## 排查顺序
Container → Port → Targets → Exporter → Query
