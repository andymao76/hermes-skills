# No-Agent 退出码速查表

## `daily-startup-healthcheck.sh`

| 退出码 | 含义 | 诊断 |
|--------|------|------|
| 0 | 全部通过 | — |
| 1 | 1个警告（如某个provider返回429/502/400） | `bash ~/.hermes/scripts/daily-startup-healthcheck.sh` 查看详情 |
| 10+ | 致命错误（Clash未运行、代理端口不通、Key过期） | 按脚本输出的 ❌ 项逐条排查 |

## `daily-system-maintenance.sh`

| 退出码 | 含义 |
|--------|------|
| 0 | 全部通过 |
| 非0 | 有残留进程/日志未清理/磁盘不足 |

## `tavily-watchdog.sh`

| 退出码 | 含义 |
|--------|------|
| 0 | 配额充足 |
| 1 | 配额<100（警告） |
| 2 | 配额<50（紧急） |

## 通用编码模式

```bash
# 推荐：分级编码
exit $((FATAL * 10 + WARN))

# 按位数分离解读：
# 十位数 = FATAL 计数
# 个位数 = WARN 计数
# exit 1  ≠ 真故障，exit 10+ = 需要人工处理
```
