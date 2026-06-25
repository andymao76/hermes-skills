---
name: docker-storage-ops
description: "Docker 存储管理 — 数据卷迁移、备份、exfat 兼容性处理"
version: 1.1.0
author: Hermes Agent
tags: [docker, volume, backup, exfat, storage, migration]
---

# Docker 存储管理 (Docker Storage Ops)

Docker 数据卷的迁移、备份与恢复，特别是涉及 **exfat 文件系统** 时的兼容性处理。

## 适用场景

- 系统磁盘空间不足，需要将 Docker 数据卷迁移到备份磁盘
- 备份磁盘使用 exfat 格式（常见于移动硬盘、Windows 共享盘）
- Docker 容器数据卷的备份/恢复

## 关键知识点

### exfat 文件系统的限制

exfat 不支持以下特性，迁移到 exfat 的 Docker 数据时会遇到问题：

| 特性 | exfat 支持 | 影响 |
|------|-----------|------|
| 符号链接 (symlink) | ❌ 不支持 | HuggingFace 模型缓存无法工作 |
| Unix 文件权限/属主 | ❌ 不支持 | `cp -a` 报 `Operation not permitted` |
| 文件锁 (POSIX advisory locks) | ❌ 不支持 | SQLite WAL 模式可能异常 |

### HuggingFace 模型缓存的特殊结构

HuggingFace `sentence-transformers` 和 `faster-whisper` 的模型缓存使用 **symlink + blobs** 结构：

```
models--sentence-transformers--all-MiniLM-L6-v2/
├── blobs/           # 实际文件内容
│   ├── abc123...    # 文件内容（去重存储）
│   └── ...
├── snapshots/       # 符号链接指向 blobs
│   └── <hash>/
│       ├── config.json -> ../../blobs/abc123...
│       └── model.safetensors -> ../../blobs/def456...
└── refs/            # 分支引用
```

在 exfat 上复制时，符号链接会丢失，导致模型加载失败。

## 迁移工作流

### 1. 诊断当前状态

```bash
# 查看磁盘情况
df -h

# 查看 Docker 卷
docker volume ls            # 所有卷
docker system df            # Docker 占用的磁盘

# 查看容器挂载详情
docker inspect <container> --format '{{json .Mounts}}' | python3 -m json.tool

# 查看环境变量和运行参数
docker inspect <container> --format '{{range .Config.Env}}{{println .}}{{end}}'

# 查看容器重启策略
docker inspect <container> --format '{{.HostConfig.RestartPolicy.Name}}'
```

### 2. 数据复制到备份盘

```bash
# 创建备份目录
mkdir -p /mnt/backup/<app>-data

# 从 Docker volume 复制到备份盘
docker run --rm \
  -v <volume_name>:/from \
  -v /mnt/backup/<app>-data:/to \
  alpine ash -c "cp -a /from/. /to/"
```

> **注意：** exfat 上会报 `Operation not permitted`（权限/符号链接），这是正常的。关键数据文件（数据库、上传文件）会成功复制。

### 3. 处理模型缓存（如果存在）

如果容器使用了 HuggingFace 模型缓存（sentence-transformers, faster-whisper 等），需要将 `cache/` 目录保留在支持符号链接的文件系统上。

**推荐方案：双挂载（split mount）**
- 用户数据 → exfat 备份盘（数据量大但结构简单）
- 模型缓存 → ext4 系统盘（需要符号链接支持）

```bash
# 创建本地缓存目录
mkdir -p ~/<app>-cache

# 用 tar 复制缓存（保留符号链接）到系统盘
docker run --rm \
  -v <volume_name>:/from \
  -v ~/<app>-cache:/to \
  alpine sh -c "tar cf - -C /from cache | tar xf - -C /to"

# 修复权限
chown -R $(whoami):$(whoami) ~/<app>-cache/
```

### 4. 用双挂载重建容器

```bash
# 停止并删除旧容器
docker stop <container>
docker rm <container>

# 重建（关键：数据在 exfat，缓存在 ext4）
docker run -d --name <container> \
  --restart always \
  -p 127.0.0.1:<port>:<container_port> \
  -v /mnt/backup/<app>-data:/app/backend/data \
  -v ~/<app>-cache/cache:/app/backend/data/cache \
  ...其他环境变量...
  <image>
```

> Docker 中后挂载的卷优先级更高，所以 `/app/backend/data/cache` 会覆盖 `/app/backend/data` 下的同名子目录，实现混合挂载。

### 5. 验证

