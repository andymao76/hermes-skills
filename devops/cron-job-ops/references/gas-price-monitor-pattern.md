# no_agent 看门狗模式：价格/数值变化监控

适用于监控某个外部数值（油价、汇率、币价、温度阈值等），只在变化时推送提醒。

## 架构

```
cron (no_agent=true)
  │
  ├── script.sh               # 轮询脚本
  ├── ~/.gas_price_state       # 状态文件（记录上次值）
  └── stdout                   # → 仅变化时输出 → 自动投递
```

- `no_agent=true`：零 Token 开销，脚本 stdout 直接投递
- **相同值时静默**：脚本输出 `GAS_PRICE_SAME|...` 时 pipline 没有内容 → 用户看不到消息
- **变化时推送**：`GAS_PRICE_CHANGED|⚠️ 涨价了！` 或 `GAS_PRICE_CHANGED|✅ 降价了！`

## 状态文件模式

```bash
STATE_FILE="$HOME/.gas_price_state"

# 读取上次记录
last_price=""
if [ -f "$STATE_FILE" ]; then
    source "$STATE_FILE"
fi

# 对比
if [ "$(echo "$current > $last" | bc -l)" -eq 1 ]; then
    echo "GAS_PRICE_CHANGED|价格上涨: ..."
elif [ "$(echo "$current < $last" | bc -l)" -eq 1 ]; then
    echo "GAS_PRICE_CHANGED|价格下跌: ..."
fi

# 写入新状态
echo "last_price=\"$current\"" > "$STATE_FILE"
echo "last_date=\"$today\"" >> "$STATE_FILE"
```

## 从 HTML 提取数值

使用 `grep -A1` 模式（比正则更可靠，应对 HTML 换行）：

```bash
# HTML: <dt>南京95号汽油</dt><dd>8.85元/升</dd>
value=$(curl -s "$URL" | grep -A1 '南京95号汽油' | grep -oP '\d+\.\d+')
```

## 依赖检查

- `bc` — 浮点数比较必需。未安装时比较失败。
- `curl` — 绝大多数系统预装。
- 看门狗脚本启动时建议做依赖检查：

```bash
for cmd in bc curl; do
    if ! command -v $cmd &>/dev/null; then
        echo "WATCHDOG_FAIL|缺少依赖: $cmd"
        exit 1
    fi
done
```

## Cron 配置

```bash
# 创建
cronjob(action='create',
    name='监控任务名',
    schedule='0 9 * * *',
    script='monitor-script.sh',
    no_agent=true,
    deliver='origin')

# 验证
cronjob(action='run', job_id='...')
```

## 实战案例：95号汽油价格监控

**脚本位置：** `~/.hermes/scripts/gas-price-monitor.sh`

**功能：**
- 每日 9:00 抓取南京95号汽油价格
- 对比上期记录
- 涨价 → 推送「⚠️ 涨价了！赶快去加油」
- 降价 → 推送「✅ 降价了！可以去加油」
- 不变 → 静默

**特点：**
- 同时提取「下次调整日期」和「预计涨跌」信息 — 即使用户不提，也给了预告
- 数据源 `qiyoujiage.com` 使用 HTTP (非 HTTPS)，注意中间人风险。如需安全连接，改用中石化官方 API 或 HTTPS 站点。
- 状态文件 `~/.gas_price_state` 使用 `source` 加载，键值格式 `key="value"`
