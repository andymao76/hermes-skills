---
name: local-llm-provider-deployment
description: 在 Linux 上部署本地 LLM 模型作为 Hermes local provider 的完整流程。包含 llama.cpp 编译、模型下载（中国镜像）、Hermes 配置、后台服务管理。适用于网络受限环境。
version: 1.0
author: andymao
category: devops
---

# 本地 LLM Provider 部署指南

## 适用场景

- 需要在 Hermes 中使用本地模型处理敏感数据（LI TAG 定义等不出本机）
- 网络环境受限（GitHub/HuggingFace 慢或被墙）
- 现有硬件资源有限但想跑轻量模型（如 Qwen2.5-1.5B）

## 快速概览

```bash
# 四步完成：
# 1. 安装 cmake + 编译 llama-server
pip install --break-system-packages -i https://pypi.tuna.tsinghua.edu.cn/simple cmake
cd ~/llama/llama.cpp && git clone --depth 1 https://github.com/ggerganov/llama.cpp.git .
cmake -B build -DLLAMA_BUILD_SERVER=ON && cmake --build build --target llama-server -j$(nproc)

# 2. 从 ModelScope 下载模型（国内镜像，速度快）
pip install modelscope -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages
python3 -c "from modelscope import snapshot_download; path = snapshot_download('Qwen/Qwen2.5-1.5B-Instruct-GGUF', cache_dir='/home/andymao/llama/models', allow_patterns='qwen2.5-1.5b-instruct-q4_k_m.gguf'); print(f'下载完成: {path}')"

# 3. 启动服务（注意: 模型最大 context 32K，用 -c 32768）
MODEL=$(find ~/llama/models -name "*.gguf" -type f | head -1)
~/llama/llama.cpp/build/bin/llama-server -m "$MODEL" --port 8080 --host 127.0.0.1 -ngl 0 -c 32768 --mlock &

# 4. 配置 Hermes（注意: 仅 API 直连可用，hermes chat 因 64K 下限不可用）
hermes config set providers.local.base_url http://127.0.0.1:8080/v1
hermes config set providers.local.default qwen2.5-1.5b-instruct-q4_k_m
hermes config set providers.local.model qwen2.5-1.5b-instruct-q4_k_m
hermes config set providers.local.api_key not-needed

# 验证 API（推荐用法）
curl -s http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5-1.5b-instruct-q4_k_m","messages":[{"role":"user","content":"你好"}],"stream":false,"max_tokens":50}'
```

## 前置条件

| 组件 | 最低要求 | 推荐配置 |
|:-----|:--------|:---------|
| CPU | x86_64, AVX2 支持 | i7-8550U 或更好 |
| RAM | 7GB 可用（1.5B 模型 + 系统） | 16GB+ |
| 磁盘 | 2GB 空闲 | 20GB+ |
| GPU | 不需要（纯 CPU） | 有 CUDA 更好 |
| 操作系统 | Linux (Ubuntu 24.04 验证) | 任何 Linux |

## 详细步骤

### 1. 编译 llama-server

```bash
mkdir -p ~/llama && cd ~/llama

# 安装 cmake（PEP 668 环境需 --break-system-packages）
pip install --break-system-packages -i https://pypi.tuna.tsinghua.edu.cn/simple cmake

# 克隆 llama.cpp（如网络慢可多次重试）
git clone --depth 1 https://github.com/ggerganov/llama.cpp.git
cd llama.cpp

# CMake 构建
cmake -B build -DLLAMA_BUILD_SERVER=ON
cmake --build build --target llama-server -j$(nproc)
# 二进制在 build/bin/llama-server
```

### 2. 下载模型（中国镜像方案）

推荐顺序：ModelScope > hf-mirror.com > HuggingFace

```bash
# 方案 A: ModelScope（推荐，速度快）
pip install modelscope -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages
python3 << 'EOF'
from modelscope import snapshot_download
path = snapshot_download(
    'Qwen/Qwen2.5-1.5B-Instruct-GGUF',
    cache_dir='/home/andymao/llama/models',
    allow_patterns='qwen2.5-1.5b-instruct-q4_k_m.gguf'
)
print(f'下载完成: {path}')
EOF

# 方案 B: hf-mirror.com（速率限制 429，备用）
HF_ENDPOINT=https://hf-mirror.com huggingface-cli download \
    Qwen/Qwen2.5-1.5B-Instruct-GGUF \
    qwen2.5-1.5b-instruct-q4_k_m.gguf \
    --local-dir ~/llama/models
```

**推荐模型选型（按 RAM 预算）：**

| 可用 RAM | 推荐模型 | 量化 | 大小 | 能力 |
|:---------|:---------|:----|:----|:-----|
| 7-8GB | Qwen2.5-1.5B | Q4_K_M | ~1.5GB | 基本文本分析 |
| 12-16GB | Qwen2.5-7B | Q4_K_M | ~4.5GB | 良好文本理解 |
| 20-24GB | Qwen2.5-14B | Q4_K_M | ~8GB | 强能力 |
| 48GB+ | Qwen2.5-72B | Q4_K_M | ~45GB | 最强 |

### 3. 启动 llama-server

