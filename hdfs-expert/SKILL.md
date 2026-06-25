---
name: hdfs-expert
description: HDFS 存储专家 — Missing/Corrupt Blocks 修复/Safe Mode 管理/NameNode HA 故障转移/JournalNode 状态检查/磁盘均衡/DataNode 管理
priority: high
category: bigdata
---

# HDFS Expert

HDFS 存储专家技能 — 覆盖 HDFS 运维核心场景：块修复、安全模式诊断、NN HA 切换、JournalNode 检查、磁盘均衡、DataNode 生命周期管理。

## 前置检查

所有操作前先确认：
- Hadoop 命令在 PATH 中（`which hdfs`），或 `source /etc/profile` / `export HADOOP_HOME=/path`
- 当前用户有 HDFS 超级用户权限（通常为 `hdfs` 用户，或 `sudo -u hdfs`）
- NameNode 服务状态（`hdfs haadmin -getServiceState nn1`）

## 0. HDFS 核心架构与角色职责

| 组件 | 角色 | 职责 | 关键配置 |
|------|------|------|----------|
| **NameNode (NN)** | Master — 元数据服务器 | 管理文件系统命名空间、维护 FsImage + Edits Log、处理客户端读写请求、控制 Block 副本放置策略 | `dfs.namenode.name.dir`、`dfs.namenode.checkpoint.dir` |
| **Standby NameNode** | 热备 | 通过 JournalNode 同步 Edits Log、保持内存元数据与 Active 一致、在 Active 故障时接管 | 同 Active NN 配置 + HA 相关参数 |
| **DataNode (DN)** | Worker — 数据存储 | 存储 Block 数据与校验和、定期向 NN 发送心跳和 BlockReport、执行 Block 复制/删除/均衡指令 | `dfs.datanode.data.dir`、`dfs.datanode.balance.bandwidthPerSec` |
| **JournalNode (JN)** | 日志仲裁集群 | 存储 Active NN 产生的 Edits Log、为 Standby NN 提供日志同步、奇数节点组成 Quorum（≥3 台，容忍 floor(n/2) 故障） | `dfs.journalnode.edits.dir`、`dfs.journalnode.rpc-address` |
| **ZKFailoverController (ZKFC)** | HA 控制器 | 监控 NN 健康、通过 ZooKeeper 选主、触发 fencing 和故障转移 | ZK quorum 地址、session 超时 |
| **HttpFS** | 网关代理 | 提供 REST API 访问 HDFS，适合跨网络或防火墙场景 | HttpFS 端口 (默认 14000) |
| **NFS Gateway** | NFS 桥接 | 通过 NFS v3 协议挂载 HDFS，支持 POSIX 兼容访问 | `nfs.exports.allowed.hosts` |
| **Balancer** | 均衡工具 | 在 DataNode 间移动 Block 以均衡磁盘使用率 | `dfs.datanode.balance.bandwidthPerSec` |
| **Disk Balancer (HDFS 3.x)** | 盘级均衡 | 在同一 DataNode 的多个磁盘间均衡数据分布 | `dfs.disk.balancer.enabled`、`dfs.disk.balancer.max.disk.throughputInMBperSec` |
| **Secondary NameNode (2.x)** | 检查点辅助 | 合并 FsImage 和 Edits Log（Hadoop 2.x 及之前；HA 下由 Standby NN 替代） | `dfs.namenode.checkpoint.period` |

### Block 放置策略

| 副本数 | 策略 | 说明 |
|--------|------|------|
| 第 1 副本 | 本地机架优先 | 写客户端所在机架（若 DN 在集群外则随机） |
| 第 2 副本 | 跨机架 | 与第 1 副本不同机架，保证机架级容错 |
| 第 3 副本 | 同机架不同节点 | 与第 2 副本同一机架的不同 DN，减少跨机架写带宽 |
| 第 4+ 副本 | 随机放置 | 均匀分布在集群中 |

`dfs.block.replicator.classname` 可自定义放置策略，默认 `BlockPlacementPolicyDefault`。

## 1. 基础诊断命令

| 命令 | 用途 |
|------|------|
| `hdfs dfsadmin -report` | 集群概览：总容量、已用、剩余、DataNode 列表及状态 |
| `hdfs dfsadmin -report -live` | 仅 Live DataNode |
| `hdfs dfsadmin -report -dead` | 仅 Dead DataNode |
| `hdfs dfsadmin -report -decommissioning` | 正在退役的节点 |
| `hdfs dfsadmin -metasave /tmp/metasave.txt` | 将 NN 内存中 block 信息导出到文件（含 pending replication, corrupt blocks 等） |
| `hdfs fsck / -files -blocks` | 文件系统完整性检查，显示每个文件的 block 状态 |
| `hdfs fsck / -files -blocks -locations` | 同上 + block 物理位置 |
| `hdfs fsck / -list-corruptfileblocks` | 列出所有 corrupt block 对应的文件 |
| `hdfs fsck / -blocks -locations -racks` | 块位置 + 机架信息（含副本数） |
| `hdfs fsck PATH -move` | 检查并对缺失块执行移动修复 |
| `hdfs fsck PATH -delete` | 检查并删除损坏文件 |

### 1.1 扩展诊断命令

| 命令 | 用途 |
|------|------|
| `hdfs dfsadmin -printTopology` | 打印机架拓扑结构 |
| `hdfs dfsadmin -allowSnapshot <path>` | 允许某目录做快照（用于数据保护） |
| `hdfs dfsadmin -disallowSnapshot <path>` | 禁止快照 |
| `hdfs dfsadmin -fetchImage /tmp/fsimage` | 从 NN 拉取最新的 FsImage |
| `hdfs dfsadmin -rollingUpgrade <action>` | 滚动升级状态查询 |
| `hdfs namenode -recover -force` | 恢复 NameNode（从 FsImage + Edits Log） |
| `hdfs dfs -df -h /` | 查看 HDFS 整体空间使用率 |
| `hdfs dfs -du -h /` | 逐级查看目录使用量 |
| `hdfs dfs -count -q /` | 查看配额（空间配额和文件数） |
| `hdfs dfsadmin -setQuota <limit> <dir>` | 设置目录空间配额（字节） |
| `hdfs dfsadmin -clrQuota <dir>` | 清除目录配额 |

## 2. Safe Mode（安全模式）管理

### 2.1 诊断当前状态
```bash
hdfs dfsadmin -safemode get
```
输出 `Safe mode is ON` 或 `Safe mode is OFF`。附带阈值信息：
```
Safe mode is ON. Entered at 2025-01-15 10:30:00. Reached threshold blocks 0.999f. 
Current threshold blocks: 0.999f. Min replication required: 1.
```

### 2.2 进入 Safe Mode 的常见原因

| 原因 | 诊断方法 | 处理 |
|------|---------|------|
| NameNode 启动（正常） | `safe mode is ON. The ratio of reported blocks 0.0000 has not reached the threshold` | 等待 DataNode 上报完毕，自动退出 |
| Block 大量丢失/副本不足 | `reported blocks` 长期未达阈值 | fsck 定位缺失→修复 |
| 磁盘写满 | `df -h` 检查 NN/DataNode 磁盘 | 清理或扩容 |
| 升级（Upgrade） | `hdfs dfsadmin -upgradeProgress status` | 按升级流程处理 |
| 手动进入 | `hdfs dfsadmin -safemode enter` 被运维执行 | 确认后手动 leave |

### 2.3 退出 Safe Mode
```bash
# 正常退出（需块上报达到阈值）
hdfs dfsadmin -safemode leave

# 强制退出（危险！可能导致数据不一致）
hdfs dfsadmin -safemode forceExit
```

### 2.4 自动退出条件
NameNode 在下列条件同时满足时自动退出 Safe Mode：
1. **块上报比例** ≥ `dfs.namenode.safemode.threshold-pct`（默认 0.999，即 99.9% 的块已上报）
2. **满足最小副本要求的块数** ≥ `dfs.namenode.replication.min`（默认 1）
3. **DataNode 心跳正常** — 已存活 DataNode 持续汇报心跳

查看当前阈值：
```bash
hdfs getconf -confKey dfs.namenode.safemode.threshold-pct
hdfs getconf -confKey dfs.namenode.replication.min
```

### 2.5 Safe Mode 强制退出的时机
仅当确认以下情况时考虑 forceExit：

- 测试环境，数据可丢弃
- 部分 DataNode 永久离线且数据已有冷备
- 紧急恢复后需手动接管检查

**安全做法**：先用 `hdfs dfsadmin -safemode leave`，仍然不行再排查块问题。

## 3. Missing Blocks 修复

### 3.1 定位缺失块
```bash
# 运行完整 fsck，查找所有块的缺失和复制不足
hdfs fsck / -files -blocks 2>&1 | grep -E "MISSING|UNDER_REPLICATED|CORRUPT"

# 获取简单的总体统计
hdfs fsck / -files -blocks 2>&1 | tail -20
```

### 3.2 修复 Missing Blocks

**方案 A：文件有副本可用，仅需补副本**
```bash
# 对有问题的文件设置副本数（触发自动复制）
hdfs dfs -setrep -R -w 3 /path/to/directory

# 或单个文件
hdfs dfs -setrep 3 /user/hive/warehouse/table_name/file.parquet
```
选项：
- `-R`：递归处理目录
- `-w`：等待复制完成才返回

**方案 B：文件还在写（lease 未释放）**
```bash
# 恢复 lease（强制解除）
hdfs debug recoverLease -path /path/to/file -retries 10

# 然后检查
hdfs fsck /path/to/file
```

