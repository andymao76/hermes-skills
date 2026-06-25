---
name: open-webui
description: >-
  Open WebUI 自托管 AI 平台的安装、配置、运维全指南。覆盖 Docker/Python 部署、模型连接、Hermes Bridge 整合、外部连接持久化、数据库操作、插件系统、故障排查。
version: 1.3.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [open-webui, ai-frontend, self-hosted, ollama, chat-ui, integration]
    related_skills: [openai-compatible-api-bridge, hermes-agent]
---

# Open WebUI 运维指南

> Open WebUI 是自托管的 AI 对话前端，支持 Ollama 和任何 OpenAI 兼容 API。141k+ GitHub Stars，V0.9.6 最新版。

## 快速识别

| 属性 | 值 |
|------|-----|
| 项目 | open-webui/open-webui (GitHub) |
| 语言 | Python 35% + Svelte 32% + JS 25% |
| 最小安装 | pip install open-webui && open-webui serve |
| 标准端口 | 8080（pip）/ 3000（Docker 默认映射） |
| 数据目录 | pip 安装：`<venv>/lib/python3.12/site-packages/open_webui/data/`；Docker：volume `open-webui:/app/backend/data` |
| 数据库 | SQLite（默认）/ PostgreSQL |
| 最新版 | V0.9.6（2026年6月，163个 Release） |

---

## 系统要求

| 资源 | 最低 | 推荐 |
|------|------|------|
| RAM | 2GB | 4GB+ |
| 磁盘 | 5GB | 10GB+ |
| Python | 3.11+ | 3.12 |
| 网络 | 可访问 HuggingFace（中国服务器需镜像） | - |

**内存说明**：Open WebUI 加载 `sentence-transformers/all-MiniLM-L6-v2`（~80MB）后常驻约 1GB+。3.6GB 服务器可运行但剩余不多。不含模型推理时的额外消耗。

---

## 安装方式

### 0. 前置检查

```bash
# Ubuntu 24.04 PEP 668 处理 —— 必须用 venv，先装 python3-venv
sudo apt install python3.12-venv -y

# 检查已有安装
python3 --version
pip --version   # 确保指向 venv 内 pip，而非系统级
```

### 1. Python pip（轻量，本机首选）

```bash
# 1. 创建虚拟环境
python3 -m venv ~/open-webui-venv
source ~/open-webui-venv/bin/activate

# 2. 安装（耗时 2-5 分钟，依赖包含 torch ~1GB、CUDA 包 ~500MB）
pip install --upgrade pip
pip install open-webui

# 3. 中国服务器先设置 HuggingFace 镜像
export HF_ENDPOINT=https://hf-mirror.com

# 4. 启动（pip 版默认 8080 端口）
open-webui serve --port 3000 --host 0.0.0.0
```

⚠️ **首次启动执行时序（1-3 分钟）：**
1. Alembic 数据库迁移（SQLite 建表，~10-30s）
2. 下载 `sentence-transformers/all-MiniLM-L6-v2`（~80MB，网络快时 ~30s，慢时 2-5min）
3. ChromaDB 初始化
4. Uvicorn 启动，开始监听端口

**验证就绪：** `ss -tlnp | grep 3000` 或日志中出现 `Uvicorn running on`。

### 1b. 中国网络环境部署（关键）

中国服务器（腾讯云/阿里云等）无法直接访问 HuggingFace，必须设置镜像：

```bash
# 启动前设置 HuggingFace 镜像站
export HF_ENDPOINT=https://hf-mirror.com

# 再启动
open-webui serve --port 3000 --host 0.0.0.0
```

**不设置 HF_ENDPOINT 的表现**：
- 日志中出现 `[Errno 101] Network is unreachable`
- 不断重试下载 `sentence-transformers/all-MiniLM-L6-v2`
- 端口一直不监听，`cat /tmp/ow.log | grep "unreachable\|retry"` 可确认

**常见镜像站**：
| 镜像 | 地址 | 说明 |
|------|------|------|
| HF Mirror（推荐） | `https://hf-mirror.com` | 最稳定，pip/snapshot 都走镜像 |
| ModelScope | 不推荐 | 仅部分模型镜像，不完整 |

