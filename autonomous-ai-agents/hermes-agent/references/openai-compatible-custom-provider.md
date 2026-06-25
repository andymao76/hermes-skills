# 添加 OpenAI 兼容的自定义供应商

Hermes Agent 支持通过 `providers` 段添加任何 OpenAI 兼容的 API 端点作为自定义供应商。

## 通用配置模板

```yaml
providers:
  <provider-name>:                       # 自定义名称，如 siliconflow, fireworks, together
    api_key: sk-xxx                      # API Key
    base_url: https://api.example.com/v1 # OpenAI 兼容的 base URL
    default: model-name                  # 默认模型名称
    model: model-name                    # 当前使用的模型
```

## 配置方式

### 方式 A：加到 providers 段（推荐，可切换）

在 config.yaml 的 `providers:` 段添加：

```yaml
providers:
  siliconflow:
    api_key: sk-xxx
    base_url: https://api.siliconflow.cn/v1
    default: Qwen/Qwen3-235B-A22B
    model: Qwen/Qwen3-235B-A22B
```

然后在 `model:` 段引用：

```yaml
model:
  provider: siliconflow
  default: Qwen/Qwen3-235B-A22B
  model: Qwen/Qwen3-235B-A22B
```

切换时改 `model.provider` 即可。

### 方式 B：直接作为主模型

```yaml
model:
  provider: siliconflow
  base_url: https://api.siliconflow.cn/v1
  api_key: sk-xxx
  default: Qwen/Qwen3-235B-A22B
  model: Qwen/Qwen3-235B-A22B
```

## 验证 API Key

```bash
# 国内站
curl -s --connect-timeout 10 "https://api.siliconflow.cn/v1/models" \
  -H "Authorization: Bearer sk-your-key"

# 国际站（需要代理）
HTTPS_PROXY=http://127.0.0.1:7897 \
curl -s --connect-timeout 10 "https://api.siliconflow.com/v1/models" \
  -H "Authorization: Bearer sk-your-key"
```

注意：部分供应商返回裸字符串而非 JSON（如 SiliconFlow 返回 `"Api key is invalid"`），需直接看原始输出。注意 `siliconflow.com`（国际站）和 `siliconflow.cn`（国内站）的 Key 不互通。

测试聊天能力：

```bash
curl -s --connect-timeout 10 -X POST "https://api.siliconflow.cn/v1/chat/completions" \
  -H "Authorization: Bearer sk-your-key" \
  -H "Content-Type: application/json" \
  -d '{"model":"Qwen/Qwen3-235B-A22B","messages":[{"role":"user","content":"hello"}]}'
```

## 重要：国际站 vs 国内站

**同名供应商可能有国际站和国内站两个 API 端点**，它们使用不同的 API Key 和域名。

以 SiliconFlow 为例：

| 站点 | 控制台 | API 端点 | 网络要求 |
|------|--------|----------|----------|
| 国际站 (siliconflow.com) | https://cloud.siliconflow.com/me/account/ak | `https://api.siliconflow.com/v1` | 需要代理（被墙） |
| 国内站 (siliconflow.cn) | https://cloud.siliconflow.cn/account/ak | `https://api.siliconflow.cn/v1` | 国内直连 |

**关键区别：**
- 国际站和国内站的账号系统/API Key **完全独立**，互不通用
- 国际站 API 需要 `HTTPS_PROXY` 才能访问（国内服务器场景）
- 模型列表不完全相同（国际站更新更快，国内站部分模型可能延迟上架）

### 代理影响

当供应商需要代理时，影响范围取决于 Hermes 的运行模式：

**CLI 模式**：继承 shell 环境变量中的代理（`https_proxy`/`HTTP_PROXY`/`HTTPS_PROXY`）。运行 `env | grep -i proxy` 确认当前环境有代理。注意代理 URL 末尾的 `/` 是可选的，两种形式都可用：`http://127.0.0.1:7897` 和 `http://127.0.0.1:7897/`。

**Gateway 模式（systemd service）**：shell 代理不继承到 systemd。需要在 `~/.config/systemd/user/hermes-gateway.service` 中添加：
```
Environment="HTTPS_PROXY=http://127.0.0.1:7897"
Environment="HTTP_PROXY=http://127.0.0.1:7897"
Environment="ALL_PROXY=socks5://127.0.0.1:7897"
```
之后 `systemctl --user daemon-reload && systemctl --user restart hermes-gateway`。