**方案 C：源文件已不可恢复，删除损坏文件**
```bash
# 或通过 fsck 删除
hdfs fsck /path/to/file -delete
```

### 3.3 验证修复
```bash
hdfs fsck / -files -blocks 2>&1 | tail -5
```
期望输出应有 `Status: HEALTHY`，无 MISSING 或 CORRUPT 告警。

## 4. Corrupt Blocks 修复

### 4.1 查看 corrupt block 列表
```bash
hdfs fsck / -list-corruptfileblocks
```
输出格式：`/path/to/file  BlockID: blk_123456789  Expected block replica count: 3  Corrupt replicas: 0/1`

### 4.2 确认副本位置
```bash
# 查看具体块的位置
hdfs fsck /path/to/file -files -blocks -locations

# 在 DataNode 上手动检查块文件校验和
hdfs fsck /path/to/file -files -blocks -locations | grep blk_123456789
```

### 4.3 修复方案

**方案 A：从健康副本恢复**
```bash
# 触发复制（如果还有健康副本，NN 会自动调度）
hdfs debug recoverLease -path /path/to/file -retries 5
hdfs dfs -setrep 3 /path/to/file
```

**方案 B：主动删除 corrupt 块（当健康副本 ≥ 安全阈值时）**
```bash
# fsck 自动删除 corrupt 块文件（但不删除文件元数据）
hdfs fsck / -delete
```
注意：-delete 会删除 corrupt block，不是删文件。文件 metadata 保留，健康副本仍可读。

**方案 C：手动复制健康副本**
如果知道哪个 DataNode 有健康副本：
```bash
# 确定健康 DataNode 上的块文件路径
# 然后 scp/hdfs dfs -cp 到目标 DataNode 同名路径
# 最后让 NN 重新识别
hdfs dfsadmin -triggerBlockReport <dn_hostname>:<port>
```

### 4.4 批量修复脚本
```bash
#!/bin/bash
# 自动遍历所有 corrupt 文件并尝试修复
hdfs fsck / -list-corruptfileblocks 2>/dev/null | grep "^/" | while read filepath; do
  echo "Repairing: $filepath"
  sudo -u hdfs hdfs dfs -setrep 3 "$filepath"
done
```

## 5. NameNode HA 管理

### 5.1 查看 NN HA 状态
```bash
# 查看两个 NN 的状态
hdfs haadmin -getServiceState nn1
hdfs haadmin -getServiceState nn2
```
输出：`active` 或 `standby`

### 5.2 故障转移（Failover）
```bash
# 手动触发 Active→Standby 切换
hdfs haadmin -transitionToActive nn2
hdfs haadmin -transitionToStandby nn1

# 如果标注为 "forced"（跳过 fencing）
hdfs haadmin -transitionToActive --forcemanual nn2
```

### 5.3 检查 HA 健康
```bash
# 检查两个 NN 是否为 healthy
hdfs haadmin -checkHealth nn1
hdfs haadmin -checkHealth nn2

# 或通过 JMX
curl -s http://nn1-host:50070/jmx?qry=Hadoop:service=NameNode,name=NameNodeStatus
curl -s http://nn2-host:50070/jmx?qry=Hadoop:service=NameNode,name=NameNodeStatus
```

### 5.4 HA fencing 机制
当 NN 故障时，fencing 确保旧 Active 停止服务：
- **SSH fencing**: `ssh -o StrictHostKeyChecking=no <active_nn> "kill -9 <nn_pid>"`
- **shell fencing**: 执行自定义脚本
- **HDFS fencing**: `hdfs haadmin -transitionToStandby`

检查 fencing 配置：
```bash
hdfs getconf -confKey dfs.ha.fencing.methods
```

### 5.5 HA 故障排查
| 现象 | 可能原因 | 检查点 |
|------|----------|--------|
| 两个 NN 都是 Standby | 脑裂防护触发或 JN 异常 | 检查 JN 和 fencing 日志 |
| Failover 失败 | Fencing 未执行或超时 | `hdfs haadmin -checkHealth` |
| 切换后 client 连接失败 | RPC 客户端缓存旧 NN 地址 | `hdfs dfs -ls /` 验证，重配 client |
| ZKFC 频繁切换 | GC Pause 或网络抖动导致 ZK Session 超时 | 调大 `dfs.ha.zk.session-timeout.ms` |
| Active NN 进程未退出但变成 Standby | 脑裂被 fencing 触发 | 检查 fence 日志确认原因 |

## 6. JournalNode 状态检查

### 6.1 检查 JournalNode 进程
```bash
# 在所有 JN 节点上
sudo -u hdfs hdfs journalnode -format  # 首次格式化
systemctl status hadoop-hdfs-journalnode
journalctl -u hadoop-hdfs-journalnode -n 50 --no-pager
```

### 6.2 检查 QJournal 协议状态
```bash
# 从 Active NN 查看 edit log 同步状态
hdfs haadmin -getServiceState nn1

# 检查 JN 上 edit log 的同步情况
curl -s "http://jn1-host:8480/journal?service=hdfsHA&journal=edits_123456" | head -5

# 检查 EditLog Tailer（Standby NN 跟踪进度）
hdfs namenode -getCorruptEditLogs -outputDir /tmp/
```

### 6.3 常见 JN 问题
| 问题 | 症状 | 处理 |
|------|------|------|
| JN 宕机 | Active NN 日志 `QuorumJournalManager` 写超时 | 重启 JN 服务 |
| JN 磁盘写满 | Edit log 写入失败 | 清理 JN 数据目录老 edit log |
| Sync 超时 | 集群压力大，write.committing 延迟 | 增加 `dfs.journalnode.edit-cache-size.bytes` |
| Quorum 丢失 | 半数以上 JN 不可用，HA 降级 | 恢复至少半数 JN 节点 |

### 6.4 查看 edit log 事务数
```bash
# 从 JN http 接口
curl -s "http://jn1-host:8480/getJournal?"
# 或 JN 统计日志
grep "synced" /var/log/hadoop-hdfs/hadoop-hdfs-journalnode-*.log
```

### 6.5 强制格式化 JN（灾难恢复）
```bash
# 在 HA 完全不可恢复时
# 1. 停止所有 NN 和 JN
# 2. 在存活 NN 执行 format（会生成新的 Namespace ID）
hdfs namenode -format -force -clusterId <cluster_id>

# 3. 格式化 JN（--force 跳过版本检查）
hdfs journalnode -format -force

# 4. 用存活 NN 自举
hdfs namenode -bootstrapStandby -force
hdfs namenode -initializeSharedEdits -force
```
⚠ 这会清空所有 edit log 历史，仅作最后手段。

## 7. DataNode 管理

### 7.1 查看 DataNode 状态
```bash
# 完整报表
hdfs dfsadmin -report

# 仅 Decommission 状态
hdfs dfsadmin -report -decommissioning

# 单个 DataNode 指标
hdfs dfsadmin -getDatanodeInfo <datanode_hostname>:50010
```

### 7.2 DataNode 退役（Decommission）
```bash
# 1. 将 DataNode hostname 加入 exclude 文件
echo "datanode-hostname" >> /etc/hadoop/conf/dfs.hosts.exclude

# 2. 刷新 NN 配置（触发退役过程）
hdfs dfsadmin -refreshNodes

# 3. 监控退役进度
hdfs dfsadmin -report -decommissioning
# 当状态从 Decommission In Progress → Decommissioned 完成
```
退役等待时间取决于：
- block 数量和数据量
- `dfs.namenode.decommission.blocks.per.interval`（默认 24/h）
- 网络带宽

### 7.3 DataNode 重新加入
```bash
# 从 exclude 文件移除 hostname，然后
hdfs dfsadmin -refreshNodes
# DN 状态变为 Normal
```

### 7.4 添加新 DataNode
```bash
# 1. 确保新节点在 include 文件中
echo "new-dn-hostname" >> /etc/hadoop/conf/dfs.hosts

# 2. 在 NN 刷新
hdfs dfsadmin -refreshNodes

# 3. 新节点启动
systemctl start hadoop-hdfs-datanode
```

### 7.5 DataNode 拓扑感知 — 配置机架
```bash
# 自定义机架脚本
# /etc/hadoop/conf/topology.py
# 返回机架路径，如 /default-rack
hdfs dfsadmin -printTopology
```

## 8. 磁盘均衡（Balancer）

### 8.1 查看磁盘使用不均衡
```bash
hdfs dfsadmin -report | grep -E "(Configured Capacity|DFS Used|DFS Remaining|Hostname)"
```
对比各 DataNode 的使用率，偏差 > 10% 通常需要均衡。

### 8.2 启动 Balancer
```bash
# 基本用法
hdfs balancer

# 调整阈值（默认 10%，表示集群内各 DN 使用率偏差不超过 10%）
hdfs balancer -threshold 5

# 指定 DataNode 集合（使用策略）
hdfs balancer -policy datanode

# 指定带宽限制（默认 20 MB/s）
hdfs balancer -bandwidth 10485760  # 10 MB/s 单位 bytes/s
```

### 8.3 Balancer 参数调优

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `dfs.datanode.balance.bandwidthPerSec` | 单个 DN 均衡带宽上限 | `10485760` (10MB/s) |
| `dfs.balancer.dispatcherThreads` | 调度线程数 | 200 |
| `dfs.balancer.movedWinWidth` | 移动窗口宽度 | 5400000ms (90min) |
| `dfs.balancer.max-size-to-move` | 单次移动最大字节 | 10GB |

