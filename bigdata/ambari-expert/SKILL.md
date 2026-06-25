---
name: ambari-expert
description: Ambari 集群管理专家 — 服务巡检/配置管理/Blueprint 部署/告警处理/Stack 升级
category: bigdata
triggers:
  - ambari
  - ambari-server
  - ambari-agent
  - blueprint
  - hdp stack
  - ambari 告警
---

# Ambari 集群管理专家

## 概述

Apache Ambari 是大数据集群管理平台，提供 Hadoop 生态组件的部署、配置、监控和管理功能。本 skill 覆盖 Ambari 日常运维的五个核心场景。

## 1. Ambari Server / Agent 服务状态检查

### 服务启停与状态

```bash
# 启动/停止/重启 Ambari Server
sudo ambari-server start
sudo ambari-server stop
sudo ambari-server restart

# 查看 Ambari Server 状态
sudo ambari-server status

# 启动/停止/重启 Ambari Agent（在所有节点执行）
sudo ambari-agent start
sudo ambari-agent stop
sudo ambari-agent restart

# 查看 Ambari Agent 状态
sudo ambari-agent status

# 查看 Ambari Server 进程
ps aux | grep AmbariServer
ps aux | grep ambari-server

# 查看 Ambari Agent 进程
ps aux | grep ambari-agent

# Ambari Server 日志
tail -f /var/log/ambari-server/ambari-server.log

# Ambari Agent 日志
tail -f /var/log/ambari-agent/ambari-agent.log
```

### 服务不可用排查流程

1. **检查 Ambari Server 进程是否存在** — `sudo ambari-server status`
2. **查看端口监听** — `ss -tlnp | grep 8080`（默认端口 8080）
3. **检查数据库连接** — Ambari Server 依赖 PostgreSQL 或 MySQL/MariaDB
   ```bash
   # PostgreSQL
   sudo -u postgres psql -c "SELECT 1" ambari
   # MySQL
   mysql -u ambari -p -e "SELECT 1"
   ```
4. **检查磁盘空间** — `df -h`（磁盘满会导致 Ambari Server 无法启动）
5. **检查 Java 进程** — `java -version`（需 JDK 8/11）
6. **检查防火墙/iptables** — `sudo iptables -L -n | grep 8080`

## 2. 组件启停

