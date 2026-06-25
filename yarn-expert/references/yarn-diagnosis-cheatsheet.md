# YARN 诊断速查手册

## 核心命令

```bash
# 查看应用
yarn application -list                          # 所有运行中应用
yarn application -list -appStates FAILED        # 失败应用
yarn application -status <app_id>               # 应用详情+诊断信息

# 查看节点
yarn node -list -all                            # 所有节点状态+资源
yarn node -status <node_id>                     # 单节点详情

# 查看队列
yarn queue -status root                         # 根队列资源分配
yarn queue -status root.<queue>                 # 子队列详情

# 查看日志
yarn logs -applicationId <app_id>               # 聚合日志
yarn logs -applicationId <app_id> -containerId <cid>  # 单 Container 日志

# 集群状态
yarn cluster -status                            # 总资源/使用量

# RM 管理
yarn rmadmin -getServiceState                   # HA 状态
yarn rmadmin -refreshQueues                     # 刷新队列
yarn rmadmin -refreshNodes                      # 刷新节点
```

## Exit Code 速查

| Code | 含义 | 操作 |
|------|------|------|
| -1000 | 被抢占 | 调整抢占策略 |
| -100 | vmem 超限 | 调大 vmem-pmem-ratio |
| -103 | pmem 超限 | 增大 Container 内存 |
| -104 | vmem 超限 | 调大比例 |
| 137 | OOM Kill | 检查 dmesg |
| 1 | 代码异常 | 拉取 stderr 日志 |

## 排查路线

```
任务提交失败/卡住
  ├─ yarn application -list
  │   ├─ 无应用 → 检查 ACL / 提交脚本
  │   └─ ACCEPTED → 检查资源
  ├─ yarn queue -status root.<queue>
  │   ├─ 队列满 → 扩容或调小任务
  │   └─ 有空闲 → 检查节点
  ├─ yarn node -list -all
  │   ├─ 节点不健康 → 检查 NM
  │   └─ 资源碎片 → 调小 maximum-allocation
  └─ yarn application -status <app_id>
      └─ 看 Diagnostics → 按 Exit Code 处理
```

## 资源碎片化检查

```bash
yarn node -list -all | awk '/RUNNING/{
  for(i=1;i<=NF;i++) {
    if($i ~ /[0-9]+MB/) mem=substr($i,1,length($i)-2);
    if($i ~ /vCores/) vcore=$(i-1);
  }
  printf "%-30s mem_avail=%-5d MB  vcore_avail=%-3d\n", $1, mem, vcore
}'
```

## 队列限制检查

```bash
yarn queue -status root.<queue> | grep -E "Capacity|AbsoluteUsed|UserLimit|Pending"
```