**验证代理是否生效**（gateway 模式下）：
```bash
cat /proc/$(pgrep -f "hermes_cli.main gateway" | head -1)/environ 2>/dev/null \
  | tr '\0' '\n' | grep -i proxy
```

## 已知的 OpenAI 兼容供应商

| 供应商 | Base URL | 网络 | 备注 |
|--------|----------|------|------|
| SiliconFlow (国际) | https://api.siliconflow.com/v1 | 需代理 | 控制台: cloud.siliconflow.com |
| SiliconFlow (国内) | https://api.siliconflow.cn/v1 | 国内直连 | 控制台: cloud.siliconflow.cn |
| Fireworks AI | https://api.fireworks.ai/inference/v1 | 海外 | |
| Together AI | https://api.together.xyz/v1 | 海外 | |
| OpenRouter | https://openrouter.ai/api/v1 | 内置支持 | |
| Groq | https://api.groq.com/openai/v1 | 内置支持 | |

## 关键陷阱：`--provider` 不自动切换模型名

**重要：** 使用 `--provider siliconflow`（或任何自定义供应商）时，Hermes **不会**自动使用 `providers.siliconflow.default` 中的模型名。它会继续使用 `model.default`（或 `model.model`）中设置的值。

这意味着如果 `model.default: deepseek-chat`，但 `--provider siliconflow`，请求会带着 `deepseek-chat` 去 SiliconFlow 的 API，导致 HTTP 400 "Model does not exist"。

**解决方案（两种）：**

**方案 A：把自定义供应商设为主模型（推荐）**
```yaml
model:
  provider: siliconflow
  api_key: sk-xxx
  base_url: https://api.siliconflow.com/v1
  default: Qwen/Qwen3.5-397B-A17B
  model: Qwen/Qwen3.5-397B-A17B
```
这样直接 `hermes` 启动就是用 SiliconFlow，不需要 `--provider`。

**方案 B：显式指定 model**
```bash
# 单次查询
hermes chat -q "你好" --provider siliconflow --model "Qwen/Qwen3.5-397B-A17B"

# 交互式会话：先指定供应商和模型启动
hermes --provider siliconflow --model "Qwen/Qwen3.5-397B-A17B"
# 或者在会话内切换
/model Qwen/Qwen3.5-397B-A17B
```

## 图片生成

### 方案 1：供应商 API 脚本（推荐，无额外配置）

参见 `scripts/siliconflow-image.py` — 通过供应商的 `/v1/images/generations` 端点直接调用：

```bash
python3 scripts/siliconflow-image.py "一只橘猫，数字艺术" -m "black-forest-labs/FLUX.1-dev"
python3 scripts/siliconflow-image.py --list-models
```

**不依赖 Hermes 图片生成工具**，只需供应商 API Key。

### 方案 2：Hermes 内置 image_generate 工具（FAL 后端）

Hermes 内置的 `image_generate` 工具只使用 **FAL.ai** 作为后端，不连接供应商的图片 API。要启用它：

```bash
# 1. 去 https://fal.ai 注册获取 FAL_KEY
# 2. 设置环境变量
echo 'FAL_KEY=your-fal-key' >> ~/.hermes/.env
# 3. 重启 Hermes 会话后可用
```

注意：FAL 也在海外，需要代理环境才能访问。

### 方案 3：ComfyUI（本地 GPU）

需要本地安装 ComfyUI + GPU，参考 `skill comfyui`。

## 注意事项

- 确认你注册的是哪个站点的账号，使用对应的 Base URL
- 国际站和国内站的 API Key **不互通**，不要用错
- 如果供应商需要代理（如国内服务器访问海外 API），确保 shell 环境或 gateway/systemd service 已配置 `HTTPS_PROXY`（以及 `ALL_PROXY` 用于某些库）
- Key 添加到 `config.yaml` 即可工作，不需要写入 `.env`
- 切换供应商后需要 `/reset` 或重启会话
- 部分供应商的模型名称需要完整路径（如 `Qwen/Qwen3.5-397B-A17B`），不要加 `Pro/` 前缀除非文档要求
- 可用模型列表：`curl -s .../v1/models -H "Authorization: Bearer sk-key" | jq '.data[].id'`