```bash
# 等待启动
sleep 30

# 检查容器状态
docker ps --filter name=<container>
docker inspect <container> --format '{{.State.Health.Status}}'

# 检查 HTTP 响应
curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:<port>/

# 检查挂载是否正确
docker inspect <container> --format '{{range .Mounts}}{{.Source}} -> {{.Destination}} ({{.Type}}){{printf "\n"}}{{end}}'

# 验证模型加载
docker logs <container> 2>&1 | grep -i "load\|embed\|model\|bert"
```

### 6. 清理旧 Docker 卷

确认新容器正常运行后：

```bash
# 列出所有卷
docker volume ls

# 删除特定卷
docker volume rm <volume_name>

# 清理所有未使用的卷
docker volume prune
```

### 双挂载验证命令

创建双挂载容器后，用以下命令验证挂载是否正确生效：

```bash
# 验证两个挂载都存在
docker inspect <container> --format '{{range .Mounts}}{{.Source}} -> {{.Destination}} ({{.Type}}){{printf "\n"}}{{end}}'

# 在容器内检查文件系统
docker exec <container> sh -c "mount | grep -E 'data|cache'"

# 输出示例（正确双挂载）：
# /dev/sda2 on /app/backend/data type exfat ...
# /dev/mapper/ubuntu--vg-ubuntu--lv on /app/backend/data/cache type ext4 ...
```

**关键：** 在 Docker 中，后挂载的卷优先级更高，所以先挂载 `/app/backend/data`（exfat），再挂载 `cache`（ext4）来覆盖子目录。

---

## 备份磁盘文件系统转换：exFAT → ext4

当备份盘从 exFAT 转换为 ext4 时，需要完整的数据迁移流程。exFAT 不支持符号链接和 POSIX 文件锁，转换为 ext4 后性能、兼容性显著提升。

### 适用场景

- 备份盘当前为 exFAT，需要更好支持 Linux 权限和符号链接
- Docker 数据卷迁移到备份盘后遇到 symlink/权限问题
- 需要将整个 Docker 运行环境迁移到备份盘

### 转换流程

#### 阶段 1：数据备份到系统盘临时目录

```bash
# 创建临时目录
mkdir -p /tmp/backup-restore

# rsync 复制（排除 exFAT 回收站，加快速度）
rsync -avh --progress \
  --exclude='.Trash-1000' \
  --exclude='$RECYCLE.BIN' \
  --exclude='System Volume Information' \
  /mnt/backup/ /tmp/backup-restore/
```

**注意：** 首次 rsync 可能因 exFAT 读取速度慢耗时较长（~59G 数据约 10-20 分钟）。rsync 支持断点续传，中断后再次运行会自动跳过已复制文件。

#### 阶段 2：校验完整性

```bash
# 文件数对比
echo "源: $(find /mnt/backup/ -not -path '*/.Trash*' -not -path '*/$RECYCLE*' -not -path '*/System Volume Information*' -type f | wc -l)"
echo "备份: $(find /tmp/backup-restore/ -type f | wc -l)"

# rsync 增量检查（检查是否还有未复制文件）
rsync -avhn --delete \
  --exclude='.Trash-1000' \
  --exclude='$RECYCLE.BIN' \
  --exclude='System Volume Information' \
  /mnt/backup/ /tmp/backup-restore/
```

rsync dry run 输出为空表示无遗漏 —— 文件数一致 + 无 rsync 差异就算验证通过。

> **注意：** du -sh 显示的"数据量"在 exFAT 和 ext4 上会不同。exFAT 分配单元大（~256KB），报告的是"已分配空间"而非"实际数据大小"。ext4 报告的是文件实际大小。60G exFAT ≈ 32G 实际数据是正常的。

#### 阶段 3：格式化

```bash
# 卸载（如果无法卸载，用 lazy 模式）
sudo umount -l /mnt/backup

# 格式化
sudo mkfs.ext4 /dev/sda2 -L BACKUP

# 挂载
sudo mount /dev/sda2 /mnt/backup
sudo chown andymao:andymao /mnt/backup
```

#### 阶段 4：数据恢复

```bash
# rsync 回写（ext4 → ext4，速度快很多）
rsync -avh --progress /tmp/backup-restore/ /mnt/backup/
```

#### 阶段 5：更新 fstab

```bash
# 获取新 UUID
lsblk /dev/sda2 -o UUID

# 替换 fstab 中的 exfat 行
sudo sed -i 's|旧UUID /mnt/backup exfat|新UUID /mnt/backup ext4 defaults 0 2|' /etc/fstab
```

