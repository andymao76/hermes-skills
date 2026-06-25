# Open WebUI 迁移到 exfat 备份盘完整记录

**日期：** 2026-06-15
**环境：** Ubuntu 24.04, Docker, Open WebUI v0.9.6
**目标：** 将 Open WebUI 从系统盘 Docker volume 迁移到 `/mnt/backup`（exfat 磁盘）

## 1. 原始状态

```
Docker volume "open-webui" → /app/backend/data  (系统盘, ext4, 265MB)
端口: 127.0.0.1:3001 → 8080
```

数据内容：
- `webui.db` — SQLite 数据库（~600KB）
- `uploads/` — 用户上传文件（可为空）
- `vector_db/` — Chroma 向量数据库
- `cache/` — HuggingFace 模型缓存（all-MiniLM-L6-v2, bge-micro-v2, faster-whisper）

## 2. 备份磁盘信息

```
/dev/sda2  /mnt/backup  exfat  895G  59G  836G  7%
挂载选项: rw,relatime,uid=1000,gid=1000,fmask=0133,dmask=0022
```

## 3. 迁移过程

### 第1步：停止容器并复制数据

```bash
docker stop open-webui
mkdir -p /mnt/backup/open-webui-data
docker run --rm -v open-webui:/from -v /mnt/backup/open-webui-data:/to \
  alpine ash -c "cp -a /from/. /to/"
```

**注意：** exfat 上 `cp -a` 会报 `Operation not permitted`（权限/符号链接），但关键数据文件（webui.db, uploads）会成功复制。

### 第2步：双挂载方案（旧容器删除，新容器重建）

由于 exfat 不支持符号链接，HuggingFace 模型缓存必须留在 ext4：

```bash
# 创建本地缓存目录
mkdir -p ~/open-webui-cache

# 用 tar 复制缓存（保留符号链接）
docker run --rm -v open-webui:/from -v ~/open-webui-cache:/to \
  alpine sh -c "tar cf - -C /from cache | tar xf - -C /to"

# 重建容器：数据在 exfat，缓存在 ext4
docker rm -f open-webui
docker run -d --name open-webui \
  --restart always \
  -p 127.0.0.1:3001:8080 \
  -v /mnt/backup/open-webui-data:/app/backend/data \
  -v /home/andymao/open-webui-cache/cache:/app/backend/data/cache \
  -e USE_OLLAMA_DOCKER=false \
  -e USE_EMBEDDING_MODEL_DOCKER=sentence-transformers/all-MiniLM-L6-v2 \
  -e USE_AUXILIARY_EMBEDDING_MODEL_DOCKER=TaylorAI/bge-micro-v2 \
  -e OLLAMA_BASE_URL=/ollama \
  -e WHISPER_MODEL=base \
  -e SCARF_NO_ANALYTICS=true \
  -e DO_NOT_TRACK=true \
  -e ANONYMIZED_TELEMETRY=false \
  ghcr.io/open-webui/open-webui:main
```

### 第3步：移除缓存挂载，改用代理下载

用户要求模型也放备份盘，于是清除本地缓存并用代理下载：

```bash
# 删除旧容器和本地缓存
docker rm -f open-webui
# 用 Docker 删除 root 所有的文件
docker run --rm -v /home/andymao/open-webui-cache/cache:/data \
  alpine sh -c "rm -rf /data/* && rm -rf /data/.* 2>/dev/null"

# 重建，不加缓存挂载
docker run -d --name open-webui ...（同第2步但去掉 cache 挂载）

# 失败：ConnectError: [Errno 97] — 容器内网络不通
```

### 第4步：解决容器内代理问题（关键发现）

宿主机有代理 `http://127.0.0.1:7897`，但 Docker bridge 模式下容器内 `127.0.0.1` 指向容器自己。

**方案：改为 host 网络模式**

```bash
docker rm -f open-webui
docker run -d --name open-webui \
  --restart always \
  --network host \                              # ← 关键变更
  -v /mnt/backup/open-webui-data:/app/backend/data \
  -e PORT=3001 \                                # ← host 模式下 -p 无效，用此控制端口
  -e HTTP_PROXY=http://127.0.0.1:7897 \         # ← host 模式下 127.0.0.1 指向宿主机
  -e HTTPS_PROXY=http://127.0.0.1:7897 \
  ...其他环境变量...
  ghcr.io/open-webui/open-webui:main
```

**结果：** 模型下载成功（约 2-3 分钟），HTTP 返回 200。

## 4. 关键命令速查

### 查看容器挂载
```bash
docker inspect open-webui --format '{{range .Mounts}}{{.Source}} -> {{.Destination}} ({{.Type}}){{printf "\n"}}{{end}}'
```

### 容器内检查文件系统
```bash
docker exec open-webui sh -c "mount | grep -E 'data|cache'"
```

### 查看完整环境变量（注意敏感值会被遮蔽为 ***）
```bash
docker inspect open-webui 2>/dev/null | python3 -c "
import sys,json
data = json.load(sys.stdin)
for e in data[0]['Config']['Env']:
    print(e)
"
```

### 查看当前运行状态
```bash
docker ps --filter name=open-webui --format 'table {{.Names}}\t{{.Status}}'
docker inspect open-webui --format '{{.State.Health.Status}}'
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:3001/
```

## 5. 注意事项

1. **exfat + SQLite：** exfat 不支持 POSIX 文件锁，但 Open WebUI 的 SQLite 操作在单进程场景下正常工作（WAL 模式可不用锁）。
2. **`--network host` 与多容器冲突：** 宿主机端口只能被一个容器占用。如果有多个容器需要端口映射，用 bridge 模式 + 网关 IP 代替。
3. **容器重建后 .webui_secret_key：** Open WebUI 会自动在数据目录生成此文件。如果旧密钥丢失，登录 session 会失效（需重新登录）。
4. **模型缓存位置更改：** 去掉缓存挂载后，模型直接下载到 `/mnt/backup/open-webui-data/cache/`（exfat）。`huggingface_hub` 会自动处理 symlink 创建失败的 fallback。