调整带宽：
```bash
# 动态调整（不需要重启）
hdfs dfsadmin -setBalancerBandwidth 20971520  # 20 MB/s
```

### 8.4 Balancer 运行策略
```bash
# 按节点池平衡
hdfs balancer -pool <pool_name>

# 排除某些 DataNode
hdfs balancer -exclude <datanode1>,<datanode2>

# 只对指定机架均衡
hdfs balancer -include -f <rack_list_file>
```

### 8.5 监控 Balancer 进度
```bash
# Balancer 日志
tail -f /var/log/hadoop-hdfs/hadoop-hdfs-balancer-*.log

# 通过 JMX
curl -s http://balancer-host:50070/jmx | grep -i balancer

# 输出示例：
# Time Stamp               Iteration#  Bytes Already Moved  Bytes Left To Move  Bytes Being Moved
# 2025-01-15 11:00:00      1           1.2 TB               0.8 TB              50 GB
```

### 8.6 HDFS 3.x Disk Balancer（盘级均衡）

Disk Balancer 解决同一 DataNode 内各磁盘间使用不均的问题，与节点级的 Balancer 互补。

```bash
# 1. 检查是否启用
hdfs getconf -confKey dfs.disk.balancer.enabled

# 2. 生成磁盘均衡计划
hdfs diskbalancer -plan <datanode_hostname>
# 输出计划 JSON 文件路径

# 3. 执行计划
hdfs diskbalancer -execute <plan.json>

# 4. 查询状态
hdfs diskbalancer -query <datanode_hostname>

# 5. 取消执行
hdfs diskbalancer -cancel <plan.json>

# 6. 强制重新生成计划（跳过读取阈值检查）
hdfs diskbalancer -plan <datanode_hostname> -force
```

| Disk Balancer 参数 | 说明 | 默认值 |
|--------------------|------|--------|
| `dfs.disk.balancer.enabled` | 启用 Disk Balancer | `true` |
| `dfs.disk.balancer.max.disk.throughputInMBperSec` | 单盘最大吞吐 MB/s | `10` |
| `dfs.disk.balancer.plan.valid.interval` | 计划有效时长 | `1d` |
| `dfs.disk.balancer.block.tolerance.percent` | 块移动容忍百分比 | `10` |

### 8.7 使用 DistCp 做跨集群数据复制（辅助均衡）

```bash
# 跨集群复制（迁移/备份）
hadoop distcp hdfs://source-nn:8020/data hdfs://target-nn:8020/data

# 限带宽复制
hadoop distcp -bandwidth 50 hdfs://source:8020/data hdfs://target:8020/data

# 增量复制（只复制修改过的文件）
hadoop distcp -update -diff hdfs://source:8020/data hdfs://target:8020/data

# 删除目标端多余文件（保持镜像一致）
hadoop distcp -update -delete hdfs://source:8020/data hdfs://target:8020/data

# 动态文件列表
hadoop distcp -f /tmp/file_list.txt hdfs://target:8020/data/

# 忽略失败继续执行
hadoop distcp -i hdfs://source:8020/data hdfs://target:8020/data
```

| DistCp 参数 | 说明 |
|-------------|------|
| `-m <num>` | 最大 map 数（默认 20，调大可加速但增加 NN 压力） |
| `-bandwidth <MB>` | 每 map 带宽限制 |
| `-update` | 只复制源端更新的文件 |
| `-diff` | 基于 snapshot 做差量同步（HDFS 2.6+） |
| `-delete` | 删除目标端多余的文件 |
| `-i` | 忽略部分失败，继续复制 |
| `-p` | 保留权限、属主、时间戳等属性 |
| `-strategy dynamic` | 动态分片策略，适合大量小文件 |

## 9. 常见场景速查

### 场景 1：集群启动后卡在 Safe Mode
```bash
hdfs dfsadmin -safemode get
# Safe mode is ON. 块上报率低 → 检查 DataNode 是否启动
# 确认 DataNode 进程存活，检查 NN 日志是否有连接异常
hdfs dfsadmin -report | head -20
```

### 场景 2：部分文件无法读取
```bash
hdfs fsck / -list-corruptfileblocks | head -20
# 确定是哪些文件
# 对重要文件尝试 setrep 恢复
# 对可丢弃文件使用 -delete
```

### 场景 3：NN HA 不能自动切换
```bash
hdfs haadmin -getServiceState nn1
hdfs haadmin -getServiceState nn2
# 检查 ZKFC (Zookeeper Failover Controller) 是否运行
ps aux | grep ZKFC
systemctl status hadoop-hdfs-zkfc
```

### 场景 4：DataNode 磁盘写满
```bash
df -h /data/hdfs/dn
# 清理无用数据
hdfs dfs -du -h / | sort -rh | head -20
# 或加盘扩容更彻底
```

### 场景 5：Balancer 不均衡
```bash
# 检查 Datanode 使用率分布
hdfs dfsadmin -report | grep -E "(Hostname|DFS Used%)"
# 调低阈值
hdfs balancer -threshold 3 -bandwidth 20971520
```

### 场景 6：FsImage Loading 过慢导致 NN 启动超时
```bash
# 查看 NN 启动日志中的 FsImage 加载时间
grep "loadFSImage" /var/log/hadoop-hdfs/hadoop-hdfs-namenode-*.log
# 查看 checkpoint 时间和大小
ls -lh /dfs/nn/current/fsimage_*
# 优化手段：压缩（使用 -Dfs.image.compress=true）、增加 NN 内存、减少目录数（小文件治理）
```

## 10. 关键配置参数调优表

### 10.1 NameNode 配置

| 参数 | 说明 | 推荐值 | 调优方向 |
|------|------|--------|----------|
| `dfs.namenode.handler.count` | NN 服务线程数 | `20 * log2(集群节点数)` | 提升并发请求处理能力 |
| `dfs.namenode.service.handler.count` | 服务 RPC handler | 通常 = handler.count | 和 handler.count 一致即可 |
| `dfs.namenode.name.dir` | 元数据存储路径（多路径镜像） | `/data1/dfs/nn,/data2/dfs/nn` | 至少 2 个不同物理盘做镜像 |
| `dfs.namenode.checkpoint.dir` | Standby NN 的检查点目录 | `/data1/dfs/namesecondary` | 需足够磁盘空间 |
| `dfs.namenode.safemode.threshold-pct` | Safe Mode 退出阈值 | `0.999f` | 小集群可调低至 0.99f 加速启动 |
| `dfs.namenode.replication.work.multiplier.per.iteration` | 每次迭代副本复制数 | `2` | 集群恢复时可提高 |
| `dfs.namenode.replication.max-streams` | 单个 DN 最大复制流 | `2` | 网络充裕时可提升至 8-10 |
| `dfs.namenode.avoid.write.stale.datanode` | 是否避免写过期 DN | `true` | 避免写入慢 DN |
| `dfs.namenode.stale.datanode.interval` | DN 过期判定时间(ms) | `30000` (30s) | 网络抖动时适当增大 |

### 10.2 DataNode 配置

| 参数 | 说明 | 推荐值 | 调优方向 |
|------|------|--------|----------|
| `dfs.datanode.data.dir` | 数据存储路径（逗号分隔） | `/data1/dfs/dn,/data2/dfs/dn` | 多盘分散 IO |
| `dfs.datanode.balance.bandwidthPerSec` | Balancer 带宽 | `10485760` (10MB/s) | 业务低峰期可调至 50-100MB |
| `dfs.datanode.handler.count` | DN 处理线程数 | `10` | 高并发时调大 |
| `dfs.datanode.max.transfer.threads` | DN 传输线程上限 | `4096` | 大集群适当增大 |
| `dfs.datanode.socket.write.timeout` | 写入超时(ms) | `480000` | 长尾写调大 |
| `dfs.datanode.du.plugins` | 磁盘使用检查插件 | `org.apache.hadoop.hdfs.server.datanode.fsdataset.impl.AvailableSpaceVolumeChoosingPolicy` | 多盘场景启用 |
| `dfs.datanode.fsdataset.volume.choosing.policy` | 卷选择策略 | `org.apache.hadoop.hdfs.server.datanode.fsdataset.impl.RoundRobinVolumeChoosingPolicy` | 写分布均衡 |

### 10.3 JournalNode 配置

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `dfs.journalnode.edits.dir` | JN 数据存储目录 | `/data/jn/edits` |
| `dfs.journalnode.rpc-address` | JN RPC 地址 | `0.0.0.0:8485` |
| `dfs.journalnode.http-address` | JN HTTP 地址 | `0.0.0.0:8480` |
| `dfs.journalnode.edit-cache-size.bytes` | Edit Log 缓存大小 | `524288` (512KB) |
| `dfs.qjournal.write-txns-timeout.ms` | QJM 写入超时 | `60000` (60s) |
| `dfs.qjournal.queued-edits.limit` | JN 缓冲 edist 数量 | `500000` |

### 10.4 网络与 IO 配置

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `dfs.datanode.socket.write.timeout` | 写 Socket 超时 | `480000` (8min) |
| `dfs.datanode.socket.read.timeout` | 读 Socket 超时 | `60000` (60s) |
| `dfs.client.socket-timeout` | 客户端 Socket 超时 | `60000` (60s) |
| `dfs.client.block.write.retries` | 块写重试次数 | `3` |
| `dfs.client.block.write.replace-datanode-on-failure.enable` | 写失败时替换 DN | `true` |
| `dfs.client.block.write.replace-datanode-on-failure.policy` | 替换策略 | `DEFAULT` |
| `ipc.client.connect.max.retries` | IPC 连接最大重试 | `50` |

