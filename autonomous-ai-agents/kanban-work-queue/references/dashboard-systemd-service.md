# Hermes Dashboard Systemd 用户服务

自动启动 Hermes Dashboard 作为 systemd 用户服务，免去每次手动 `hermes dashboard`。

## 服务文件

路径：`~/.config/systemd/user/hermes-dashboard.service`

```
[Unit]
Description=Hermes Agent Dashboard
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=<HERMES_VENV>/bin/hermes dashboard --port 9119 --no-open
Restart=on-failure
RestartSec=5
Environment=HERMES_HOME=<HERMES_HOME>

[Install]
WantedBy=default.target
```

> `<HERMES_VENV>` → `~/.hermes/hermes-agent/venv`  
> `<HERMES_HOME>` → `~/.hermes`

## 启用与管理

```bash
systemctl --user daemon-reload
systemctl --user enable hermes-dashboard.service   # 开机自启
systemctl --user start hermes-dashboard.service    # 立即启动
systemctl --user status hermes-dashboard.service   # 查看状态

# 日常管理
systemctl --user stop hermes-dashboard
systemctl --user restart hermes-dashboard
journalctl --user -u hermes-dashboard -n 30        # 查看日志
```

## 验证

```bash
ss -tlnp | grep 9119
# → LISTEN 127.0.0.1:9119
```

浏览器打开 http://127.0.0.1:9119

## 注意事项

- Dashboard 会自动停掉旧实例（如果有），防止端口冲突
- 默认只绑定 `127.0.0.1`，不暴露到局域网
- 如需远程访问，加 `--insecure` 参数（⚠️ 暴露 API Key）
- 如果同时启用了 Hermes Gateway，dashboard 是独立服务，互不影响
