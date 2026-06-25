# 多源运维文档调研工作流

> 基于 2026-06-07 会话中 HDFS/Hive/HBase/GP/ES/Kafka 运维文档的跨平台调研实践

## 调研流程

```
1. 确定调研主题 + 目标组件列表
2. 同时搜索 CSDN + 知乎 + Google
3. 提取代表性文章（3-5篇/组件）
4. 标注文章中可能过时/错误的内容
5. 交叉验证（Google 最新信息对照）
6. 整理输出到屏幕 + 知识库
```

## 组件搜索关键词模板

```
# 运维文档搜索
site:csdn.net <组件> 运维 故障 调优
site:zhihu.com <组件> 运维 踩坑 调优
<组件> common errors production troubleshooting 2026

# 交叉对比
<组件A> vs <组件B> comparison 2026
<组件> versus <替代品> 2026
```

## CSDN 搜索结果处理

- CSDN 页面反爬严重，`web_extract` 常超时或被拒
- **可用替代**: 通过 Google/Bing 搜索摘要获取元数据（标题、作者、热度）
- **需要跳过**: 2023年后 AI 生成/抄袭拼凑的文章（内容空洞，参数无版本标注）
- **Red flags**: 没写适用版本的、把厂商定制参数当 Apache 原生参数的、仍推荐 CMS/G1GC 的
- 优先选作者有实际生产经验的文章（腾讯云/阿里云/网易等背景）

## 过时知识筛选清单

| 类别 | 过时观点 | 2026年正确认知 |
|------|---------|---------------|
| HDFS | SecondaryNameNode 恢复 NN | HA + ZKFC 自动切换 |
| Hive | Metastore HA 用 ZK Leader 选举 | 无状态 + 负载均衡 |
| HBase | CMS GC | G1GC |
| HBase | Region 大小固定 1MB | 动态调整 |
| Greenplum | Resource Queue | Resource Group (GP7 已废弃 RQ) |
| GP | `gprecoverseg -r` | `-s` (GP7) |
| ES | `discovery.zen` | Raft (ES 8.x) |
| Kafka | `--zookeeper` 参数 | `--bootstrap-server` + KRaft |
| Kafka | RangeAssignor 默认 | StickyAssignor (2.4+) |

## 输出格式

为后续知识库归档，保持每份调研产物统一格式：

1. **文档头部**: 日期、数据源列表、组件范围
2. **各组件小节**: 
   - `🔴 高危错误`（严重过时/错误信息）
   - `🟡 中等过时`（版本未更新、参数默认值改变）
   - `🟢 系统性缺失`（新特性未覆盖）
3. **跨组件共性问题**: 如"版本不标注"、"AI抄袭拼凑"、"CMS推荐"
4. **平台评估**: 各平台（CSDN/知乎/Google）的可用性和质量评分

## 英文术语产出

每份调研文档末尾提供英文术语对照表及授课例句，方便用户在国外客户交流中使用。

## 参考

- 本地知识库 `bigdata-ops-docs-errors-review.md` — 6组件错误汇总
- 本地知识库 `bigdata-component-cross-comparison-2026.md` — 交叉对比 + 14条无效知识