## 11. HA 配置完整 XML 模板

```xml
<!-- core-site.xml -->
<configuration>
  <property>
    <name>fs.defaultFS</name>
    <value>hdfs://mycluster</value>
  </property>
  <property>
    <name>ha.zookeeper.quorum</name>
    <value>zk1:2181,zk2:2181,zk3:2181</value>
  </property>
</configuration>

<!-- hdfs-site.xml -->
<configuration>
  <!-- 基本设置 -->
  <property>
    <name>dfs.replication</name>
    <value>3</value>
  </property>
  <property>
    <name>dfs.namenode.safemode.threshold-pct</name>
    <value>0.999f</value>
  </property>

  <!-- Nameservice 定义 -->
  <property>
    <name>dfs.nameservices</name>
    <value>mycluster</value>
  </property>
  <property>
    <name>dfs.ha.namenodes.mycluster</name>
    <value>nn1,nn2</value>
  </property>

  <!-- NN RPC 和 HTTP 地址 -->
  <property>
    <name>dfs.namenode.rpc-address.mycluster.nn1</name>
    <value>nn1-host:8020</value>
  </property>
  <property>
    <name>dfs.namenode.rpc-address.mycluster.nn2</name>
    <value>nn2-host:8020</value>
  </property>
  <property>
    <name>dfs.namenode.http-address.mycluster.nn1</name>
    <value>nn1-host:50070</value>
  </property>
  <property>
    <name>dfs.namenode.http-address.mycluster.nn2</name>
    <value>nn2-host:50070</value>
  </property>

  <!-- JournalNode 共享 Edits -->
  <property>
    <name>dfs.namenode.shared.edits.dir</name>
    <value>qjournal://jn1:8485;jn2:8485;jn3:8485/mycluster</value>
  </property>

  <!-- HA 客户端自动故障转移 -->
  <property>
    <name>dfs.client.failover.proxy.provider.mycluster</name>
    <value>org.apache.hadoop.hdfs.server.namenode.ha.ConfiguredFailoverProxyProvider</value>
  </property>

  <!-- Fencing 机制 -->
  <property>
    <name>dfs.ha.fencing.methods</name>
    <value>sshfence</value>
  </property>
  <property>
    <name>dfs.ha.fencing.ssh.private-key-files</name>
    <value>/home/hdfs/.ssh/id_rsa</value>
  </property>

  <!-- ZKFC 自动故障转移 -->
  <property>
    <name>dfs.ha.automatic-failover.enabled</name>
    <value>true</value>
  </property>

  <!-- 自动故障转移 ZooKeeper -->
  <property>
    <name>dfs.client.failover.connection.retries.on.timeouts</name>
    <value>3</value>
  </property>

  <!-- Block 放置策略 -->
  <property>
    <name>dfs.block.replicator.classname</name>
    <value>org.apache.hadoop.hdfs.server.blockmanagement.BlockPlacementPolicyDefault</value>
  </property>

  <!-- 路径 -->
  <property>
    <name>dfs.namenode.name.dir</name>
    <value>/data/dfs/nn</value>
  </property>
  <property>
    <name>dfs.datanode.data.dir</name>
    <value>/data/dfs/dn</value>
  </property>
  <property>
    <name>dfs.journalnode.edits.dir</name>
    <value>/data/dfs/jn</value>
  </property>

  <!-- 安全模式 -->
  <property>
    <name>dfs.namenode.safemode.threshold-pct</name>
    <value>0.999f</value>
  </property>

  <!-- Balancer -->
  <property>
    <name>dfs.datanode.balance.bandwidthPerSec</name>
    <value>10485760</value>
  </property>
</configuration>
```

## 12. 命令速查增强

### 12.1 节点管理

| 操作 | 命令 |
|------|------|
| 列出所有 NN | `hdfs getconf -namenodes` |
| 检查 NN RPC 端口 | `hdfs getconf -confKey dfs.namenode.rpc-address.mycluster.nn1` |
| 设置 DN 带宽 | `hdfs dfsadmin -setBalancerBandwidth 20971520` |
| 触发 DN 块报告 | `hdfs dfsadmin -triggerBlockReport <dn_hostname>:50010` |
| 触发 DN 缓存刷新 | `hdfs dfsadmin -reconfig <dn_hostname>:50010 start` |
| DN 退役状态检查 | `hdfs dfsadmin -report -decommissioning` |
| DN 添加（刷新） | `hdfs dfsadmin -refreshNodes` |
| 查看拓扑 | `hdfs dfsadmin -printTopology` |
| 查看 DN 详细信息 | `hdfs dfsadmin -getDatanodeInfo <dn_hostname>:50010` |
| 获取 FsImage | `hdfs dfsadmin -fetchImage /tmp/fsimage` |
| 统计 DN 使用率分布 | `hdfs dfsadmin -report \| awk '/DFS Used%/{print prev, $NF} {prev=$NF}'` |
| 列出所有 DN 主机 | `hdfs dfsadmin -report \| grep "Hostname:" \| awk '{print $2}'` |

### 12.2 文件系统管理

| 操作 | 命令 |
|------|------|
| 查看 HDFS 整体空间 | `hdfs dfs -df -h /` |
| 查看目录大小排序 | `hdfs dfs -du -h / \| sort -rh \| head -20` |
| 查看目录下文件数 | `hdfs dfs -count /path` |
| 设置文件副本数 | `hdfs dfs -setrep -R -w 3 /path` |
| 修改块大小 | `hdfs dfs -D dfs.blocksize=268435456 -put file /path` |
| 查看文件块信息 | `hdfs fsck /path/to/file -files -blocks -locations` |
| 获取文件 Lease | `hdfs debug recoverLease -path /path -retries 10` |
| 文件快照创建 | `hdfs dfs -createSnapshot /path snapshot_name` |
| 文件快照删除 | `hdfs dfs -deleteSnapshot /path snapshot_name` |
| 文件快照列表 | `hdfs dfs -ls /path/.snapshot` |
| 文件加密区创建 | `hdfs crypto -createZone -keyName key1 -path /encrypted` |
| 保留空间设置 | `hdfs dfsadmin -setSpaceQuota 10t /path` |
| 保留文件数设置 | `hdfs dfsadmin -setQuota 1000000 /path` |
| 查看目录配额 | `hdfs dfs -count -q /path` |
| 设置 ACL | `hdfs dfs -setfacl -m user:alice:rwx /path` |
| 获取 ACL | `hdfs dfs -getfacl /path` |
| 设置 HDFS 文件压缩 | `hdfs dfs -D dfs.client.block.write.replace-datanode-on-failure.enable=true -put file /path` |

### 12.3 小文件治理

小文件过多会耗尽 NN 内存（每个文件约 150 字节元数据），是 HDFS 最常见性能瓶颈之一。

**诊断小文件问题**
```bash
# 统计各级目录的文件数（发现小文件密集目录）
hdfs dfs -count -q / 2>/dev/null
hdfs dfs -count -q /user 2>/dev/null
hdfs dfs -count -q /tmp 2>/dev/null

# 统计文件大小分布
hdfs fsck / -files 2>/dev/null | grep "^/" | awk -F ' ' '{print $2}' | awk \
  '{if($1<1024*1024) small++; else if($1<128*1024*1024) medium++; else large++} \
   END{printf "Small(<1MB):%d Medium(1MB-128MB):%d Large(>128MB):%d total:%d\n", small, medium, large, small+medium+large}'

# 查看 NN 内存中的文件数
curl -s http://nn-host:50070/jmx?qry=Hadoop:service=NameNode,name=FSNamesystem* | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(d['beans'][0])" 2>/dev/null | \
  grep -E "(FilesTotal|BlocksTotal)"
```

**小文件合并方案**

| 方案 | 命令/工具 | 适用场景 |
|------|-----------|----------|
| HAR 归档 | `hadoop archive -archiveName files.har -p /src /dest` | 不常访问的历史文件 |
| DistCp 合并 | 先合并再 distcp | 离线批量合并 |
| SequenceFile | 将小文件合并为 SequenceFile | MapReduce/Spark 输入 |
| Hive 合并 | `ALTER TABLE ... CONCATENATE;` | Hive ORC/Parquet 表 |
| HBase 替代 | HBase 存储海量小数据 | 实时小文件随机读写 |

**HAR (Hadoop Archive) 操作**
```bash
# 创建 HAR 归档（减少文件数但不压缩数据）
hadoop archive -archiveName myarchive.har -p /user/hive/warehouse/small_files /user/archive/

# 查看 HAR 文件
hdfs dfs -ls har:///user/archive/myarchive.har

# 读取 HAR 中数据（Spark/Hive 需要配置支持 HAR）
hdfs dfs -ls har:///user/archive/myarchive.har/path

# 解归档
hdfs dfs -cp har:///user/archive/myarchive.har/* /dest/path/
```

**Tuning 参数控制小文件产生**
```bash
# 降低合并阈值
# hdfs-site.xml 加：
# dfs.namenode.max.blocks.per.file = 100000
# 控制每个 DN 的 chunk 大小

# MapReduce 输出合并
# set mapreduce.output.fileoutputformat.compress=true
# set mapreduce.fileoutputformat.compress.codec=org.apache.hadoop.io.compress.SnappyCodec
# set mapreduce.output.fileoutputformat.compress.type=BLOCK

# Spark 写出合并
# df.coalesce(1).write.option("maxRecordsPerFile", 1000000)
# df.repartition(10).write  # 按分区控制输出文件数
```

