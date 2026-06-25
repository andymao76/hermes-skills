# OWLS WEB-UI 调试参考 (A1 项目)

## 系统信息

| 项目 | 值 |
|------|-----|
| Web 服务器 | rhino04 (215.152.1.11) |
| Web 端口 | 8899 |
| 服务路径 | /home/websrv/listener-web-1.0 |
| API 前缀 | /listener-server/ |
| 后端框架 | Spring Boot (http-nio-8899-exec) |
| 前端框架 | Vue.js |
| 日志关键词 | TmcRequestPrint |

## 常见 API 端点

| 端点 | 说明 |
|------|------|
| `/listener-server/targetQueryMgmt/detailQuery` | 明细查询 |
| `/listener-server/targetQueryMgmt/...` | 目标查询相关 |
| `/listener-server/...` | OWLS 后端接口 |

## 调用链示例

从 DevTools → Initiator 读取（由下往上）：

```
Promise.then
  Dr @ request.ts:107          ← Axios 发请求
  s  @ targetQuery.ts:24       ← 封装查询参数
  Pe @ middle.vue:1056         ← 中间处理
  be @ QTable.vue:537          ← 表格组件触发
```

## WEB LOG 关联分析

```bash
# 在 rhino04 搜索日志
ssh 215.152.1.11
grep "detailQuery" /home/websrv/listener-web-1.0/logs/*.log | tail -20
```

## 数据库验证

从 Payload 提取 tid + mapId 后查 Greenplum：

```sql
-- 查命中表
SELECT * FROM hts_lig_hi2 WHERE tid = '<tid>' AND clue_id = <mapId>;

-- 查字段映射
SELECT * FROM rds_source_define WHERE sourceno = '<tableName>';
```