⚠️ **重要：context 大小限制** — Qwen2.5-1.5B 最大支持 32K context（`-c 32768`），更大的模型（如 7B）可支持 64K+。Hermes Agent 的 system prompt 要求至少 64K，因此**小模型（≤1.5B）无法通过 `hermes chat` CLI 使用**。只能用 API 直连集成到自定义流程。

```bash
# 查找实际模型文件（ModelScope 的目录名可能包含 ___5___ 等特殊字符）
MODEL=$(find ~/llama/models -name "*.gguf" -type f | head -1)
echo "模型路径: $MODEL"

# 前台启动（测试用）
~/llama/llama.cpp/build/bin/llama-server \
    -m "$MODEL" \
    --port 8080 --host 127.0.0.1 \
    -ngl 0 -c 32768 --mlock

# 后台启动（生产用）
nohup ~/llama/llama.cpp/build/bin/llama-server \
    -m "$MODEL" \
    --port 8080 --host 127.0.0.1 \
    -ngl 0 -c 32768 --mlock > ~/llama/server.log 2>&1 &

# 验证服务是否启动（等待 5-10 秒模型加载）
sleep 5 && ss -tlnp | grep 8080

# 验证 API 是否响应
curl -s http://127.0.0.1:8080/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"model":"qwen2.5-1.5b-instruct-q4_k_m","messages":[{"role":"user","content":"你好"}],"stream":false,"max_tokens":50}'
```

### 4. 配置 Hermes Provider

```bash
# 使用 hermes config set（不要直接编辑 config.yaml）
hermes config set providers.local.base_url http://127.0.0.1:8080/v1
hermes config set providers.local.default qwen2.5-1.5b-instruct-q4_k_m
hermes config set providers.local.model qwen2.5-1.5b-instruct-q4_k_m
hermes config set providers.local.api_key not-needed

# ⚠️ 使用限制：Hermes Agent 硬性要求 64K 的 system prompt 容量
# 1.5B 及以下小模型（context ≤ 32K）无法用 hermes chat CLI 直接访问
# 只能通过 API 直连在自定义流程中使用
#
# 7B 及以上模型（context ≥ 64K，如 Qwen2.5-7B）支持 hermes chat CLI
# hermes chat --provider local --model qwen2.5-1.5b-instruct-q4_k_m

# 正确用法（API 直连）：
curl -s http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5-1.5b-instruct-q4_k_m","messages":[{"role":"user","content":"你好"}],"stream":false,"max_tokens":50}'
```

### 5. 创建自启动服务（可选）

```ini
# ~/.config/systemd/user/llama-server.service
[Unit]
Description=llama-server local LLM
After=network.target

[Service]
Type=simple
ExecStart=%h/llama/llama.cpp/build/bin/llama-server \
    -m %h/llama/models/.../*.gguf \
    --port 8080 --host 127.0.0.1 \
    -ngl 0 -c 32768 --mlock
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now llama-server
systemctl --user status llama-server
```

## Pitfalls

| 问题 | 原因 | 解决 |
|:-----|:-----|:-----|
| GitHub 下载超时 | 墙内网络 | 用 git clone 重试或换国内镜像 |
| pip install PEP 668 报错 | Ubuntu 24.04 策略 | 加 `--break-system-packages` |
| cmake 不存在 | 未安装 | `pip install cmake -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages` |
| hf-mirror 429 Too Many Requests | 速率限制 | 换 ModelScope 下载 |
| ModelScope 文件名含 __5__ 等特殊字符 | 文件名特殊字符替换 | 用 `find ~/llama/models -name "*.gguf" -type f` 查找实际路径 |
| **hermes chat --provider local 报 context 不足** | **Hermes 要求 64K，1.5B 模型只有 32K** | **改用 API 直连（curl），或用 7B 及以上模型** |
| llama-server 启动后不响应 | 模型加载中 | 等待 5-10 秒，用 ss -tlnp 确认端口 |
| `-ngl 0` 是纯 CPU 模式 | 无 NVIDIA GPU | 有 GPU 时改为 `-ngl 99` |
| Hermes config.yaml 不能直接编辑 | 安全限制 | 用 `hermes config set` 命令 |
| `cmake --build` 超时（>5分钟） | 编译耗时久 | 改用 `cd build && make -j$(nproc) llama-server`（通常更快） |

## 资源估算

启动 llama-server 后资源占用：

| 模型 | RAM 占用 | CPU 推理时 | 启动时间 |
|:-----|:--------|:----------|:---------|
| Qwen2.5-0.5B Q4 | ~500MB-1GB | ~5% | ~5秒 |
| Qwen2.5-1.5B Q4 | ~1.5-2GB | ~10-20% | ~10秒 |
| Qwen2.5-7B Q4 | ~4.5-6GB | ~50-80% | ~30秒 |

空闲时 CPU 几乎为 0（模型驻留内存但不计算）。

## 文件结构

```
~/llama/
├── llama.cpp/             # 源码（已编译，可删除 build/ 节省磁盘）
│   └── build/bin/llama-server  # 二进制
├── models/                # GGUF 模型文件
│   └── Qwen/.../*.gguf
├── server.log             # 运行日志
└── llama.zip              # 原始安装包（可删）
```

## 关联资源

- Hermes Provider 配置: `hermes config set providers.*`
- 网络诊断: `provider-switch` skill
- LI 安全红线（本地模型仅用于敏感 LI 分析）