**NN 内存估算**
```
NN 内存 ≈ 每个文件 650 字节 + 每个 block 250 字节
1 亿个文件（每文件 1 block）≈ (100M × 650 + 100M × 250) ≈ 90 GB 堆
建议堆大小 = 估算 × 1.5（预留 GC 空间）
```

## 13. FsImage 与 Edits Log 管理

### 13.1 FsImage 简介

FsImage 是 HDFS 文件系统元数据的完整快照（目录树、文件属性、Block 映射）。Edits Log 记录自上次 FsImage 以来的增量变更。

| 文件 | 路径 | 说明 |
|------|------|------|
| `fsimage_*` | `dfs.namenode.name.dir/current/` | 元数据完整快照 |
| `edits_*` | `dfs.namenode.name.dir/current/` | 增量编辑日志 |
| `seen_txid` | `dfs.namenode.name.dir/current/` | 记录已应用的最后一个 txid |
| `VERSION` | `dfs.namenode.name.dir/current/` | 命名空间版本和集群ID |

### 13.2 FsImage 查看与分析

```bash
# 离线查看 FsImage 内容（不启动 NN）
hdfs oiv -i /dfs/nn/current/fsimage_0000000000000000001 -o /tmp/fsimage.xml -p XML

# 输出为 HTML 跳跃式查看
hdfs oiv -i /dfs/nn/current/fsimage_0000000000000000001 -o /tmp/fsimage.html -p HTML

# 输出为 JSON（HDFS 3.x 支持）
hdfs oiv -i /dfs/nn/current/fsimage_0000000000000000001 -o /tmp/fsimage.json -p JSON

# 查看 FsImage 中的延迟虚节点
hdfs oiv -i /dfs/nn/current/fsimage_* -o /tmp/fsimage.xml -p XML
grep -oP 'INodeFile.*' /tmp/fsimage.xml | head -5

# 查看 FsImage 大小和创建时间
ls -lh /dfs/nn/current/fsimage_*
```

### 13.3 Edits Log 查看

```bash
# 离线查看 Edits Log（二进制格式 → XML）
hdfs oev -i /dfs/nn/current/edits_0000000000000000001-0000000000000001000 \
  -o /tmp/edits.xml -p XML

# 查看 Edits Log 中的事务数
grep -c "<RECORD>" /tmp/edits.xml

# 查看当前最大 txid
hdfs dfsadmin -metasave /tmp/metasave.txt 2>/dev/null
grep "txid" /tmp/metasave.txt

# 查看 NN 上 Edits Log 文件
hdfs namenode -getCommittedTxnId
```

### 13.4 Checkpoint 管理

```bash
# 手动触发 checkpoint（Standby NN 执行）
hdfs dfsadmin -safemode enter
hdfs dfsadmin -saveNamespace
hdfs dfsadmin -safemode leave

# 查看 checkpoint 周期
hdfs getconf -confKey dfs.namenode.checkpoint.period
hdfs getconf -confKey dfs.namenode.checkpoint.txns

# Standby NN 自动 checkpoint 条件：
# - 距上次 checkpoint 超过 dfs.namenode.checkpoint.period（默认 3600 秒）
# - Edits txns 超过 dfs.namenode.checkpoint.txns（默认 1000000）
```

### 13.5 FsImage/Edits 故障恢复

```bash
# 场景：Edits Log 损坏，NN 无法启动
# Step 1: 确认损坏的 edits 文件
# Step 2: 使用 oev 尝试读取，确认损坏点
hdfs oev -i edits_inprogress_XXXXXXXXXXX -o /dev/null 2>&1

# Step 3: 跳过损坏 edits（使用 -recover 选项）
hdfs namenode -recover -force

# Step 4: 或手动修复——删除损坏 edits 后的所有 edits 文件
# 保留最后一个完整 edits 和 fsimage

# Step 5: 验证
hdfs namenode -rollEdits
```

### 13.6 配置 FsImage 压缩

```xml
<!-- 启用 FsImage 压缩 -->
<property>
  <name>fs.image.compress</name>
  <value>true</value>
</property>
<property>
  <name>fs.image.compression.codec</name>
  <value>org.apache.hadoop.io.compress.SnappyCodec</value>
</property>
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `fs.image.compress` | 是否压缩 FsImage | `false` |
| `fs.image.compression.codec` | 压缩编码 | `org.apache.hadoop.io.compress.DefaultCodec` |
| `fs.image.compress.blocksize` | FsImage 文件压缩块大小 | `65536` (64KB) |
| `dfs.namenode.checkpoint.period` | 自动 checkpoint 间隔（秒） | `3600` (1h) |
| `dfs.namenode.checkpoint.txns` | 自动 checkpoint 触发的事务数 | `1000000` |
| `dfs.namenode.num.checkpoints.retained` | 保留的 checkpoint 数 | `2` |
| `dfs.namenode.num.extra.edits.retained` | 额外保留的 edits 数 | `1000000` |

## 14. NameNode GC 调优

NN 是 Java 进程，GC 停顿直接影响元数据服务的可用性。大集群（文件数 > 1 亿）必须精细调优 JVM GC。

### 14.1 CMS GC 配置（Hadoop 2.x / 3.x 兼容）

```bash
# hdfs-env.sh 或 HADOOP_NAMENODE_OPTS
export HADOOP_NAMENODE_OPTS="-Xms64g -Xmx64g \
  -XX:+UseConcMarkSweepGC \
  -XX:+UseParNewGC \
  -XX:+CMSParallelRemarkEnabled \
  -XX:CMSInitiatingOccupancyFraction=70 \
  -XX:+UseCMSInitiatingOccupancyOnly \
  -XX:+ScavengeBeforeRemark \
  -XX:+CMSScavengeBeforeRemark \
  -XX:ParallelGCThreads=8 \
  -XX:ConcGCThreads=4 \
  -XX:+DisableExplicitGC \
  -verbose:gc -XX:+PrintGCDetails -XX:+PrintGCDateStamps \
  -Xloggc:/var/log/hadoop-hdfs/nn-gc.log \
  -XX:+UseGCLogFileRotation -XX:NumberOfGCLogFiles=10 -XX:GCLogFileSize=100M"
```

| CMS 参数 | 说明 | 推荐值 |
|----------|------|--------|
| `-Xms` / `-Xmx` | 最小/最大堆 | 设为相同值避免动态调整 |
| `-XX:CMSInitiatingOccupancyFraction` | 触发 CMS 老年代占比 | `70` |
| `-XX:ParallelGCThreads` | GC 并行线程 | CPU 核心数的 5/8 |
| `-XX:ConcGCThreads` | 并发线程 | ParallelGCThreads 的 1/4 |
| `-XX:+CMSParallelRemarkEnabled` | 并行 Remark 阶段 | 减少 STW 时间 |
| `-XX:+DisableExplicitGC` | 禁止 System.gc() | 避免意外 Full GC |

### 14.2 G1GC 配置（HDFS 3.x 推荐，大堆场景最佳）

```bash
export HADOOP_NAMENODE_OPTS="-Xms128g -Xmx128g \
  -XX:+UseG1GC \
  -XX:MaxGCPauseMillis=200 \
  -XX:G1HeapRegionSize=32m \
  -XX:G1NewSizePercent=8 \
  -XX:G1MaxNewSizePercent=20 \
  -XX:G1ReservePercent=15 \
  -XX:G1HeapWastePercent=5 \
  -XX:G1MixedGCCountTarget=8 \
  -XX:InitiatingHeapOccupancyPercent=45 \
  -XX:G1MixedGCLiveThresholdPercent=85 \
  -XX:+ParallelRefProcEnabled \
  -XX:+AlwaysPreTouch \
  -XX:+PerfDisableSharedMem \
  -verbose:gc -XX:+PrintGCDetails -XX:+PrintGCDateStamps \
  -Xloggc:/var/log/hadoop-hdfs/nn-gc.log \
  -XX:+UseGCLogFileRotation -XX:NumberOfGCLogFiles=10 -XX:GCLogFileSize=100M"
```

| G1GC 参数 | 说明 | 推荐值 |
|-----------|------|--------|
| `-XX:MaxGCPauseMillis` | 目标 GC 暂停时间 | `200` (ms) |
| `-XX:G1HeapRegionSize` | Region 大小（1-512MB） | `32m` |
| `-XX:InitiatingHeapOccupancyPercent` | 触发并发周期的堆占用率 | `45`（写密集型可调至 35） |
| `-XX:G1ReservePercent` | 预留空间百分比 | `15`（预留防止 promotion failure） |
| `-XX:G1MixedGCCountTarget` | Mixed GC 目标次数 | `8` |
| `-XX:+ParallelRefProcEnabled` | 并行引用处理 | 提升性能 |
| `-XX:+AlwaysPreTouch` | 启动时预占内存 | 避免运行时 mmap 延迟 |

### 14.3 GC 监控与调优

```bash
# 查看当前 GC 配置
jps | grep NameNode | awk '{print $1}' | xargs -I{} jinfo -flags {}

# 实时 GC 统计
jstat -gcutil <nn_pid> 5000 10
# 输出：S0 S1 E O M CCS YGC YGCT FGC FGCT GCT

