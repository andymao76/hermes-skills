# Open WebUI 默认模型持久化

## 问题

Open WebUI 启动后如果没有环境变量 `OPENAI_API_BASE_URLS`，外部连接会丢失。
但默认模型（初始对话时自动选中的模型）可以通过数据库持久化。

## DB 写入默认模型

```bash
python3 -c "
import sqlite3, json
db = sqlite3.connect('/path/to/webui.db')
row = db.execute('SELECT id, data FROM config WHERE id = 1').fetchone()
config = json.loads(row[1])
config['default_models'] = 'deepseek-chat'
new_val = json.dumps(config)
db.execute('UPDATE config SET data = ? WHERE id = 1', (new_val,))
db.commit()
"
```

## 关键点

- `data` 列是 JSON 格式，不是字符串
- `default_models` 是逗号分隔的模型 ID（单模型也可以直接写）
- 需要重启 Open WebUI 才能生效
- 外部连接（API URL + Key）仍然在运行时加载，不能用 DB 持久化
- 必须用 `open-webui.sh start`（它会自动通过 API 配置外部连接）或环境变量方式启动

## 相关表结构

Table: `config`
| Column | Type | 说明 |
|--------|------|------|
| id | INTEGER | 1 (单行) |
| data | JSON | 配置数据 |
| version | INTEGER | 版本号 |
| created_at | DATETIME | |
| updated_at | DATETIME | |
