# Clash Verge 配置诊断示例（2026-06-10）

源自实际诊断会话。两个订阅的完整配置和节点状态。

## 配置路径

```
~/.local/share/io.github.clash-verge-rev.clash-verge-rev/profiles.yaml
~/.local/share/io.github.clash-verge-rev.clash-verge-rev/verge.yaml
```

## 订阅概览

| 属性 | Basic-677806（当前） | CrossWall 克洛斯 |
|------|---------------------|-----------------|
| 类型 | remote | remote |
| 流量 | 已用 ~20GB / 100GB | 已用 ~44.5GB / 200GB |
| 到期 | 2026-08-21 | 2026-11-14 |
| 当前节点 | JP-1 | 美国SG11 |
| 最后更新 | 2026-06-10 | 2026-06-10 |

## 诊断流程

1. `ps aux | grep verge` → 确认 3 进程(clash-verge, clash-verge-service, verge-mihomo)
2. `ss -tlnp | grep 7897` → 确认端口监听
3. `read_file profiles.yaml` → 检查流量和节点
4. `read_file verge.yaml` → 检查 external_controller 状态（默认 false）
5. `journalctl -u clash-verge-service -n 20` → 检查日志

## 安全策略注意事项

- `read_file` 优先于 `cat`/`grep`：直接访问配置文件
- `curl --proxy` 可能被安全策略拦截：改用 `read_file` 判断
- 不要访问 `clash-verge.yaml`（运行时完整配置），优先读 `profiles.yaml`

## verge.yaml 关键字段

| 字段 | 值 | 说明 |
|------|-----|------|
| enable_external_controller | false | 无 HTTP API |
| enable_tun_mode | false | TUN 未启用 |
| enable_system_proxy | true | 系统代理已开 |
| verge_mixed_port | 7897 | 混合代理端口 |