# 分析 GC 日志（GC pause 时间分布）
grep "GC pause" /var/log/hadoop-hdfs/nn-gc.log | \
  grep -oP '(\d+\.\d+) secs' | cut -d' ' -f1 | \
  awk '{if($1>1) full++; else if($1>0.5) long++; else if($1>0.2) med++; else short++} \
  END{printf "STW pauses: short(<200ms):%d med(200-500ms):%d long(500ms-1s):%d full(>1s):%d\n", short, med, long, full}'

# 检查是否发生 Full GC（大停顿）
grep -c "Full GC" /var/log/hadoop-hdfs/nn-gc.log

# 持续监控 GC
while true; do
  jstat -gcutil <nn_pid> 10000 1
  sleep 10
done
```

### 14.4 GC 问题诊断表

| GC 现象 | 原因 | 调优措施 |
|---------|------|----------|
| Young GC 频繁 | 新生代过小 | 增大 `G1NewSizePercent` 或 `-Xmn` |
| Concurrent Mode Failure | 并发回收跟不上对象分配 | 降低 `InitiatingHeapOccupancyPercent`，增大堆 |
| Full GC 频繁 | CMS 碎片或 G1 疏散失败 | CMS: 启用 `-XX:+UseCMSCompactAtFullCollection`；G1: 增大 `G1ReservePercent` |
| 单次 GC > 5s | 堆过大或引用处理慢 | 启用 `ParallelRefProcEnabled`，Reduce `G1HeapRegionSize` |
| Promotion Failed | 老年代无法晋升 | 增大 `G1ReservePercent` 或整体堆，降低 IHO 触发值 |
| 元空间 OOM | 类加载过多 | 设置 `-XX:MaxMetaspaceSize`，排查类泄漏 |

## 15. HDFS Federation 配置

### 15.1 Federation 架构

HDFS Federation 将元数据分布到多个独立的 NameNode，每个 NN 管理一部分 namespace volume。适合超大规模集群（单 NN 无法承载）。

| 组件 | 说明 |
|------|------|
| Namespace Volume | 一个独立的 NameNode 管理的目录空间 |
| Block Pool | 与 Namespace Volume 对应的 block 集合 |
| Backend Storage | 所有 DataNode 统一注册到所有 Block Pool |
| Router (HDFS 3.x) | Federation 路由层，统一客户端访问入口 |

### 15.2 多 Namespace 配置示例

```xml
<!-- hdfs-site.xml Federation 配置 -->
<configuration>
  <!-- Nameservice 1: 用于用户数据 -->
  <property>
    <name>dfs.nameservices</name>
    <value>ns1,ns2</value>
  </property>

  <!-- NS1 配置 -->
  <property>
    <name>dfs.namenode.rpc-address.ns1</name>
    <value>nn1-host:8020</value>
  </property>
  <property>
    <name>dfs.namenode.http-address.ns1</name>
    <value>nn1-host:50070</value>
  </property>
  <property>
    <name>dfs.namenode.name.dir.ns1</name>
    <value>/data/dfs/nn1</value>
  </property>

  <!-- NS2 配置（如用于临时/ETL 数据） -->
  <property>
    <name>dfs.namenode.rpc-address.ns2</name>
    <value>nn2-host:8020</value>
  </property>
  <property>
    <name>dfs.namenode.http-address.ns2</name>
    <value>nn2-host:50070</value>
  </property>
  <property>
    <name>dfs.namenode.name.dir.ns2</name>
    <value>/data/dfs/nn2</value>
  </property>

  <!-- Federation 路由（HDFS 3.x Router-Based Federation） -->
  <property>
    <name>dfs.federation.router.default.nameservice</name>
    <value>ns1</value>
  </property>
</configuration>
```

### 15.3 Federation 运维命令

```bash
# 查看各 NameNode 的 Block Pool
hdfs dfsadmin -report

# 在 Federation 环境下查看各 NN 状态
hdfs haadmin -ns ns1 -getServiceState nn1
hdfs haadmin -ns ns2 -getServiceState nn2

# 跨 Namespace 操作（使用全路径）
hdfs dfs -ls hdfs://ns1/user/
hdfs dfs -ls hdfs://ns2/tmp/

# Federation Router（3.x）状态
hdfs dfs -ls /  # Router 自动路由到默认 Namespace
```

### 15.4 Federation 使用 Mount Table

```bash
# HDFS 3.x Router-Based Federation
# Router 使用 mount table 将目录挂载到不同 Namespace
# 例如：/user → ns1, /tmp → ns2
hdfs dfsadmin -setMountTable /data/tmp ns2
hdfs dfsadmin -getMountTable
hdfs dfsadmin -removeMountTable /data/tmp
```

| Federation 优缺点 | 说明 |
|-------------------|------|
| ✅ 水平扩展元数据 | 多个 NN 分担内存压力 |
| ✅ 隔离性 | 不同 Namespace 故障不影响其他 |
| ✅ 性能隔离 | 写入压力分散到多个 NN |
| ❌ 运维复杂度 | 管理多个 NN、ViewFs/Router |
| ❌ 跨 Namespace 操作受限 | 不支持跨 NS rename 或硬链 |

## 16. 故障排查实战表（6 种场景）

### 场景 1：Safe Mode 无法退出

```bash
# 诊断步骤
hdfs dfsadmin -safemode get
# 检查两个关键指标：block 上报率和副本满足率

# 打印详细原因
hdfs dfsadmin -report | grep -E "Blocks with corrupt|Missing blocks|Under replicated blocks"

# 如果块上报率不足 → 检查 DN 状态和连接
hdfs dfsadmin -report -dead
# 如果死节点过多：等待重启或移除死节点

# 如果 missing/corrupt 过多 → 执行修复
hdfs fsck / -list-corruptfileblocks | grep -c "^/"
hdfs fsck / -files -blocks 2>&1 | tail -5

# 紧急措施：调低阈值快速退出（风险可控）
hdfs dfsadmin -safemode leave
# 如果 leave 失败：检查 NN 日志是否有 IOException
```

### 场景 2：NN 堆内存不足（OOM / GC 压力大）

```bash
# 确认症状
jstat -gcutil <nn_pid> 2000 5
# 观察 Old 区占用率持续上升

# 查看 NN 内存中文件/Block 数
curl -s http://nn-host:50070/jmx?qry=Hadoop:service=NameNode,name=FSNamesystem* | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Files: {d[\"beans\"][0][\"FilesTotal\"]}, Blocks: {d[\"beans\"][0][\"BlocksTotal\"]}')"

# 估算所需堆内存
# 公式：内存 = 文件数 × 650B + Block数 × 250B + 30% 预留

# 短期解决：重启 NN 增大 -Xmx
# 长期解决：
# - 小文件治理（HAR 归档）
# - Federation 拆分 Namespace
# - HDFS 3.x Router-Based Federation
```

### 场景 3：DataNode 频繁失联（心跳超时）

```bash
# 心跳超时公式
# timeout = 2 * dfs.namenode.heartbeat.recheck-interval (5min default)
#            + 10 * dfs.namenode.heartbeat.interval (3s default)
# ≈ 2 * 300000 + 10 * 3000 = 630000ms = 10.5min

# 诊断
hdfs dfsadmin -report -dead
# 检查 DN 日志
tail -100 /var/log/hadoop-hdfs/hadoop-hdfs-datanode-*.log | grep -E "ERROR|WARN|Timeout"

# 检查 DN 磁盘
df -h /data/dfs/dn

# 调优：增大超时容忍
# hdfs-site.xml:
# dfs.namenode.heartbeat.recheck-interval = 600000 (10min)
# dfs.namenode.heartbeat.interval = 5 (s)

# 重启 DN
systemctl restart hadoop-hdfs-datanode
```

### 场景 4：HDFS 磁盘损坏（DataNode 存储故障）

```bash
# 症状：DN 日志 CRC 校验错误，块文件无法读取

# Step 1：确认损坏磁盘
lsblk
smartctl -a /dev/sdb | grep -E "Reallocated_Sector_Ct|Current_Pending_Sector|Offline_Uncorrectable"

# Step 2：隔离损坏磁盘（从 datanode.data.dir 移除路径）
# 修改 dfs.datanode.data.dir，去掉坏盘路径
# 重启 DN

# Step 3：NN 检测到副本丢失后自动复制
# 监控复制进度
hdfs dfsadmin -report | grep "Under replicated blocks"

# Step 4：替换磁盘后重新添加
# 新磁盘挂载回原路径
# 添加到 dfs.datanode.data.dir
# 重启 DN 或 reconfig
hdfs dfsadmin -reconfig <dn>:50010 start
```

### 场景 5：JournalNode 故障导致 HA 降级

```bash
# 诊断
# Quorum 丢失：3 台 JN 中 2 台故障则 HA 停摆

# Step 1：检查存活 JN
curl -s http://jn1-host:8480/journal?service=hdfsHA 2>/dev/null | head -5
curl -s http://jn2-host:8480/journal?service=hdfsHA 2>/dev/null | head -5
curl -s http://jn3-host:8480/journal?service=hdfsHA 2>/dev/null | head -5

# Step 2：重启故障 JN
systemctl restart hadoop-hdfs-journalnode

# Step 3：检查 JN 磁盘空间
df -h /data/dfs/jn

# Step 4：清理 JN 老 edits（保留足够数量）
# 在 NN 同步正常的前提下，删除旧 edits 文件
# JN 数据目录：/data/dfs/jn/current/
# 只保留最近几天的 edits

