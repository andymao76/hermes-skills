# A1 项目 JanusGraph 数据模型与查询 (苏丹谛听)

## 数据模型

| 元素 | 类型 | 说明 |
|------|------|------|
| `msisdn` | 顶点属性 | 号码（主标识） |
| `capturetime` | 顶点属性 | 捕获时间（Unix 秒） |
| `card_msisdn` | 顶点属性 | 卡片号码（复合键前缀） |
| `connect` | 边标签 | 通话/连接关系（双向） |
| `sourceno` | 边属性 | 局数据源编号（如 DST_014031） |
| `date` | 边属性 | 日期（如 20250620，整数格式） |
| `count` | 边属性 | 次数 |

## 服务地址

| 项目 | 值 |
|------|-----|
| Gremlin Server | rhino01 (215.152.1.11:8182) |
| Console 路径 | /home/websrv/janusgraph/bin/gremlin.sh |
| remote.yaml 配置 | conf/remote.yaml → hosts: [215.152.1.11] |

## 核心查询模式

```groovy
// 按号码+日期查边
g.V().has('msisdn','123355579').bothE().has('date',20241023)

// 按日期范围查顶点
g.V().has('capturetime',gt(1750291200))
     .has('capturetime',lte(1750377599))
     .limit(10).valueMap()

// 号码关联度树分析
g.V().has('msisdn',915637674).as('a')
  .bothE('connect').has('sourceno','DST_014031')
  .has('date',gte(20250903)).has('date',lte(20250909))
  .otherV().has('msisdn',without(915637674)).as('b')
  .tree().by(valueMap())

// 边+两端顶点详情
g.E().has('capturetime',gt(1750291200))
     .has('capturetime',lte(1750377599))
     .limit(10).project('edge','from','to')
     .by(valueMap()).by(outV().valueMap()).by(inV().valueMap())
```

## 运维命令

```bash
# 重启 Gremlin Server
ps -ef | grep gremlin | grep -v grep | awk '{print $2}' | xargs kill -9
export JANUSGRAPH_YAML=/home/websrv/janusgraph/conf/gremlin-server/socket-gremlin-server.yaml
./gremlin-server.sh start

# jansi 缺失修复
wget https://repo1.maven.org/maven2/org/fusesource/jansi/jansi/1.18/jansi-1.18.jar
cp jansi-1.18.jar /home/websrv/janusgraph/lib/
```
