---
name: local-llm-provider-deployment
description: 在 Linux 上部署/配置本地/自托管 LLM 作为 Hermes provider 的完整流程。包含 llama.cpp 编译、Ollama 远程配置、模型下载（中国镜像）、Hermes 配置（主模型 + 全部辅助模型）、后台服务管理。适用于网络受限环境或敏感数据处理。
version: 1.4
author: andymao
category: devops
---

# 本地 LLM Provider 部署与配置

## 适用场景

- 需要在 Hermes 中使用本地模型处理敏感数据（LI TAG 定义等不出本机）
- 网络环境受限（GitHub/HuggingFace 慢或被墙）
- 现有硬件资源有限但想跑轻量模型（如 Qwen2.5-1.5B）
- 已有远程 Ollama 服务器，需将 Hermes 全部流量切换到本地模型
- 需要替代在线 API Provider（如 DeepSeek），全面切换到自托管模型

## 快速概览（llama.cpp 本地部署）

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

## 快速概览（远程 Ollama 配置）

已有 Ollama 服务（远程或本地 11434 端口），几分钟完成配置：

```bash
# 1. 添加 Ollama 为自定义 provider
hermes config set providers.ollama.base_url http://<ollama_host>:11434/v1
hermes config set providers.ollama.api_key not-needed
hermes config set providers.ollama.default <model_name>
hermes config set providers.ollama.model <model_name>
hermes config set providers.ollama.context_length <context_size>

# 2. 强制覆写 context（本地模型默认 32K~40K，低于 64K 门槛）
hermes config set model.ollama_num_ctx 65536
hermes config set model.context_length 65536

# 3. 切换默认模型
hermes config set model.provider ollama
hermes config set model.default qwen2.5:7b
hermes config set model.base_url http://<ollama_host>:11434/v1

# 4. 验证连通性
curl -s http://<ollama_host>:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"<model_name>","messages":[{"role":"user","content":"你好"}],"stream":false}'

# 5. 切换全部辅助模型（见下方完整命令表）
```

## 前置条件

| 组件 | 最低要求 | 推荐配置 |
|:-----|:--------|:---------|
| CPU | x86_64, AVX2 支持 | i7-8550U 或更好 |
| RAM | 7GB 可用（1.5B 模型 + 系统） | 16GB+ |
| 磁盘 | 2GB 空闲 | 20GB+ |
| GPU | 不需要（纯 CPU） | 有 CUDA 更好 |
| 操作系统 | Linux (Ubuntu 24.04 验证) | 任何 Linux |

## 模型推荐（Ollama 场景）

已有 Ollama 服务时推荐模型组合（按用途）：

| 用途 | 推荐模型 | 参数 | 大小 | Hermes主模型? | 备注 |
|:-----|:---------|:----|:----|:-------------|:-----|
| 日常对话 | **qwen2.5:7b** | 7.6B | 4.36GB | ✅可 | tools支持，content正常 |
| 代码 Review | **qwen2.5-coder:7b** | 7.6B | 4.36GB | ✅可 | tools支持，content正常 |
| 中文分析 | qwen3:14b | 14.8B | 8.64GB | ❌不可 | reasoning字段问题 |
| 复杂推理 | deepseek-r1:7b | 7.6B | 4.36GB | ❌不可 | 无tools支持 |
| 更强模型 | qwen3:32b | 32.8B | 18.8GB | ❌不可 | reasoning字段问题 |

**⚠️ Qwen3 模型不能作为 Hermes 主模型！** 详见下方 Pitfalls。

## Ollama Provider 配置详解

### 1. 添加 provider

```bash
# 添加 Ollama 自定义 provider（远程或本地）
hermes config set providers.ollama.base_url http://<host>:11434/v1
hermes config set providers.ollama.api_key not-needed
hermes config set providers.ollama.default <model_name>
hermes config set providers.ollama.model <model_name>
hermes config set providers.ollama.context_length <model_context_size>

# ⚠️ 强制 64K 覆写（必配！不配则 _ollama_context_limit_error 报错）
# Hermes 在 conversation_loop.py 中检测 ollama_num_ctx < 64K 会拒绝运行。
# 本地模型默认 32K~40K，必须强制覆写：
hermes config set model.ollama_num_ctx 65536
hermes config set model.context_length 65536
```

**context_length 参考值：**
- qwen3:8b → 40960
- qwen2.5-coder:7b → 32768
- qwen3:14b → 40960
- deepseek-r1:7b → 131072

**⚠️ 所有本地模型 context 均低于 64K！**
Hermes 硬性要求 `MINIMUM_CONTEXT_LENGTH = 64_000`（`agent/model_metadata.py:185`），上述值都会触发 `_ollama_context_limit_error`。必须用下面两种方式之一强制覆写：

**方式 A — 配置文件覆写（推荐，qqwn3:8b 及以上适用）：**
```bash
hermes config set model.ollama_num_ctx 65536
hermes config set model.context_length 65536
```
qwen3:8b 原生支持 RoPE 扩展到 128K，覆写到 64K 完全安全。