#### 阶段 6：清理临时数据

```bash
rm -rf /tmp/backup-restore/
df -h /   # 确认系统盘空间已恢复
```

### 验证

| 检查项 | 命令 |
|--------|------|
| 文件系统类型 | `lsblk /dev/sda2 -o NAME,FSTYPE,SIZE,MOUNTPOINT` |
| 文件数一致性 | `find /mnt/backup/ -not -path '*/lost+found/*' -type f \| wc -l` |
| 空间 | `df -h /mnt/backup/` |
| fstab 挂载 | `mount \| grep backup` |

---

## Docker 数据根目录迁移到外部磁盘

将 Docker 的完整数据目录（镜像、容器、卷、构建缓存）从系统盘迁移到备份盘，解放系统盘空间。

### 迁移流程

```bash
# 1. 先停 socket 再停 docker（重要：顺序不能反！）
sudo systemctl stop docker.socket    # 先停 socket，防止自动唤醒
sudo systemctl stop docker           # 再停 docker 服务

# 2. 在目标盘创建数据目录
sudo mkdir -p /mnt/backup/docker

# 3. 配置 daemon.json
sudo tee /etc/docker/daemon.json <<'EOF'
{
  "data-root": "/mnt/backup/docker"
}
EOF

# 4. 迁移现有数据
sudo rsync -avh /var/lib/docker/ /mnt/backup/docker/

# 5. 备份原目录
sudo mv /var/lib/docker /var/lib/docker.bak

# 6. 启动（先启动 docker，socket 会自动跟随）
sudo systemctl start docker docker.socket

# 7. 验证
docker info | grep "Docker Root Dir"
docker ps

# 8. 确认无误后删除原目录备份
sudo rm -rf /var/lib/docker.bak
```

### Pitfall：docker.socket 的自动唤醒陷阱

**问题：** 直接 `sudo systemctl stop docker` 后，docker.socket 仍在运行。当有程序通过 Docker socket（`/var/run/docker.sock`）发起请求时，systemd 会自动唤醒 docker.service，导致数据迁移过程中 Docker 进程重新启动。

**症状：**
```bash
$ sudo systemctl stop docker
$ sudo rsync -avh /var/lib/docker/ /mnt/backup/docker/
# 中途 Docker 自动启动，迁移失败
```

**正确做法：**
```bash
# 必须先停 socket
sudo systemctl stop docker.socket
# 再停 docker
sudo systemctl stop docker
# 恢复时
sudo systemctl start docker docker.socket
```

### 验证迁移后路径

```bash
# 确认 Docker Root Dir 已指向新路径
docker info 2>/dev/null | grep "Docker Root Dir"
# 输出示例: Docker Root Dir: /mnt/backup/docker

# 确认旧路径已被替换
ls -la /var/lib/docker      # 应该不存在或指向新位置
```

### 确认容器仍在 BACKUP 盘运行

```bash
# 重建所需的容器（如 Open WebUI）
docker run -d --name open-webui \
  --restart unless-stopped \
  -p 127.0.0.1:3001:8080 \
  -v /mnt/backup/open-webui-data:/app/backend/data \
  -e PORT=8080 \
  ...

# 验证新容器运行在新的 data-root 上
docker info 2>/dev/null | grep "Docker Root Dir"
# 应显示 /mnt/backup/docker
```

> **注意：** 迁移后旧容器数据丢失（旧的 container/volume 在 `/var/lib/docker/` 下已备份并删除）。需重新 `docker run` 重建容器，挂载 BACKUP 盘上的数据卷。

当宿主机通过代理（Clash/Clash Verge 等）联网时，Docker 容器默认无法使用宿主机代理，因为容器内 `127.0.0.1` 指向容器自己，不是宿主机。

### 症状

| 错误消息 | 含义 |
|---------|------|
| `ConnectError: [Errno 97] Address family not supported by protocol` | 容器完全无法联网（IPv6 问题或代理不通） |
| `ConnectError: [Errno 111] Connection refused` | 容器尝试连接 `127.0.0.1:PORT` 但宿主机代理不在那里 |
| `Cannot determine model snapshot path` | 模型下载失败 |
| `Name or service not known` | DNS 解析失败 |

### 解决方案对比

| 方案 | 优点 | 缺点 |
|------|------|------|
| **`--network host`**（推荐） | 最简单，共享宿主机网络栈，`127.0.0.1` 直接指向宿主机 | 容器端口直接暴露在宿主机上（无端口映射隔离） |
| **Docker bridge + 网关 IP** | 保留端口映射 | 需知道 Docker 网关 IP（通常 `172.17.0.1`），可能随环境变化 |