**⚠️ 关键陷阱：**
1. `HF_ENDPOINT` **必须在启动前设置**为环境变量（`export`），不能只写进 `.env` 文件
2. 如果使用 `sudo -u user` 或 `systemd` 启动，`WorkingDirectory` 必须指向用户家目录——否则 Open WebUI 在当前 CWD 找 `.env` 和 `.webui_secret_key` 会报 `PermissionError`
3. **不能**通过设置 `RAG_EMBEDDING_MODEL=""` + `RAG_EMBEDDING_ENGINE=""` 跳过模型下载，Open WebUI 会报 `ValueError: No embedding model is loaded`
4. **解决方案**：用 `HF_ENDPOINT` 让模型从国内镜像下载，而非跳过模型

### 2. Docker（生产环境推荐）

**CPU 版（本地 Ollama）：**
```bash
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui --restart always \
  ghcr.io/open-webui/open-webui:main
```

**GPU 版（CUDA）：**
```bash
docker run -d -p 3000:8080 --gpus all \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui --restart always \
  ghcr.io/open-webui/open-webui:cuda
```

**代理场景（中国服务器，通过 Clash 等代理访问 HuggingFace）：**
服务器若通过本地代理（如 Clash Verge 127.0.0.1:7897）访问外网，Docker bridge 网络模式下容器内 `127.0.0.1` 指向容器自身而非宿主机，代理不可达。

**方案 A（推荐）：host 网络模式** — 容器共享宿主机网络栈，`127.0.0.1:7897` 直接可用：
```bash
docker run -d \
  --restart always \
  --network host \
  -v /mnt/backup/open-webui-data:/app/backend/data \
  -e PORT=3001 \
  -e RAG_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2 \
  -e AUXILIARY_EMBEDDING_MODEL=TaylorAI/bge-micro-v2 \
  -e HF_HUB_DISABLE_SYMLINKS_WARNING=1 \
  -e HTTP_PROXY=http://127.0.0.1:7897 \
  -e HTTPS_PROXY=http://127.0.0.1:7897 \
  ghcr.io/open-webui/open-webui:main
```
注意：host 网络模式下 `-p` 端口映射无效，用 `PORT=3001` 环境变量控制监听端口。`0.0.0.0:3001` 绑定到所有接口。

**方案 B：bridge 网络 + Docker 网关 IP** — 保留端口映射，用 Docker bridge 网关 IP 访问宿主机代理：
```bash
docker run -d \
  --restart always \
  -p 127.0.0.1:3001:8080 \
  -v /mnt/backup/open-webui-data:/app/backend/data \
  -e RAG_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2 \
  -e AUXILIARY_EMBEDDING_MODEL=TaylorAI/bge-micro-v2 \
  -e HF_HUB_DISABLE_SYMLINKS_WARNING=1 \
  -e HTTP_PROXY=http://172.17.0.1:7897 \
  -e HTTPS_PROXY=http://172.17.0.1:7897 \
  ghcr.io/open-webui/open-webui:main
```
`172.17.0.1` 是默认 Docker bridge 网关。非默认网络时用 `docker network inspect bridge` 查 Gateway 地址。

**exfat/外接磁盘数据挂载：**
若系统盘空间不足，可将数据目录挂载到外接（exfat）备份盘。注意：
- exfat **不支持符号链接**，HuggingFace 模型缓存（snapshots/blobs 结构依赖 symlink）需特殊处理
- 首次迁移时**清空目标盘的 cache/ 目录**，让容器重新下载模型——`huggingface_hub` 在无法创建符号链接时会自动回退为复制文件
- 迁移流程见下方「Docker Volume 迁移到外部磁盘」

**捆绑 Ollama 版：**
```bash
docker run -d -p 3000:8080 --gpus=all \
  -v ollama:/root/.ollama \
  -v open-webui:/app/backend/data \
  --name open-webui --restart always \
  ghcr.io/open-webui/open-webui:ollama
```

**仅用 OpenAI API（无本地模型）：**
```bash
docker run -d -p 3000:8080 \
  -e OPENAI_API_KEY=your_secret_key \
  -v open-webui:/app/backend/data \
  --name open-webui --restart always \
  ghcr.io/open-webui/open-webui:main
```