### 通过 Ambari Web UI
- 登录 Ambari Web UI (默认 http://<ambari-server>:8080)
- 左侧服务列表 → 选择目标服务
- 右上角 "Service Actions" → Start / Stop / Restart

### 通过 Ambari REST API（推荐自动化方式）

```bash
# 基础变量
AMBARI_HOST="localhost"
PORT="8080"
CLUSTER_NAME="<cluster_name>"
USER_PASS="admin:admin"
BASE_URL="http://${AMBARI_HOST}:${PORT}/api/v1/clusters/${CLUSTER_NAME}"

# 获取所有服务的当前状态
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  "${BASE_URL}/services" | python -m json.tool

# 启动某个服务（如 HDFS）
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  -X PUT -d '{"RequestInfo":{"context":"Start HDFS"},"Body":{"ServiceInfo":{"state":"STARTED"}}}' \
  "${BASE_URL}/services/HDFS"

# 停止某个服务
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  -X PUT -d '{"RequestInfo":{"context":"Stop HDFS"},"Body":{"ServiceInfo":{"state":"INSTALLED"}}}' \
  "${BASE_URL}/services/HDFS"

# 重启所有已停止的服务
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  -X PUT -d '{"RequestInfo":{"context":"Start All Services","query":"ServiceInfo/state=INSTALLED"},"Body":{"ServiceInfo":{"state":"STARTED"}}}' \
  "${BASE_URL}/services"

# 查看服务请求状态
REQUEST_ID="1"
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  "http://${AMBARI_HOST}:${PORT}/api/v1/clusters/${CLUSTER_NAME}/requests/${REQUEST_ID}"
```

### 组件级启停（精确控制）

```bash
# 获取服务的所有组件
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  "${BASE_URL}/services/HDFS/components"

# 启动某个组件（如 NameNode）
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  -X PUT -d '{"RequestInfo":{"context":"Start NameNode"},"Body":{"HostComponent":{"state":"STARTED"}}}' \
  "${BASE_URL}/hosts/<hostname>/host_components/NAMENODE"

# 停止某个组件
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  -X PUT -d '{"RequestInfo":{"context":"Stop NameNode"},"Body":{"HostComponent":{"state":"INSTALLED"}}}' \
  "${BASE_URL}/hosts/<hostname>/host_components/NAMENODE"
```

## 3. 配置管理

### 查看当前配置

```bash
# 查看集群所有配置类型和版本
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  "${BASE_URL}/configurations"

# 查看某个配置的详情（如 hdfs-site）
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  "${BASE_URL}/configurations?type=hdfs-site&tag=version1"

# 查看服务的当前配置
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  "${BASE_URL}/services/HDFS"
```

### 修改配置并生效

```bash
# 创建新配置版本并应用到服务
# 1. 获取当前配置的 tag/version
CURRENT_VERSION=$(curl -u ${USER_PASS} -s -H "X-Requested-By: ambari" \
  "${BASE_URL}/configurations?type=hdfs-site&tag=version1" | python -c "import sys,json; d=json.load(sys.stdin); print(d['items'][0]['tag'])")

# 2. 推送新配置
# 注意：properties 中放需要的配置项
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  -X POST -d '{
    "Clusters": {
      "desired_config": {
        "type": "hdfs-site",
        "tag": "version2",
        "properties": {
          "dfs.replication": "3",
          "dfs.blocksize": "268435456"
        }
      }
    }
  }' "${BASE_URL}"

# 3. 重启受影响的服务使配置生效
# 配置变更后需要重启相关服务，Ambari Web UI 中会显示 "Restart Required" 标识
```

### 配置对比

```bash
# 对比两个配置版本的差异
python -c "
import json, urllib.request, base64, sys

auth = base64.b64encode(b'admin:admin').decode()
req = urllib.request.Request(
    'http://localhost:8080/api/v1/clusters/<cluster>/configurations?type=hdfs-site&tag=version1'
)
req.add_header('Authorization', f'Basic {auth}')
req.add_header('X-Requested-By', 'ambari')
resp = urllib.request.urlopen(req).read()
conf1 = json.loads(resp)

req2 = urllib.request.Request(
    'http://localhost:8080/api/v1/clusters/<cluster>/configurations?type=hdfs-site&tag=version2'
)
req2.add_header('Authorization', f'Basic {auth}')
req2.add_header('X-Requested-By', 'ambari')
resp2 = urllib.request.urlopen(req2).read()
conf2 = json.loads(resp2)

props1 = conf1['items'][0]['properties']
props2 = conf2['items'][0]['properties']

for k in set(list(props1.keys()) + list(props2.keys())):
    if props1.get(k) != props2.get(k):
        print(f'{k}: {props1.get(k)} -> {props2.get(k)}')
"
```

## 4. Blueprint 部署

Blueprint 是 Ambari 提供的声明式集群部署方式，通过 JSON 模板描述集群拓扑和配置。

### Blueprint 基础结构

Blueprint 由两部分组成：
- **Blueprint 定义**：描述集群的组件拓扑、主机组映射、配置
- **Cluster Creation Template**：将主机主机名映射到主机组

### 生成现有集群的 Blueprint

```bash
# 导出当前集群的 Blueprint
BLUEPRINT_NAME="my-blueprint"
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  "${BASE_URL}?format=blueprint" \
  > cluster_blueprint.json

# 单独导出 Blueprint 定义
curl -u admin:admin -H "X-Requested-By: ambari" \
  "http://localhost:8080/api/v1/blueprints/${BLUEPRINT_NAME}?format=blueprint" \
  > blueprint.json

# 导出主机映射（主机组-主机名对应关系）
curl -u admin:admin -H "X-Requested-By: ambari" \
  "http://localhost:8080/api/v1/blueprints/${BLUEPRINT_NAME}?format=blueprint&hostgroup=true" \
  > hostmapping.json
```

### 创建和注册 Blueprint

```bash
# 1. 注册 Blueprint
curl -u admin:admin -H "X-Requested-By: ambari" \
  -X POST -d @blueprint.json \
  "http://localhost:8080/api/v1/blueprints/${BLUEPRINT_NAME}"

# 2. 注册 Cluster Creation Template
curl -u admin:admin -H "X-Requested-By: ambari" \
  -X POST -d @cluster_creation_template.json \
  "http://localhost:8080/api/v1/clusters/${CLUSTER_NAME}"

# 3. 查看 Blueprint 注册列表
curl -u admin:admin -H "X-Requested-By: ambari" \
  "http://localhost:8080/api/v1/blueprints"

# 4. 删除 Blueprint
curl -u admin:admin -H "X-Requested-By: ambari" \
  -X DELETE "http://localhost:8080/api/v1/blueprints/${BLUEPRINT_NAME}"
```

### Blueprint JSON 示例

```json
{
  "Blueprints": {
    "blueprint_name": "hdp-blueprint",
    "stack_name": "HDP",
    "stack_version": "3.1"
  },
  "configurations": [
    {
      "hdfs-site": {
        "properties": {
          "dfs.replication": "3",
          "dfs.namenode.name.dir": "/data/hadoop/hdfs/namenode",
          "dfs.datanode.data.dir": "/data/hadoop/hdfs/datanode"
        }
      }
    },
    {
      "yarn-site": {
        "properties": {
          "yarn.resourcemanager.hostname": "rm-host.example.com"
        }
      }
    }
  ],
  "host_groups": [
    {
      "name": "master",
      "components": [
        {"name": "NAMENODE"},
        {"name": "RESOURCEMANAGER"},
        {"name": "HISTORYSERVER"},
        {"name": "AMBARI_SERVER"}
      ],
      "cardinality": "1"
    },
    {
      "name": "worker",
      "components": [
        {"name": "DATANODE"},
        {"name": "NODEMANAGER"},
        {"name": "HDFS_CLIENT"},
        {"name": "YARN_CLIENT"}
      ],
      "cardinality": "1+"
    }
  ]
}
```

### Cluster Creation Template 示例

```json
{
  "blueprint": "hdp-blueprint",
  "default_password": "admin123",
  "host_groups": [
    {
      "name": "master",
      "hosts": [
        {"fqdn": "master1.example.com"}
      ]
    },
    {
      "name": "worker",
      "hosts": [
        {"fqdn": "worker1.example.com"},
        {"fqdn": "worker2.example.com"},
        {"fqdn": "worker3.example.com"}
      ]
    }
  ]
}
```

### Blueprint 部署监控

```bash
# 查看集群创建进度
curl -u admin:admin -H "X-Requested-By: ambari" \
  "http://localhost:8080/api/v1/clusters/${CLUSTER_NAME}/requests/1"

# 查看所有进行中的操作
curl -u admin:admin -H "X-Requested-By: ambari" \
  "http://localhost:8080/api/v1/clusters/${CLUSTER_NAME}/requests"
```

## 5. 告警管理

### 查看告警

```bash
# 获取所有告警
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  "${BASE_URL}/alerts"

# 获取当前活动的告警（CRITICAL / WARNING）
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  "${BASE_URL}/alerts?Alert/state=CRITICAL"

# 获取告警统计
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  "${BASE_URL}?fields=alerts_summary"

# 获取告警定义列表
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  "http://${AMBARI_HOST}:${PORT}/api/v1/clusters/${CLUSTER_NAME}/alert_definitions"
```

### 告警操作

```bash
# 禁用某个告警定义（按告警定义 ID）
ALERT_DEF_ID="123"
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  -X PUT -d '{"AlertDefinition":{"enabled":false}}' \
  "http://${AMBARI_HOST}:${PORT}/api/v1/clusters/${CLUSTER_NAME}/alert_definitions/${ALERT_DEF_ID}"

# 启用告警定义
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  -X PUT -d '{"AlertDefinition":{"enabled":true}}' \
  "http://${AMBARI_HOST}:${PORT}/api/v1/clusters/${CLUSTER_NAME}/alert_definitions/${ALERT_DEF_ID}"

# 手动触发某个告警定义检查
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  -X PUT -d '{"RequestInfo":{"context":"Execute alert check","action":"execute"},"Body":{"AlertDefinition/name":"<alert_name>"}}' \
  "${BASE_URL}/alert_definitions"

# 忽略/清除某个告警
ALERT_ID="456"
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  -X PUT -d '{"Alert":{"state":"OK"}}' \
  "${BASE_URL}/alerts/${ALERT_ID}"
```

### 告警通知配置

```bash
# 查看当前告警通知配置
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  "http://${AMBARI_HOST}:${PORT}/api/v1/alert_targets"

# 创建邮件告警通知目标
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  -X POST -d '{
    "AlertTarget": {
      "name": "Admin Email",
      "description": "Send alerts to admin",
      "notification_type": "EMAIL",
      "global": true,
      "alert_states": ["CRITICAL", "WARNING"],
      "properties": {
        "ambari.dispatch-property.recipients": "admin@example.com",
        "ambari.dispatch-property.smtp.host": "smtp.example.com",
        "ambari.dispatch-property.smtp.port": "25",
        "ambari.dispatch-property.mail.from": "ambari@example.com"
      }
    }
  }' "http://${AMBARI_HOST}:${PORT}/api/v1/alert_targets"
```

## 6. Stack 升级

### Stack 版本管理

```bash
# 查看可用的 Stack 版本
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  "http://${AMBARI_HOST}:${PORT}/api/v1/stacks"

# 查看当前集群的 Stack 版本
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  "${BASE_URL}?fields=Clusters/desired_stack_version"

# 查看 Stack 详情（如 HDP 3.1）
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  "http://${AMBARI_HOST}:${PORT}/api/v1/stacks/HDP/versions/3.1"
```

### Repository（仓库）管理

```bash
# 查看当前仓库配置
# repositories 配置文件路径
/etc/ambari-server/conf/ambari.properties  # Server 端
cat /etc/ambari-agent/conf/ambari-agent.ini  # Agent 端

# 通过 REST API 查看仓库配置
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  "http://${AMBARI_HOST}:${PORT}/api/v1/stacks/HDP/versions/3.1/repository_versions"
```

### 滚动升级（Rolling Upgrade）

滚动升级流程（通过 REST API）：

```bash
# 1. 创建升级计划
# 获取兼容的升级目标
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  "${BASE_URL}/upgrade_out?target_stack=HDP-3.2"

# 2. 开始升级
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  -X POST -d '{
    "Upgrade": {
      "direction": "UPGRADE",
      "repository_version_id": <repo_version_id>,
      "upgrade_type": "ROLLING",
      "fail_on_check_warning": false
    }
  }' "${BASE_URL}/upgrade"

# 3. 查看升级进度
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  "${BASE_URL}/upgrade"

# 4. 获取某个升级任务的详情
UPGRADE_ID="1"
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  "${BASE_URL}/upgrades/${UPGRADE_ID}"

# 5. 查看各升级组状态
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  "${BASE_URL}/upgrades/${UPGRADE_ID}/upgrade_groups"

# 6. 中止升级
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  -X PUT -d '{"Upgrade":{"request_status":"ABORTED"}}' \
  "${BASE_URL}/upgrades/${UPGRADE_ID}"
```

### 升级前检查

```bash
# 运行 Pre-Upgrade Check
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  -X POST -d '{"UpgradeCheck":{"repository_version_id":<repo_version_id>}}' \
  "${BASE_URL}/upgrade_checks"

# 查看检查结果
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  "${BASE_URL}/upgrade_checks"
```

## 7. 常用诊断命令速查

### 系统级诊断

```bash
# 查看 Ambari Server 日志最新错误
tail -100 /var/log/ambari-server/ambari-server.log | grep -i error

# 查看 Ambari Agent 日志最新错误
tail -100 /var/log/ambari-agent/ambari-agent.log | grep -i error

# 查看 Ambari Server 数据库健康状态
mysql -u ambari -p -e "SHOW TABLES;" ambari  # MySQL
sudo -u postgres psql -c "\dt" ambari       # PostgreSQL

# 验证 Ambari 端口可用
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/

# 查看集群健康概览
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  "${BASE_URL}?fields=Clusters/health_report"
```

### Agent 注册诊断

```bash
# 检查 Agent 是否成功注册到 Server
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  "${BASE_URL}/hosts"

# 检查某个主机的 Agent 心跳
curl -u ${USER_PASS} -H "X-Requested-By: ambari" \
  "${BASE_URL}/hosts/<hostname>?fields=Hosts/host_state,Hosts/host_status,Hosts/last_agent_environment"

# Agent 侧手动注册（在 Agent 节点执行）
sudo ambari-agent restart
sudo tail -f /var/log/ambari-agent/ambari-agent.log | grep "Registering"
```

### 数据库备份与恢复

```bash
# PostgreSQL 备份
pg_dump -U ambari ambari > ambari_backup_$(date +%Y%m%d).sql

# MySQL 备份
mysqldump -u ambari -p ambari > ambari_backup_$(date +%Y%m%d).sql

# 恢复
psql -U ambari ambari < ambari_backup.sql
mysql -u ambari -p ambari < ambari_backup.sql
```

### Ambari Server 管理命令

```bash
# 重置 Ambari Server 数据库（极危险，先备份！）
sudo ambari-server reset

# 更新 Ambari Server 配置
sudo ambari-server setup
sudo ambari-server setup-ldap  # LDAP 配置
sudo ambari-server setup-security  # SSL 配置

# 检查 Ambari Server 配置
sudo ambari-server setup --verbose

# 设置 JDK 路径
sudo ambari-server setup --jdk-home=/usr/lib/jvm/java-8-openjdk-amd64
```

## 8. REST API 基础速查

| 端点 | 用途 | 方法 |
|------|------|------|
| `/api/v1/clusters` | 列出所有集群 | GET |
| `/api/v1/clusters/{name}` | 集群详情 | GET |
| `/api/v1/clusters/{name}/services` | 服务列表 | GET |
| `/api/v1/clusters/{name}/services/{srv}` | 服务详情 | GET |
| `/api/v1/clusters/{name}/hosts` | 主机列表 | GET |
| `/api/v1/clusters/{name}/configurations` | 配置列表 | GET |
| `/api/v1/clusters/{name}/alerts` | 告警列表 | GET |
| `/api/v1/clusters/{name}/requests` | 请求/任务状态 | GET |
| `/api/v1/blueprints` | Blueprint 管理 | GET/POST/DELETE |
| `/api/v1/stacks` | Stack 版本管理 | GET |

## 9. 常见问题排查

### Ambari Server 无法启动
- 检查数据库连接（PostgreSQL/MySQL）
- 检查 `/var/log/ambari-server/ambari-server.log`
- 检查磁盘空间：`df -h`
- 检查 Java 版本是否兼容
- 尝试重启：`sudo ambari-server restart`

### Ambari Agent 注册失败
- 检查 Agent 端 `/etc/ambari-agent/conf/ambari-agent.ini` 中的 `hostname` 配置
- 确保 Agent 能解析 Ambari Server 主机名
- 检查 Agent 日志中的 "Connection refused" 错误
- 检查 Server 端的 agent 白名单配置

### 服务组件启动失败
- 使用 REST API 查看详细错误信息：`/requests/{id}`
- 检查各组件的日志文件（通常位于 `/var/log/<component>/`）
- 检查主机资源（内存/磁盘/CPU）
- 确认依赖服务是否已启动

### Blueprint 部署失败
- 验证 JSON 格式正确：`python -m json.tool blueprint.json`
- 确认 Stack 名称和版本正确
- 确认所有主机名可解析且 SSH 连通
- 检查 host_groups 的 cardinality 设置

## 标准命令速查

```bash
# ==== Ambari Server ====
sudo ambari-server status
sudo ambari-server start
sudo ambari-server stop
sudo ambari-server restart

# ==== Ambari Agent ====
sudo ambari-agent status
sudo ambari-agent start
sudo ambari-agent stop
sudo ambari-agent restart

# ==== REST API 基础 ====
curl -u admin:admin -H "X-Requested-By: ambari" http://localhost:8080/api/v1/clusters/
curl -u admin:admin -H "X-Requested-By: ambari" http://localhost:8080/api/v1/clusters/<cluster>/services
curl -u admin:admin -H "X-Requested-By: ambari" http://localhost:8080/api/v1/clusters/<cluster>/hosts
curl -u admin:admin -H "X-Requested-By: ambari" http://localhost:8080/api/v1/clusters/<cluster>/alerts
curl -u admin:admin -H "X-Requested-By: ambari" http://localhost:8080/api/v1/clusters/<cluster>/configurations
```