**方式 B — Ollama Modelfile 覆写（所有模型适用）：**
```bash
ollama create <new_model_name> -f - << 'EOF'
FROM <base_model>
PARAMETER num_ctx 65536
EOF
```
Hermes 检测到 Modelfile 中有 `num_ctx` 会优先使用该值。适合希望持久化保存的场景。

### 2. 切换默认模型

```bash
# ⚠️ 先备份当前配置！切换 provider 可能导致 Hermes 不可用
# 如果新模型不工作，可快速回滚：
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak
hermes config set model.provider ollama
hermes config set model.default qwen2.5:7b     # 示例：qwen2.5 日常对话
hermes config set model.base_url http://<ollama_host>:11434/v1
```

## 备份与回滚 SOP

任何时候切换 provider 或修改 model 配置，先备份：

```bash
# 备份（修改前执行）
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak.$(date +%Y%m%d_%H%M%S)
cp ~/.hermes/.env ~/.hermes/.env.bak.$(date +%Y%m%d_%H%M%S)

# 回滚（出问题时执行）
cp ~/.hermes/config.yaml.bak.<timestamp> ~/.hermes/config.yaml
cp ~/.hermes/.env.bak.<timestamp> ~/.hermes/.env
```

注意：同时备份 `.env` 文件，因为它也包含关键的 API key 配置。

## 最佳实践：双 Provider 模式

对于无法接受本地 7B 模型推理速度的用户，推荐"API 主模型 + 本地辅助"的双 provider 架构：

```bash
# 主模型 → 线上 API（快速、高质量）
hermes config set model.provider deepseek
hermes config set model.default deepseek-v4-flash
hermes config set model.base_url https://api.deepseek.com/v1

# 本地 Ollama → 代码 Review 等敏感/离线任务
# 使用时临时指定 provider：
hermes chat -q "Review this code: ..." --provider ollama --model qwen2.5-coder:7b
```

**适用场景：**
| 流量 | 使用模型 | 原因 |
|:-----|:---------|:-----|
| 日常对话、编码、搜索 | DeepSeek API | 响应快（秒级），质量高 |
| 代码 Review | Ollama qwen2.5-coder:7b | 本地不出网，处理敏感代码 |
| LI 数据解析 | Ollama 本地模型 | 涉密数据不出本机 |

**性能基准（qwen2.5:7b + Ollama 本地）：**
- 纯推理（无工具）：~6 秒/次
- Hermes 首次调用（44 tools，~12.8K tokens 输入）：**~48 秒**以上
- 原因：Hermes 每个 API 调用携带全部工具 schema（44+ 个工具描述），输入 token 量远超纯推理

**结论：** 7B 本地模型适合工具调用少的辅助任务（如代码 Review），不适合作为主模型承载高频、多工具的日-常对话。这是硬件限制，非配置问题。

### 3. 验证连通性

```bash
# 测试 model（注意检查 content 字段是否非空）
curl -s http://<ollama_host>:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5:7b","messages":[{"role":"user","content":"你好"}],"stream":false}' \
  | python3 -c "
import sys,json; d=json.load(sys.stdin)
msg = d['choices'][0]['message']
content = msg.get('content','')
if content.strip():
    print('OK:', content[:80])
elif msg.get('reasoning',''):
    print('FAIL: reasoning only, content empty — Qwen3模型不能做主模型')
else:
    print('FAIL: empty response')
"

# 列出全部可用模型
curl -s http://<ollama_host>:11434/api/tags | python3 -m json.tool
```

### 4. 切换全部辅助模型（12+ 项）

切换主模型后，必须逐一切换所有辅助（auxiliary）配置，否则仍会用旧 provider：

```bash
# === 语义/文本类 ===
hermes config set auxiliary.compression.provider ollama
hermes config set auxiliary.compression.model <model_name>

hermes config set auxiliary.skills_hub.provider ollama
hermes config set auxiliary.skills_hub.model <model_name>

hermes config set auxiliary.approval.provider ollama
hermes config set auxiliary.approval.model <model_name>

hermes config set auxiliary.title_generation.provider ollama
hermes config set auxiliary.title_generation.model <model_name>

hermes config set auxiliary.triage_specifier.provider ollama
hermes config set auxiliary.triage_specifier.model <model_name>

hermes config set auxiliary.profile_describer.provider ollama
hermes config set auxiliary.profile_describer.model <model_name>

# === MCP / 网关类 ===
hermes config set auxiliary.mcp.provider ollama
hermes config set auxiliary.mcp.model <model_name>

# === 视觉类 ===
hermes config set auxiliary.vision.provider ollama
hermes config set auxiliary.vision.model <model_name>

# === 网页提取类 ===
hermes config set auxiliary.web_extract.provider ollama
hermes config set auxiliary.web_extract.model <model_name>

# === Kanban 类 ===
hermes config set auxiliary.kanban_decomposer.provider ollama
hermes config set auxiliary.kanban_decomposer.model <model_name>

# === Curator 类（技能生命周期）===
hermes config set auxiliary.curator.provider ollama
hermes config set auxiliary.curator.model <model_name>

# === 微信平台 ===
hermes config set weixin.provider ollama
hermes config set weixin.model <model_name>
```

