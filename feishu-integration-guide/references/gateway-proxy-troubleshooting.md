# Gateway 代理排障

## 背景

Hermes Gateway 通过 systemd 服务运行，可通过 proxy.conf drop-in 配置代理。
当 Clash Verge / verge-mihomo 在端口 7897 运行时，所有 Gateway 出站连接默认走代理。

## 飞书 WebSocket 走代理问题

飞书 WebSocket 连接 `wss://msg-frontier.feishu.cn` 通过 HTTPS_PROXY 转发。
某些代理可能无法正确转发飞书的 WSS 连接，导致 connect timeout。

### 诊断

```bash
# 检查代理是否在运行
ss -tlnp | grep 7897

# 测试飞书 API 通过代理是否可达
curl -s --connect-timeout 5 -x http://127.0.0.1:7897 https://open.feishu.cn

# 检查 Gateway 日志中的连接状态
journalctl --user -u hermes-gateway.service --no-pager | grep "Lark.*error\|Lark.*timeout"
```

### 修复

将 `.feishu.cn` 加入 NO_PROXY，让飞书直连：

```bash
cat ~/.config/systemd/user/hermes-gateway.service.d/proxy.conf

sed -i 's/NO_PROXY=\(.*\)/NO_PROXY=\1,.feishu.cn/' \
  ~/.config/systemd/user/hermes-gateway.service.d/proxy.conf

systemctl --user daemon-reload
systemctl --user restart hermes-gateway.service
```

## Gateway 优雅关闭卡住

`systemctl --user restart` 时 Gateway 可能进入 `deactivating (stop-sigterm)` 状态卡住，
原因是 MCP 子进程未及时响应 SIGTERM。

### 修复

强制 SIGKILL 再启动：

```bash
systemctl --user kill -s SIGKILL hermes-gateway.service
sleep 2
systemctl --user reset-failed hermes-gateway.service
systemctl --user start hermes-gateway.service
```

## 代理完整配置参考

```ini
[Service]
Environment=HTTPS_PROXY=http://127.0.0.1:7897
Environment=HTTP_PROXY=http://127.0.0.1:7897
Environment=NO_PROXY=localhost,127.0.0.1,::1,.local,.feishu.cn,.aliyuncs.com,.siliconflow.cn,.deepseek.com,.weixin.qq.com,.wechat.com,.xiaohongshu.com,.zhihu.com,.taobao.com,.tmall.com,.csdn.net,.baidu.com,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16
```