### 方案 A：host 网络模式

```bash
docker run -d --name <container> \
  --network host \                    # 关键：共享宿主机网络
  -e HTTP_PROXY=http://127.0.0.1:7897 \
  -e HTTPS_PROXY=http://127.0.0.1:7897 \
  -e NO_PROXY=localhost,127.0.0.1 \
  ...
  <image>
```

**注意端口映射变化：** `--network host` 模式下 `-p` 参数无效！容器监听的端口直接在宿主机上以相同端口号暴露。如果需要改变端口，通过环境变量配置：

```bash
# Open WebUI 示例：用 PORT 环境变量改端口
docker run -d --name open-webui \
  --network host \
  -e PORT=3001 \                     # host 模式下直接控制监听端口
  ...
  ghcr.io/open-webui/open-webui:main
```

### 方案 B：bridge 网关 IP

```bash
# 获取 Docker 网关 IP
ip route show default | awk '{print $3}'       # 或
docker network inspect bridge --format '{{(index .IPAM.Config 0).Gateway}}'

# 使用网关 IP 而非 127.0.0.1
docker run -d --name <container> \
  -e HTTP_PROXY=http://172.17.0.1:7897 \       # 宿主机真实 IP，不是 127.0.0.1
  -e HTTPS_PROXY=http://172.17.0.1:7897 \
  ...
  <image>
```

### 验证代理是否在容器内生效

```bash
# 在容器内测试外网连通性
docker exec <container> curl -s --connect-timeout 5 https://huggingface.co/ | head -c 100

# 如果返回 HTML 内容，说明代理工作正常
# 如果报错，先检查宿主机代理是否运行
ss -tlnp | grep 7897                    # 确认代理端口在宿主机上监听
```

---

## 常见陷阱

### Pitfall 1：Open WebUI 嵌入模型崩溃循环（exfat 最常见故障）

**症状：** Docker 容器启动后很快 crash-restart 循环，`docker ps` 显示 `Restarting (1)`，`health: starting` 永不变为 healthy。

**错误日志：**
```
ValueError: No embedding model is loaded.
Set RAG_EMBEDDING_MODEL to a valid SentenceTransformer model name,
or configure an external RAG_EMBEDDING_ENGINE (ollama, openai, azure_openai).
```

**根因分析：** 当 Open WebUI 数据目录在 exfat 上时，嵌入模型加载有三重风险：

| 问题 | 说明 |
|------|------|
| 模型缓存丢失 | exfat 不支持 symlink，HuggingFace 的 snapshot→blobs 结构无法正确展开 |
| 首次下载超时 | 容器启动后需从 HF 下载模型文件（数百 MB），可能因代理/限速超时 |
| 健康检查过快 | Docker health check 在模型加载完之前超时 → 标记 unhealthy → 重启 → 死循环 |

**修复方案（按推荐优先级排列）：**

**方案 A（推荐，最快）：使用外部嵌入 API**
重建容器，用 OpenAI 兼容 API 替代本地嵌入模型：

```bash
docker rm -f open-webui
docker run -d --name open-webui \
  --restart unless-stopped \
  -p 127.0.0.1:3001:8080 \
  -v /mnt/backup/open-webui-data:/app/backend/data \
  -e PORT=8080 \
  -e RAG_EMBEDDING_ENGINE=openai \
  -e OPENAI_API_BASE_URL=http://localhost:9099/v1 \
  -e OPENAI_API_KEY="" \
  ghcr.io/open-webui/open-webui:main
```

优点：无需下载模型、不依赖 exfat 的符号链接支持、启动即用。
缺点：需要有个 OpenAI 兼容的嵌入 API 服务在运行。

**方案 B：双挂载（数据在 exfat，缓存到 ext4）**
```bash
# 创建本地缓存目录
mkdir -p ~/open-webui-cache

# 从容器复制已有缓存（如果有）
docker run --rm -v open-webui:/from -v ~/open-webui-cache:/to \
  alpine sh -c "tar cf - -C /from cache | tar xf - -C /to"
chown -R $(whoami):$(whoami) ~/open-webui-cache/

# 重建容器，缓存覆盖到 ext4
docker rm -f open-webui
docker run -d --name open-webui \
  --restart unless-stopped \
  -p 127.0.0.1:3001:8080 \
  -v /mnt/backup/open-webui-data:/app/backend/data \
  -v ~/open-webui-cache/cache:/app/backend/data/cache \
  -e PORT=8080 \
  ghcr.io/open-webui/open-webui:main
```