### 3. systemd 服务（生产环境推荐）

```ini
# /etc/systemd/system/open-webui.service
[Unit]
Description=Open WebUI - AI Chat Frontend
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=<实际运行用户>
WorkingDirectory=/home/<用户>
Environment=HF_ENDPOINT=https://hf-mirror.com   # 中国服务器必填
ExecStart=/home/<用户>/open-webui-venv/bin/open-webui serve --port 3000 --host 0.0.0.0
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo cp open-webui.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now open-webui
sudo systemctl status open-webui
```

**关键细节**：
- `WorkingDirectory` 必须设置到用户家目录——否则 Open WebUI 找不到 `.env` 和 `.webui_secret_key`
- `HF_ENDPOINT` 必须写在 `Environment=` 中，不是写在 ExecStart 的 shell 变量里
- 内存占用高（~1GB+），3.6GB RAM 服务器可运行但需注意剩余容量

### 4. Kubernetes（Helm）

```bash
helm repo add open-webui https://helm.openwebui.com
helm install open-webui open-webui/open-webui
```

---

## 连接模型供应商

Open WebUI 支持三种模型源：

### 方式一：Ollama（本地模型）
无需配置，自动检测同机 Ollama（默认 http://localhost:11434）。
容器内需设置 `OLLAMA_BASE_URL` 指向宿主机。

### 方式二：OpenAI 兼容 API
Admin Settings → Connections → OpenAI API，填写：
- API URL: `http://localhost:9099/v1`（Hermes Bridge 地址）
- API Key: 空或你的 key

### 方式三：外部供应商
内置支持 OpenAI、Anthropic、GroqCloud、Mistral、OpenRouter 等。

---

## Hermes Bridge 整合

### 架构

```
Open WebUI (3000) → Hermes Bridge (9099) → Hermes CLI → LLM Provider
                     OpenAI 兼容代理        后台调用         SiliconFlow/DeepSeek
```

### 管理命令

```bash
# Hermes Bridge（API 代理）
~/.hermes/scripts/hermes-bridge.sh start|stop|restart|status|logs

# Open WebUI
~/.hermes/scripts/open-webui.sh start|stop|restart|status|logs
```

### 外部连接持久化

Open WebUI 重启后，通过 API 配置的外部连接（Settings 中手动添加）会丢失。
管理脚本在 `start` 后自动通过 API 重新配置：

```bash
# 获取 token
TOKEN=$(curl -s -X POST http://localhost:3000/api/v1/auths/signin \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"your_password"}' | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('token',''))")

# 配置外部连接
curl -s -X POST http://localhost:3000/api/v1/configs/connections \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ENABLE_DIRECT_CONNECTIONS":true,
    "ENABLE_BASE_MODELS_CACHE":true,
    "OPENAI_API_BASE_URLS":"http://localhost:9099/v1",
    "OPENAI_API_KEYS":""
  }'
```

---

## 数据库操作

SQLite 数据库路径取决于安装方式：

| 安装方式 | 数据库路径 |
|----------|-----------|
| pip 安装（venv） | `<venv>/lib/python3.12/site-packages/open_webui/data/webui.db` |
| Docker | `open-webui:/app/backend/data/webui.db`（Docker volume） |
| 系统级 pip | `~/.open-webui/data/webui.db` |

> **pip 安装的数据目录在 venv 包目录内**，不在 `~/.open-webui/`。备份时注意路径。数据库文件属主是运行用户，需要 sudo 或同用户才能访问。

### 查找数据库位置

```bash
# 通过运行进程查找
ls -la /proc/$(pgrep -f "open-webui serve" | head -1)/fd/ 2>/dev/null | grep webui.db

# 全盘搜索
find / -name "webui.db" -type f 2>/dev/null

# 查看表结构
python3 -c "
import sqlite3
conn = sqlite3.connect('path/to/webui.db')
tables = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()
print([t[0] for t in tables])
"
```

