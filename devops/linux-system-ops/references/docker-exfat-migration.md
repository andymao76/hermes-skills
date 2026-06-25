# Docker 容器数据迁移到 exfat 备份盘

将 Docker volume 中的数据迁移到 exfat 格式的备份磁盘，释放系统盘空间。

## 适用场景

- 系统盘空间不足，备份盘（exfat）空间充裕
- 需要将 Docker 容器的持久化数据迁移到外置/备份磁盘
- 容器数据包括：SQLite 数据库、用户上传文件、模型缓存等

## 核心问题

exfat 文件系统的限制：
1. **不支持符号链接** — HuggingFace 模型缓存（`snapshots/` 指向 `../../blobs/` 的 symlink）无法工作
2. **不支持文件锁（advisory lock）** — SQLite 并发写入可能异常
3. **不支持 Unix 权限** — 通过 mount 选项 `uid=`, `gid=`, `fmask=`, `dmask=` 控制
4. **大分配单元（256K）** — 小文件多时空间浪费大，`ls`/`find` 操作极慢

## HuggingFace 模型缓存行为

`huggingface_hub` 在 exfat 上尝试创建符号链接失败后，会**自动回退到复制文件**（而非创建 symlink），因此模型可以正常下载和使用。回退时会有警告，可用 `HF_HUB_DISABLE_SYMLINKS_WARNING=1` 抑制。

**关键坑点：** 如果已有旧的符号链接缓存（从 ext4 volume 的 `cp -a` 复制过来），在 exfat 上这些 symlink 会变成**断链**（文件看似存在但实际内容无效），导致错误：
```
Error: Unrecognized model in .../snapshots/xxx/
Should have a `model_type` key in its config.json.
```
**修复：** 彻底删除 cache 目录，让 huggingface_hub 重新下载（回退模式下自动复制文件）。需用 Docker root 清理（tar 复制到 exfat 的文件是 root 所有）：
```bash
docker run --rm -v /mnt/backup/<app>-data:/data alpine sh -c "rm -rf /data/cache"
```

## 操作步骤

### 1. 备份数据

```bash
# 停止容器
docker stop <container-name>

# 创建备份目录
mkdir -p /mnt/backup/<app>-data

# 复制 Docker volume 数据到备份盘
docker run --rm \
  -v <volume-name>:/from \
  -v /mnt/backup/<app>-data:/to \
  alpine sh -c "cp -a /from/. /to/"
```

### 2. 处理模型缓存（HuggingFace / sentence-transformers）

exfat 无法创建符号链接，而 HuggingFace Hub 的缓存结构依赖 symlink（`snapshots/` 目录下的文件指向 `../../blobs/`）。

**方案 A：模型缓存留在系统盘（双挂载）**
```bash
# 创建本地缓存目录
mkdir -p ~/<app>-cache

# 从 volume 复制缓存到系统盘（保留符号链接）
docker run --rm \
  -v <volume-name>:/from \
  -v ~/<app>-cache:/to \
  alpine sh -c "tar cf - -C /from cache | tar xf - -C /to"

# 容器运行时，双挂载：
docker run -d ... \
  -v /mnt/backup/<app>-data:/app/backend/data \
  -v ~/<app>-cache/cache:/app/backend/data/cache \
  ...
```

**方案 B：容器通过代理下载到备份盘**
适用于容器启动时自动下载模型且备份盘网络可达的情况。

关键：**容器内 `127.0.0.1` 指向容器自己，不是宿主机**。

方法一（推荐）— host 网络模式：
```bash
docker run -d --name <app> \
  --network host \
  -v /mnt/backup/<app>-data:/app/backend/data \
  -e HTTP_PROXY=http://127.0.0.1:7897 \
  -e HTTPS_PROXY=http://127.0.0.1:7897 \
  ...
```

方法二 — bridge 模式 + 网关 IP：
```bash
# 网关通常是 172.17.0.1
docker run -d --name <app> \
  -v /mnt/backup/<app>-data:/app/backend/data \
  -e HTTP_PROXY=http://172.17.0.1:7897 \
  -e HTTPS_PROXY=http://172.17.0.1:7897 \
  ...
```

### 3. 重建容器

```bash
# 删除旧容器
docker rm <container-name>

# 删除旧 volume（确认数据已迁移后）
docker volume rm <volume-name>
```

## 清理

```bash
# 清理废弃 volume
docker volume prune -f

# 清理废弃镜像
docker image prune -a  # 谨慎使用，会删除所有未被使用的镜像
```

## 已知坑点

- **cp -a 到 exfat 会报大量 Operation not permitted** — 这是 exfat 不支持保留 Unix 权限和符号链接的正常提示，文件内容已复制
- **模型下载失败：[Errno 97] Address family not supported by protocol** — Docker 容器无法访问外网，通常因未配代理
- **模型下载失败：[Errno 111] Connection refused** — 代理地址错误。容器内 `127.0.0.1` 是容器自身，需用 `--network host` 或宿主机网关 IP
- **容器 health: unhealthy 但 port 已监听** — 可能因为 embedding 模型加载失败导致健康检查不通过
- **--restart always 策略的容器**：用 `docker stop` 停止后不会自动重启；用 `docker kill` 停止后会自动重启；系统重启后自动拉起
- **容器被意外删除**：数据在新挂载路径（备份盘）上完好，只需重新 `docker run` 相同挂载参数即可恢复
- **host 网络模式不能同时用 -p 端口映射** — 容器直接暴露端口在宿主机上，需用环境变量 `PORT=3001` 控制容器监听端口
- **清理 root 所有的缓存文件**：`cp -a` 或 `tar` 通过 Docker 复制到 exfat 的文件 owner 是 root，普通用户 `rm -rf` 会权限不足，需用 `docker run --rm -v /mnt/backup/...:/data alpine sh -c "rm -rf /data/cache"`