# Step 5：如果 JN 数据损坏
# 从健康 JN 复制 edits 到损坏 JN
# 或者重新初始化 JN（灾难恢复流程见 6.5）
```

### 场景 6：小文件过多引发 NN 性能瓶颈

```bash
# 诊断
# NN RPC 响应慢、Safe Mode 加载 FsImage 超长

# Step 1：统计小文件占比
hdfs fsck / -files 2>/dev/null | grep "^/" | awk -F ' ' '{print $2}' | awk \
  '{if($1<1024*1024) s++; else if($1<128*1024*1024) m++; else l++} \
  END{printf "Small(%%) files: %.1f%% Medium(%%) files: %.1f%% Large(%%) files: %.1f%%\n", s/(s+m+l)*100, m/(s+m+l)*100, l/(s+m+l)*100}'

# Step 2：找到小文件密集目录
hdfs dfs -count -h / | sort -t' ' -k2 -rn | head -20

# Step 3：执行 HAR 归档
hadoop archive -archiveName data_archive.har -p /user/hive/warehouse/db1.db /user/archive/hive/

# Step 4：检查归档前后文件数变化
hdfs dfs -count -h /user/archive/hive/

# Step 5：监控 NN 内存释放
# 等待归档完成后，确认 BlocksTotal 下降
```

## 17. 运维脚本模板

### 17.1 健康检查脚本

```bash
#!/bin/bash
# HDFS 健康检查脚本 — 用于 Cron 或监控系统
# 保存为 /usr/local/bin/hdfs-health-check.sh

CLUSTER_NAME="mycluster"
NN1_HOST="nn1-host"
NN2_HOST="nn2-host"
JN_HOSTS=("jn1-host" "jn2-host" "jn3-host")
ISSUES=0

check_nn() {
  local nn=$1 host=$2
  local state=$(hdfs haadmin -getServiceState "$nn" 2>/dev/null)
  if [ $? -ne 0 ]; then
    echo "CRITICAL: Cannot get $nn state!"
    ISSUES=$((ISSUES+2))
    return
  fi
  echo "OK: $nn state=$state"
}

check_safemode() {
  local sm=$(hdfs dfsadmin -safemode get 2>/dev/null)
  if echo "$sm" | grep -q "ON"; then
    echo "WARNING: Safe mode is ON!"
    ISSUES=$((ISSUES+1))
  else
    echo "OK: Safe mode is OFF"
  fi
}

check_datanodes() {
  local dead=$(hdfs dfsadmin -report -dead 2>/dev/null | grep -c "Hostname")
  local live=$(hdfs dfsadmin -report -live 2>/dev/null | grep -c "Hostname")
  echo "OK: Live=$live Dead=$dead"
  if [ "$dead" -gt 0 ]; then
    echo "WARNING: $dead dead DataNode(s)!"
    ISSUES=$((ISSUES+dead))
  fi
}

check_journalnode() {
  for jn in "${JN_HOSTS[@]}"; do
    if curl -s --max-time 5 "http://$jn:8480/journal?service=hdfsHA" >/dev/null 2>&1; then
      echo "OK: JN $jn is alive"
    else
      echo "CRITICAL: JN $jn unreachable!"
      ISSUES=$((ISSUES+2))
    fi
  done
}

check_blocks() {
  local report=$(hdfs fsck / -files -blocks 2>&1 | tail -3)
  local missing=$(echo "$report" | grep -oP 'Missing blocks:\s+\K\d+' )
  local corrupt=$(echo "$report" | grep -oP 'Corrupt blocks:\s+\K\d+' )
  echo "Blocks: missing=$missing corrupt=$corrupt"
  if [ "${missing:-0}" -gt 0 ] || [ "${corrupt:-0}" -gt 0 ]; then
    echo "WARNING: $missing missing, $corrupt corrupt blocks!"
    ISSUES=$((ISSUES+1))
  fi
}

# 执行检查
check_nn "nn1" "$NN1_HOST"
check_nn "nn2" "$NN2_HOST"
check_safemode
check_datanodes
check_journalnode
check_blocks

echo "Total issues=$ISSUES"
exit $ISSUES
```

### 17.2 磁盘均衡调度脚本

```bash
#!/bin/bash
# Balancer 定时运行脚本 — 建议 Cron 每天低峰期执行
# 保存为 /usr/local/bin/hdfs-balancer-run.sh

LOG_FILE="/var/log/hadoop-hdfs/balancer-cron.log"
BALANCER_PID_FILE="/tmp/hdfs-balancer.pid"
THRESHOLD=${1:-5}
BANDWIDTH=${2:-20971520}  # 20 MB/s
TIMEOUT_HOURS=${3:-4}

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# 检查是否已有 balancer 运行
if [ -f "$BALANCER_PID_FILE" ] && kill -0 $(cat "$BALANCER_PID_FILE") 2>/dev/null; then
  log "Balancer already running, exiting."
  exit 1
fi

# 检查集群状态
DEAD_NODES=$(hdfs dfsadmin -report -dead 2>/dev/null | grep -c "Hostname")
if [ "$DEAD_NODES" -gt 0 ]; then
  log "WARNING: $DEAD_NODES dead DataNode(s). Skip balancer."
  exit 1
fi

SAFE_MODE=$(hdfs dfsadmin -safemode get 2>/dev/null)
if echo "$SAFE_MODE" | grep -q "ON"; then
  log "Safe mode is ON. Skip balancer."
  exit 1
fi

# 设置带宽
hdfs dfsadmin -setBalancerBandwidth "$BANDWIDTH" >> "$LOG_FILE" 2>&1

# 启动 Balancer（后台运行 4 小时）
log "Starting balancer: threshold=$THRESHOLD bandwidth=$BANDWIDTH timeout=${TIMEOUT_HOURS}h"
nohup timeout "${TIMEOUT_HOURS}h" hdfs balancer \
  -threshold "$THRESHOLD" \
  -policy datanode \
  >> "$LOG_FILE" 2>&1 &

BALANCER_PID=$!
echo $BALANCER_PID > "$BALANCER_PID_FILE"
log "Balancer PID: $BALANCER_PID"

# 等待完成
wait $BALANCER_PID
BALANCER_EXIT=$?
rm -f "$BALANCER_PID_FILE"

if [ $BALANCER_EXIT -eq 0 ]; then
  log "Balancer completed successfully."
elif [ $BALANCER_EXIT -eq 124 ]; then
  log "Balancer timed out after ${TIMEOUT_HOURS}h."
else
  log "Balancer exited with code $BALANCER_EXIT."
fi

exit $BALANCER_EXIT
```

### 17.3 小文件治理脚本

```bash
#!/bin/bash
# 小文件识别与 HAR 归档脚本
# 保存为 /usr/local/bin/hdfs-small-files-archive.sh

THRESHOLD_BYTES=$((1 * 1024 * 1024))  # < 1MB 视为小文件
ARCHIVE_ROOT="/user/archive"
DRY_RUN=${1:-true}  # 默认 dry-run

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

find_small_files() {
  local dir=$1
  log "Scanning $dir for small files (< ${THRESHOLD_BYTES}B)..."
  hdfs dfs -ls -R "$dir" 2>/dev/null | \
    awk -v threshold="$THRESHOLD_BYTES" '$5 < threshold && $5 > 0 {print $8}' | \
    head -10000  # 限制每次处理 1 万
}

create_har() {
  local src_dir=$1
  local archive_name=$(basename "$src_dir")_$(date '+%Y%m%d')
  local archive_path="$ARCHIVE_ROOT/${archive_name}.har"

  # 检查是否已经归档
  hdfs dfs -test -d "$archive_path" 2>/dev/null && log "Archive $archive_path exists, skip." && return 1

  if [ "$DRY_RUN" = true ]; then
    log "DRY-RUN: would create HAR from $src_dir to $archive_path"
    return 0
  fi

  log "Creating HAR: $src_dir → $archive_path"
  hadoop archive -archiveName "$archive_name.har" -p "$src_dir" "$ARCHIVE_ROOT/" 2>&1 | tail -5

  if [ $? -eq 0 ]; then
    log "HAR created: $archive_path"
    # 可选：删除原始文件（确认归档验证通过后）
    # hdfs dfs -rm -r -skipTrash "$src_dir"
  else
    log "ERROR: HAR creation failed for $src_dir"
  fi
}

# 主流程
SMALL_FILE_DIRS=(
  "/user/hive/warehouse"
  "/tmp"
  "/user/history"
)

for dir in "${SMALL_FILE_DIRS[@]}"; do
  log "Processing $dir ..."
  count=$(hdfs dfs -count "$dir" 2>/dev/null | awk '{print $2}')
  log "  File count: $count"
  if [ "$count" -gt 10000 ]; then
    log "  Large number of files detected ($count), recommend HAR archive."
    create_har "$dir"
  fi
done

log "Small file check complete."
```

### 17.4 Disaster Recovery 脚本

```bash
#!/bin/bash
# NameNode 灾难恢复脚本 — 单 NN 损坏或 HA 完全不可用
# 保存为 /usr/local/bin/hdfs-nn-recovery.sh

NN_HOST=$1
CLUSTER_ID=${2:-mycluster}
BACKUP_DIR="/data/backup/hdfs-nn"
DATE_TAG=$(date '+%Y%m%d_%H%M%S')

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

die() {
  log "FATAL: $*"
  exit 1
}

# 检查环境
which hdfs || die "hdfs command not found"
[ -n "$NN_HOST" ] || die "Usage: $0 <nn_host> [cluster_id]"