```bash
# 查看用户
sqlite3 webui.db "SELECT id, name, email FROM user;"

# 查看认证信息
sqlite3 webui.db "SELECT email, password FROM auth;"

# 修改密码（需要 bcrypt hash）
python3 -c "
import bcrypt
h = bcrypt.hashpw(b'new_password', bcrypt.gensalt(12))
print(h.decode())
"
sqlite3 webui.db "UPDATE auth SET password='$HASH' WHERE email='user@example.com';"

# 查看系统配置
sqlite3 webui.db "SELECT id, data FROM config WHERE id=1;"
```

> config 表的 `data` 字段是 JSON，包含 `default_models`、`default_prompt_suggestions` 等配置。

### 设置默认模型

```python
# 通过 SQLite 直接设置
import json, sqlite3
conn = sqlite3.connect("webui.db")
row = conn.execute("SELECT data FROM config WHERE id=1").fetchone()
cfg = json.loads(row[0])
cfg["default_models"] = ["deepseek-chat", "siliconflow"]
conn.execute("UPDATE config SET data=? WHERE id=1", (json.dumps(cfg),))
conn.commit()
```

---

## 插件系统

Open WebUI 支持四种插件类型（通过 Pipelines 框架）：

| 类型 | 作用 | 示例 |
|------|------|------|
| **Tools** | 工具函数（函数调用） | 搜索、计算、数据库查询 |
| **Pipes** | 模型管道（请求拦截/转换） | 翻译、内容过滤、限流 |
| **Filters** | 过滤器（输入/输出处理） | 敏感词过滤、格式检查 |
| **Actions** | 自定义操作 | 发送 webhook、创建工单 |

Pipelines 是独立的 Python 服务，通过 Open WebUI 的 `/pipelines` 端点连接。
`pip install open-webui[plugins]` 可启用插件支持。

---

## 故障排查

### 外部连接重启丢失
**问题：** 重启后 Settings 中配置的外部连接消失。
**原因：** Open WebUI 的 connections 配置不持久化到 SQLite。
**解决：** 用 `open-webui.sh start` 启动（自动 API 配置），或在环境变量中设置 `OPENAI_API_BASE_URLS`。

### 端口冲突
```bash
# 检查端口占用
ss -tlnp | grep -E '3000|9099'
# 强制杀掉旧进程
kill -9 $(lsof -ti:3000) 2>/dev/null
```

### 首次启动后端口仍未监听

**问题：** 启动后 `ss -tlnp | grep 3000` 无输出，日志停留在 Alembic migration。
**原因：** 首次启动有三件事按序执行：
1. Alembic 数据库迁移（SQLite 建表，通常 <30s）
2. 下载 sentence-transformers 模型（~80MB，网络慢时 1-5 分钟）
3. ChromaDB 初始化 + Uvicorn 启动

**诊断：**
```bash
# 查看完整日志，定位卡在哪一步
cat /tmp/ow.log | grep -i "error\|exception\|timeout\|unreachable\|retry"
# 若看到 [Errno 101]，说明 HuggingFace 被墙 → 设置 HF_ENDPOINT 后重启
```

**解决：**
- HuggingFace 被墙 → `export HF_ENDPOINT=https://hf-mirror.com` 后重启
- 单纯等待时间不足 → 如果服务器网络好，等 2-3 分钟即可
- 内存不足 OOM → `dmesg | tail -5` 检查进程是否被杀死

### Python 安装失败：PEP 668 / ensurepip 缺失

**问题：** `pip install open-webui` 报错提示需要 venv，或 `python3 -m venv` 报 `ensurepip is not available`。
**原因：** Ubuntu 24.04 默认不安装 `python3-venv`，且 pip 遵循 PEP 668 禁止系统级安装。
**解决：**
```bash
sudo apt install python3.12-venv -y
python3 -m venv ~/open-webui-venv
source ~/open-webui-venv/bin/activate
pip install open-webui
```

### 启动后无法访问
检查 `open-webui serve` 是否绑定 `0.0.0.0`（默认）还是 `127.0.0.1`。
```bash
# 显式指定监听地址
open-webui serve --port 3000 --host 0.0.0.0
```

### 数据库损坏
```bash
# 备份后重建
sqlite3 webui.db ".backup webui.db.bak"
# 完整性检查
sqlite3 webui.db "PRAGMA integrity_check;"
```