优点：保留本地嵌入，离线可用。
缺点：需要在 ext4 上预留额外空间放缓存。

**方案 C：使用更小的嵌入模型（减少下载时间和缓存需求）**
将 `RAG_EMBEDDING_MODEL` 改为更轻量的模型如 `TaylorAI/bge-micro-v2`（仅 30MB vs all-MiniLM-L6-v2 的 80MB）。

**诊断技巧：**
```bash
# 1. 看容器状态，确认是否在重启循环
docker ps --filter name=open-webui --format "table {{.Names}}\t{{.Status}}"

# 2. 看最后几行日志，定位错误
docker logs open-webui --tail 30 2>&1

# 3. 看健康检查详情
docker inspect open-webui --format '{{json .State.Health}}' | python3 -m json.tool

# 4. 测试端口是否可访问
curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://localhost:3001/
```

**注意：** 不要傻等容器自己恢复——crash loop 中的容器会不断重启，永远不会自己变 healthy。必须 `docker rm -f` 后重建。

### Pitfall 2：Docker inspect 中的密钥遮蔽

Docker 会遮蔽 `.Env` 中的敏感环境变量（`OPENAI_API_KEY`、`TIKTOKEN_ENCODING_NAME` 等），输出为 `***`。

```bash
# 被遮蔽的变量显示为 ***
docker inspect <container> --format '{{range .Config.Env}}{{println .}}{{end}}'

# 解决方法：从原始启动命令或 docker-compose 中获取
# 对于 Open WebUI，密钥通常自动生成，无需手动指定
```

### Pitfall 3：区分"启动慢"与"崩溃循环"

首次在 exfat 上启动 Open WebUI 时，SentenceTransformer 模型加载需要时间（可能 60-120 秒）。但必须区分：

| 状态 | 容器信息 | 如何处理 |
|------|---------|---------|
| **正常启动慢** | `Up 2 minutes (health: starting)` | 等待 60-120 秒，`docker logs` 显示模型下载进度 |
| **崩溃循环** | `Restarting (1)` 或 `Up 10 seconds (health: unhealthy)` | 必须 `docker rm -f` 后重建，等多久都不会好 |

**判断标准：** 查看容器运行时间——如果每次都是几秒到十几秒就重启，说明是崩溃循环。如果持续运行 60+ 秒仍为 `health: starting`，可能是正常慢启动。

### Pitfall 4：重启策略

迁移后确保容器有 `--restart always`（或 `unless-stopped`），避免系统重启后容器无法自动启动。

### Pitfall 5：host.docker.internal 在 Linux 上的兼容性

Open WebUI 使用 `RAG_EMBEDDING_ENGINE=openai` + `OPENAI_API_BASE_URL=http://host.docker.internal:9099/v1` 时，`host.docker.internal` 在 Linux 上默认不支持（此域名是 Docker Desktop for Mac/Windows 的特性）。

**症状：** Open WebUI 容器启动后 embedding 请求失败，日志显示连接被拒绝。

**解决方案：**

```bash
# 方案 A：添加 host-gateway 映射
docker run -d --name open-webui \
  --add-host host.docker.internal:host-gateway \
  ...

# 方案 B：直接用宿主机 IP 替代（推荐，更通用）
docker run -d --name open-webui \
  -e OPENAI_API_BASE_URL=http://172.17.0.1:9099/v1 \
  ...

# 方案 C：使用 --network host 模式（端口直接暴露）
docker run -d --name open-webui \
  --network host \
  -e PORT=3001 \
  -e OPENAI_API_BASE_URL=http://127.0.0.1:9099/v1 \
  ...
```

**注意：** `--network host` 模式下 `-p` 参数无效，容器端口直接绑定到宿主机。Open WebUI 通过 `PORT=3001` 控制监听端口。

```bash
# 检查
docker inspect <container> --format '{{.HostConfig.RestartPolicy.Name}}'
```

## 快速参考

```bash
# 查看所有 Docker 卷大小
docker run --rm -v <volume>:/data alpine du -sh /data/

# 从容器提取完整 env
docker inspect <container> | python3 -c "
import sys,json
data = json.load(sys.stdin)
env = data[0]['Config']['Env']
for e in env:
    print(e)
"

# 检查挂载点（容器内视角）
docker exec <container> sh -c "mount | grep -E 'data|cache'"
```