# Step 1: 停止 NN
log "Stopping NameNode on $NN_HOST..."
ssh "$NN_HOST" "systemctl stop hadoop-hdfs-namenode" 2>/dev/null

# Step 2: 备份当前 FsImage
log "Backing up current metadata to $BACKUP_DIR/$DATE_TAG..."
NN_DATA_DIR=$(ssh "$NN_HOST" "hdfs getconf -confKey dfs.namenode.name.dir 2>/dev/null | cut -d',' -f1")
[ -n "$NN_DATA_DIR" ] || NN_DATA_DIR="/data/dfs/nn"
ssh "$NN_HOST" "mkdir -p $BACKUP_DIR/$DATE_TAG && cp -r $NN_DATA_DIR/current $BACKUP_DIR/$DATE_TAG/" || die "Backup failed"

# Step 3: 检查 FsImage 完整性
log "Checking FsImage integrity..."
ssh "$NN_HOST" "hdfs namenode -checksum $NN_DATA_DIR/current/fsimage_*" 2>/dev/null || log "WARNING: Checksum check not available, skipping."

# Step 4: 尝试 -recover 模式启动
log "Attempting NN recovery mode..."
ssh "$NN_HOST" "sudo -u hdfs hdfs namenode -recover -force" 2>&1 | tail -20

if [ $? -eq 0 ]; then
  log "Recovery successful. Starting NN..."
  ssh "$NN_HOST" "systemctl start hadoop-hdfs-namenode"
else
  die "Recovery failed. Check $BACKUP_DIR/$DATE_TAG/ for manual restore."
fi

# Step 5: 验证
sleep 30
STATE=$(hdfs haadmin -getServiceState nn1 2>/dev/null)
log "NN state: $STATE"

if echo "$STATE" | grep -q "active\|standby"; then
  log "Recovery complete. NN is $STATE."
else
  log "WARNING: NN state is '$STATE', check manually."
fi
```

### 17.5 Cron 模板

```bash
# /etc/cron.d/hdfs-maintenance
# ┌───────── 分钟 (0-59)
# │ ┌───────── 小时 (0-23)
# │ │ ┌───────── 日 (1-31)
# │ │ │ ┌───────── 月 (1-12)
# │ │ │ │ ┌───────── 周 (0-7, 0=周日)
# │ │ │ │ │
# 0 3 * * * hdfs /usr/local/bin/hdfs-health-check.sh >> /var/log/hdfs-health.log 2>&1
# 0 4 * * 0 hdfs /usr/local/bin/hdfs-small-files-archive.sh false >> /var/log/hdfs-archive.log 2>&1
# 0 1 * * 1-5 hdfs /usr/local/bin/hdfs-balancer-run.sh 5 20971520 4 >> /var/log/hdfs-balancer-cron.log 2>&1
# 0 2 1 * * hdfs hdfs dfsadmin -fetchImage /data/backup/hdfs/fsimage_weekly
```

## 18. 日志与监控速查

| 日志文件 | 用途 | 查看方式 |
|----------|------|----------|
| NN 主日志 | NameNode 操作记录 | `tail -f /var/log/hadoop-hdfs/hadoop-hdfs-namenode-*.log` |
| NN GC 日志 | Safe Mode 延迟可能与 GC 有关 | `tail -f /var/log/hadoop-hdfs/hadoop-hdfs-namenode-*-gc.log*` |
| DN 日志 | DataNode 心跳/块上报 | `tail -f /var/log/hadoop-hdfs/hadoop-hdfs-datanode-*.log` |
| JN 日志 | JournalNode edit log 同步 | `tail -f /var/log/hadoop-hdfs/hadoop-hdfs-journalnode-*.log` |
| Balancer 日志 | 均衡进度与异常 | `tail -f /var/log/hadoop-hdfs/hadoop-hdfs-balancer-*.log` |
| ZKFC 日志 | HA 自动故障转移 | `tail -f /var/log/hadoop-hdfs/hadoop-hdfs-zkfc-*.log` |
| HDFS Audit 日志 | 所有文件访问审计 | `tail -f /var/log/hadoop-hdfs/hdfs-audit.log` |
| Disk Balancer 日志 | 盘级均衡执行日志 | `tail -f /var/log/hadoop-hdfs/hadoop-hdfs-diskbalancer-*.log` |

## 19. JMX 监控端点

| JMX 指标 | 端点 | 关键字段 |
|----------|------|----------|
| NN 状态 | `http://nn-host:50070/jmx?qry=Hadoop:service=NameNode,name=NameNodeStatus` | `State`, `NNRole` |
| FSNamesystem | `http://nn-host:50070/jmx?qry=Hadoop:service=NameNode,name=FSNamesystem*` | `FilesTotal`, `BlocksTotal`, `CapacityRemainingGB`, `CapacityUsedGB` |
| NN RPC 统计 | `http://nn-host:50070/jmx?qry=Hadoop:service=NameNode,name=RpcActivityForPort8020` | `RpcQueueTimeNumOps`, `RpcProcessingTimeAvgTime` |
| JVM 内存 | `http://nn-host:50070/jmx?qry=java.lang:type=Memory` | `HeapMemoryUsage.used`, `HeapMemoryUsage.max` |
| GC 统计 | `http://nn-host:50070/jmx?qry=java.lang:type=GarbageCollector,name=G1\ Young\ Generation` | `CollectionCount`, `CollectionTime` |
| DataNode | `http://dn-host:50075/jmx?qry=Hadoop:service=DataNode,name=DataNodeActivity*` | `BytesWritten`, `BytesRead`, `BlocksRemoved` |
| Balancer 进度 | `http://nn-host:50070/jmx?qry=Hadoop:service=NameNode,name=Balancer*` | `BalancerStatus` |
| Disk Balancer | `http://dn-host:50075/jmx?qry=Hadoop:service=DataNode,name=DiskBalancerStatus` | `DiskBalancerStatus` |

## 20. 备份与恢复策略

| 备份对象 | 备份方法 | 频率 | 用途 |
|----------|----------|------|------|
| FsImage | `hdfs dfsadmin -fetchImage /backup/` | 每日 | 元数据恢复 |
| Edits Log | 周期性归档 edits 到备份目录 | 每小时 | 事务回放 |
| DistCp 跨集群 | `hadoop distcp -update hdfs://nn1:8020/ hdfs://nn2:8020/` | 每日/每周 | 数据容灾 |
| HDFS Snapshot | `hdfs dfs -createSnapshot /data daily_$(date +%Y%m%d)` | 每日 | 快速恢复文件 |
| NN 配置文件 | 备份 `core-site.xml`, `hdfs-site.xml` | 变更时 | 配置恢复 |

## 21. 性能基准命令

```bash
# HDFS 写性能测试
hadoop jar /usr/lib/hadoop-mapreduce/hadoop-mapreduce-client-jobclient-*.jar \
  TestDFSIO -write -nrFiles 10 -fileSize 1000 -buffSize 65536 \
  -resFile /tmp/testdfsio_write.log

# HDFS 读性能测试
hadoop jar /usr/lib/hadoop-mapreduce/hadoop-mapreduce-client-jobclient-*.jar \
  TestDFSIO -read -nrFiles 10 -fileSize 1000 -buffSize 65536 \
  -resFile /tmp/testdfsio_read.log

# 清理测试数据
hadoop jar /usr/lib/hadoop-mapreduce/hadoop-mapreduce-client-jobclient-*.jar \
  TestDFSIO -clean

# NN 吞吐测试（NNBench）
hadoop jar /usr/lib/hadoop-mapreduce/hadoop-mapreduce-client-jobclient-*.jar \
  NNBench -operation create_write -maps 20 -reduces 0 \
  -startTime $(date +%s) -blockSize 1 -bytesToWrite 0 \
  -numberOfFiles 10000 -replicationFactorPerFile 3
```

## 22. 常用 Troubleshooting 快速命令

```bash
# 查看所有 DN 使用率分布
hdfs dfsadmin -report | grep -E "(Hostname|DFS Used%)"

# 查看 NN RPC 响应时间
curl -s http://nn-host:50070/jmx?qry=Hadoop:service=NameNode,name=RpcActivityForPort8020 | \
  python3 -c "import sys,json; d=json.load(sys.stdin)['beans'][0]; print(f'QueueTimeAvg={d[\"RpcQueueTimeAvgTime\"]:.2f}ms, ProcessingAvg={d[\"RpcProcessingTimeAvgTime\"]:.2f}ms')"

# 检查 HDFS 中坏盘数量
hdfs dfsadmin -getDatanodeInfo <dn-host>:50010 2>/dev/null | grep -i "volume"

# 查看 block 上报延迟
grep "BlockReport" /var/log/hadoop-hdfs/hadoop-hdfs-datanode-*.log | tail -5

# 检查 edits 积压数
curl -s http://jn1-host:8480/getJournal? 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Edits: lastTxid={d.get(\"lastTxId\",0)}, syncTxid={d.get(\"syncTxId\",0)}, gap={d.get(\"lastTxId\",0)-d.get(\"syncTxId\",0)}')"

# 检查 FsImage 加载时间
grep "loadFSImage" /var/log/hadoop-hdfs/hadoop-hdfs-namenode-*.log | tail -3

# 大文件占比
hdfs fsck / -files 2>/dev/null | grep "^/" | awk -F ' ' '{print $2}' | \
  awk '{if($1>1024*1024*1024) big++} END{print "Files > 1GB: " big}'

# 统计每个目录的 inode 数（文件+目录）
hdfs dfs -count -h / | sort -t' ' -k2 -rn | head -20
```