---

### API 端点发现

Open WebUI 提供 `/openapi.json` 端点，可导出所有 API 路由。当需要寻找正确的配置接口时，优先从此处探索：

```bash
# 导出所有 API 路由（需要管理员 token）
curl -s http://localhost:3000/openapi.json \
  -H "Authorization: Bearer $TOKEN" | \
  python3 -c "import sys,json;paths=json.load(sys.stdin).get('paths',{}); \
  config_paths=[p for p in paths if 'config' in p.lower() or 'openai' in p.lower()]; \
  print('\n'.join(sorted(config_paths)))"
```

### 管理员注册与初始化

首次部署后，通过 API 注册管理员账号（或直接在 UI 注册）：

```bash
# 注册
curl -X POST http://localhost:3000/api/v1/auths/signup \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@example.com","password":"your_password","name":"Admin"}'

# 登录获取 token
TOKEN=$(curl -s -X POST http://localhost:3000/api/v1/auths/signin \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@example.com","password":"your_password"}' | \
  python3 -c "import sys,json;print(json.load(sys.stdin).get('token',''))")
```

### 配置多个 OpenAI 兼容提供商

Open WebUI 支持为每个 OpenAI 兼容端点配置独立的 URL+Key 对，用数组形式传递：

```bash
# 添加 DeepSeek + SiliconFlow 双备用
curl -X POST http://localhost:3000/openai/config/update \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ENABLE_OPENAI_API": true,
    "OPENAI_API_BASE_URLS": [
      "https://api.deepseek.com/v1",
      "https://api.siliconflow.cn/v1"
    ],
    "OPENAI_API_KEYS": [
      "sk-deepseek-xxx",
      "sk-siliconflow-xxx"
    ],
    "OPENAI_API_CONFIGS": {}
  }'

# 验证模型列表
curl -s http://localhost:3000/openai/models \
  -H "Authorization: Bearer $TOKEN"
```

配置成功后 `openai/models` 返回 `{"data": [{"id": "deepseek-v4-flash"}, ...]}`。若返回空数组，说明 API Key 有误或端点不可达。

## 常用 API 端点

| 方法 | 路径 | 用途 |
|------|------|------|
| GET | /openapi.json | 导出所有 API 路由（接口发现用） |
| POST | /api/v1/auths/signup | 注册管理员账号 |
| POST | /api/v1/auths/signin | 登录获取 token |
| GET | /api/v1/models | 获取可用模型列表 |
| POST | /api/v1/chat/completions | 对话（OpenAI 兼容） |
| GET | /openai/config | 查看 OpenAI 连接配置 |
| POST | /openai/config/update | 修改 OpenAI 连接配置 |
| GET | /openai/models | 查看已连接的提供商模型列表 |

### OpenAI 连接 API 配置

正确的 API 载荷格式（v0.9.6）：

```bash
# 正确的字段名和类型
curl -X POST http://localhost:3000/openai/config/update \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ENABLE_OPENAI_API": true,
    "OPENAI_API_BASE_URLS": ["https://api.deepseek.com/v1"],
    "OPENAI_API_KEYS": [""],
    "OPENAI_API_CONFIGS": {}
  }'
```

**⚠️ 关键细节**：
- `OPENAI_API_BASE_URLS` 是**数组**（`["url"]`），不是字符串
- `OPENAI_API_KEYS` 也是数组，与 URL 一一对应
- `ENABLE_OPENAI_API` 必须设为 `true`，否则 /openai/models 返回 503
- `/api/v1/configs/connections` 返回的是开关状态，不用于设置 URL
- 设置后 POST /openai/models/ 返回 {"data": []} 说明 URL 合法但无 API Key

---

## 核心架构

| 层 | 技术 | 说明 |
|----|------|------|
| 前端 | Svelte + TypeScript | 响应式 UI，PWA 支持 |
| 后端 | Python (FastAPI) | API 服务，RAG 引擎 |
| 数据库 | SQLite / PostgreSQL | 用户/对话/配置存储 |
| 向量库 | ChromaDB（默认）/ PGVector / Qdrant / Milvus / ES | RAG 文档检索 |
| 模型源 | Ollama / OpenAI API / Anthropic / 任意 OpenAI 兼容 | LLM 推理后端 |
| 扩展 | Pipelines（独立 Python 服务） | 工具/管道/过滤器/操作 |

