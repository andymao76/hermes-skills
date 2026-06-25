# 自定义 Doris MCP 服务器（领域专用工具）

> 基于通用 `db_query_server.py` 的升级方案，封装 LI 领域专用的 MCP 工具集。
> 脚本路径：`~/.hermes/mcp-servers/doris_mcp_server.py`

## 工具清单

| 工具 | 功能 |
|------|------|
| `show_tables` | 列出当前库所有表 |
| `describe_table` | 查看表结构 |
| `query_sql` | 执行 SELECT 查询（含 limit 参数） |
| `explain_sql` | 查看查询执行计划 |
| `liid_summary` | 按 LIID 汇总：事件类型分布、时间范围、来源系统、MSISDN |
| `cdr_summary` | CDR 事件汇总（event_type 1/10/15 等呼叫相关类型） |
| `ipdr_summary` | IPDR 事件汇总（排除 CDR 类型的其余 event_type 自动归类） |

## 架构模式

```python
from mcp.server.fastmcp import FastMCP
import pymysql

mcp = FastMCP("doris-mcp-server")

@mcp.tool()
def some_tool(param: str) -> str:
    """工具描述"""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT ...", (param,))
            results = _rows_to_list(cur.fetchall())
        return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    finally:
        conn.close()
```

## 环境变量配置

```yaml
env:
  DORIS_HOST: '127.0.0.1'
  DORIS_PORT: '9030'
  DORIS_USER: 'root'
  DORIS_PASSWORD: 'your-password'
  DORIS_DATABASE: 'hermes_ai'
```

## 关键设计要点

1. **连接池不要**：MCP 工具每次调用独立建连/关连，FastMCP 的 stdio 模式已经是短连接
2. **异常安全**：每个工具必须用 try/finally 确保 conn.close()
3. **JSON 返回**：所有工具返回 JSON 字符串，便于 Hermes Agent 二次处理
4. **LIID 跨表查询**：`liid_summary` 自动扫描库中所有含 `liid` 列的表进行聚合
5. **CDR/IPDR 分类**：基于 event_type 值域区分（CDR=1/10/15，其余归 IPDR），可配置

## 添加至 Hermes

```bash
# 先用 hermes mcp add 添加
yes | hermes mcp add doris \
  --command /home/andymao/.hermes/venv/bin/python3 \
  --args /home/andymao/.hermes/mcp-servers/doris_mcp_server.py \
  --env DORIS_HOST=127.0.0.1 \
  --env DORIS_PORT=9030 \
  --env DORIS_USER=root \
  --env DORIS_PASSWORD=your-pass \
  --env DORIS_DATABASE=hermes_ai

# 然后用 hermes mcp rm 删除并手动写入 config.yaml 修复 env 格式
#（因为 --env 参数会被错误地写成 args 而非 env: dict）
```

详见主 SKILL.md 的 `hermes mcp add --env` 陷阱说明。