**⚠️ 关键注意：** 漏掉任何一个 auxiliary 项，该功能仍会尝试走旧 provider（如 deepseek API），导致混合调用。可通过 `grep "deepseek" ~/.hermes/config.yaml | grep -v "^.*providers:"` 检查是否还有残留引用。只有 providers 定义段里的 deepseek 引用是正常的。

### 5. 一键批量切换脚本（Python）

```python
# save as: switch_provider.py
import subprocess, sys

provider = sys.argv[1] if len(sys.argv) > 1 else "ollama"
model = sys.argv[2] if len(sys.argv) > 2 else "qwen3:8b"

keys = [
    "model.provider", "model.default",
    "auxiliary.compression.provider", "auxiliary.compression.model",
    "auxiliary.skills_hub.provider", "auxiliary.skills_hub.model",
    "auxiliary.approval.provider", "auxiliary.approval.model",
    "auxiliary.title_generation.provider", "auxiliary.title_generation.model",
    "auxiliary.triage_specifier.provider", "auxiliary.triage_specifier.model",
    "auxiliary.profile_describer.provider", "auxiliary.profile_describer.model",
    "auxiliary.mcp.provider", "auxiliary.mcp.model",
    "auxiliary.vision.provider", "auxiliary.vision.model",
    "auxiliary.web_extract.provider", "auxiliary.web_extract.model",
    "auxiliary.kanban_decomposer.provider", "auxiliary.kanban_decomposer.model",
    "auxiliary.curator.provider", "auxiliary.curator.model",
    "weixin.provider", "weixin.model",
]
for k in keys:
    if k.endswith(".provider"):
        subprocess.run(["hermes", "config", "set", k, provider])
    else:
        subprocess.run(["hermes", "config", "set", k, model])
```

### 6. 验证全部切换完成

```bash
# 检查是否还有旧 provider 引用（只显示非 providers 定义段的残留）
grep -n "deepseek" ~/.hermes/config.yaml | grep -v "^.*providers:"
# 期望输出：空（只有 providers 定义段里的正常引用）

# 确认当前模型
hermes config | grep -A2 "Model"
```

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
# （agent/model_metadata.py:185 → MINIMUM_CONTEXT_LENGTH = 64_000）
# 所有本地模型（Ollama 报告的 context_length 只有 32K~40K）默认都低于此值。
# 必须强制覆盖 context 才能用 hermes chat CLI：
#
#   hermes config set model.ollama_num_ctx 65536
#   hermes config set model.context_length 65536
#
# 或者创建 Modelfile 指定 PARAMETER num_ctx 65536 后重新创建模型。
# 不覆写的模型只能通过 curl API 直连在自定义流程中使用。

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
| Hermes config.yaml 不能直接编辑 | 安全限制 | 用 `hermes config set` 命令；nested auxiliary 配置用 `auxiliary.xxx.provider` 路径 |
| `cmake --build` 超时（>5分钟） | 编译耗时久 | 改用 `cd build && make -j$(nproc) llama-server`（通常更快） |
| **patch 工具无法修改 config.yaml** | 安全限制 | 只使用 `hermes config set`，不用 `patch`/`write_file` |
| **Qwen3 reasoning 字段问题** | Qwen3 系列（qwen3:8b, qwen3:14b, qwen3:32b）通过 Ollama OpenAI 兼容 API 时，回复内容进入 `reasoning` 字段而非 `content`，`content` 永远为空字符串。Hermes 从 `content` 读取回复，因此 **Qwen3 全系不能作为 Hermes 主模型** | 只能用 qwen2.5 系列（content 正常）。测试方法：`curl -s <ollama_url>/v1/chat/completions -d '{"model":"<name>","messages":[{"role":"user","content":"hi"}],"max_tokens":50,"stream":false}' \| python3 -c "import sys,json; d=json.load(sys.stdin); print('content:', repr(d['choices'][0]['message'].get('content','')))"`。如果 content 为空、reasoning 有内容，则不适合做主模型 |
| **辅助模型仍走旧 provider** | 漏掉了某些 auxiliary 配置 | 逐项检查 `grep "deepseek" config.yaml \| grep -v providers:` |
| **config set 对 auxiliary 成功但 hermes config 仍显示旧值** | 缓存未刷新 | `hermes config` 读运行时缓存，下次 `/new` 或 restart 后显示新值 |

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
- 网络诊断 & Provider 切换: `provider-switch` skill
- LI 安全红线（本地模型仅用于敏感 LI 分析）
- Ollama 模型列表: `curl -s http://<host>:11434/api/tags | python3 -m json.tool`
- Ollama 模型 API 测试: `curl -s http://<host>:11434/v1/chat/completions -d '{"model":"<name>","messages":[{"role":"user","content":"hi"}],"stream":false}'`
- Ollama 模型兼容性验证（tools + content 字段 + context_length）: `references/ollama-model-compatibility-test.md`
- 配置残留检查: `grep -n "old_provider" ~/.hermes/config.yaml | grep -v "^.*providers:"`
- 一键批量切换脚本参考上方「一键批量切换脚本」章节