---

## 版本升级

```bash
# pip 安装
pip install --upgrade open-webui

# Docker
docker pull ghcr.io/open-webui/open-webui:main
docker stop open-webui && docker rm open-webui
# 重新运行 docker run ...（注意保留 volume）

---

## Docker Volume 迁移到外部磁盘

当系统盘空间不足时，可将 Open WebUI 的 Docker volume 数据迁移到外接备份盘。

### 场景

- 系统盘 `/` 空间紧张，备份盘 `/mnt/backup`（exfat）有大量空闲
- 需要释放 Docker volume 占用的系统盘空间

### 迁移流程

```bash
# 1. 停止容器
docker stop open-webui

# 2. 复制 volume 数据到备份盘（注意：cp 到 exfat 会丢失符号链接）
docker run --rm \
  -v open-webui:/from \
  -v /mnt/backup/open-webui-data:/to \
  alpine sh -c "cp -a /from/. /to/"

# 3. 关键：清空 exfat 上的模型缓存（HuggingFace symlink 结构在 exfat 上损坏）
docker run --rm \
  -v /mnt/backup/open-webui-data:/data \
  alpine sh -c "rm -rf /data/cache"

# 4. 删除旧容器和旧 volume
docker rm open-webui
docker volume rm open-webui

# 5. 用新挂载重建容器（带代理，让容器重新下载模型到 exfat）
docker run -d --name open-webui \
  --restart always \
  --network host \
  -v /mnt/backup/open-webui-data:/app/backend/data \
  -e PORT=3001 \
  -e RAG_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2 \
  -e AUXILIARY_EMBEDDING_MODEL=TaylorAI/bge-micro-v2 \
  -e HF_HUB_DISABLE_SYMLINKS_WARNING=1 \
  -e HTTP_PROXY=http://127.0.0.1:7897 \
  -e HTTPS_PROXY=http://127.0.0.1:7897 \
  ghcr.io/open-webui/open-webui:main
```

### 原理说明

| 问题 | 原因 | 解决 |
|------|------|------|
| `cp -a` 报 `Operation not permitted` | exfat 不支持 Unix 权限和符号链接 | 忽略即可，文件内容已复制 |
| 模型缓存报 `Unrecognized model` / `no model_type` | HuggingFace 缓存使用 symlink（snapshots→blobs），exfat 不创建链接 | **必须清空 cache/ 目录**，让 huggingface_hub 重新下载（exfat 上自动回退为复制文件） |
| `Address family not supported` / `Connection refused` | Docker bridge 网络下 `127.0.0.1` 指向容器自身 | 用 `--network host` 或 Docker 网关 IP `172.17.0.1` |
| `No embedding model is loaded` | 模型加载失败且无可用缓存 | 确保网络可达（代理设置正确）且 cache/ 目录为空 |

### 模型缓存大小

首次下载约 943MB（all-MiniLM-L6-v2 + bge-micro-v2 + faster-whisper-base），exfat 上无法使用 symlink 去重，实际占用比 ext4 上稍大。

### 还原（从备份盘回到系统盘）

反向操作：把 `/mnt/backup/open-webui-data/` 复制回新 Docker volume 即可。

---

# 自动更新
# 推荐 Watchtower 或 WUD
```

---

## 与 Hermes Agent 的分工

| 场景 | 推荐工具 |
|------|----------|
| 日常对话、写作、翻译 | Open WebUI |
| 代码问答、辅助编程 | Open WebUI |
| 执行命令、管理文件、运维操作 | Hermes CLI |
| 发消息到微信/Telegram/Discord | Hermes CLI（send_message） |
| 定时任务、自动推送 | Hermes CLI（cronjob） |
| 跨 session 记忆、技能积累 | Hermes Agent |
| 并行子代理 | Hermes Agent（delegate_task） |

两者互补。Open WebUI 提供**图形化对话体验**，Hermes 提供**工具调用和系统访问能力**。
