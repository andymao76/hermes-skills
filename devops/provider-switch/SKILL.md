---
name: provider-switch
description: 网络感知的 LLM Provider 自动切换策略 — 根据网络环境（中国/海外/代理状态）自动选择最优模型配置
trigger: 模型切换、Provider 切换、网络环境变化、出差、国内/海外切换
category: devops
---

# Provider 智能切换 (provider-switch)

## 网络模式定义

| 模式 | 判定条件 | 策略 |
|------|---------|------|
| 🇨🇳 中国模式 | 百度可达 + Google 不可达 | DeepSeek / SiliconFlow / 阿里百炼 优先 |
| 🌐 海外模式 | Google 可达 | Gemini / OpenAI / OpenRouter / Nous 优先 |
| 🔌 无代理模式 | 代理端口 7897 未 LISTEN | 国内 Provider 直连 |
| ⚠️ 降级模式 | 主 Provider 连续 3 次超时 | 切换下一个可用 Provider |

## 检测命令

```bash
# 判断当前网络模式
function net_mode() {
  local baidu=$(curl -s -o /dev/null -w "%{http_code}" https://www.baidu.com --max-time 3)
  local google=$(curl -s -o /dev/null -w "%{http_code}" https://www.google.com --max-time 3)
  local proxy=$(ss -lntp | grep -q 7897 && echo "up" || echo "down")

  if [ "$google" = "200" ]; then echo "海外模式"
  elif [ "$baidu" = "200" ]; then echo "中国模式"
  else echo "无网络"
  fi
  echo "代理状态: $proxy"
}
```

## 模型到 Provider 映射

### 日常模型 (默认)

| 用途 | 中国 | 海外 |
|------|------|------|
| 日常对话 | deepseek-v4-flash | gemini-2.5-flash |
| 深度分析 | deepseek-v4-pro | gemini-2.5-pro |
| 备用 | qwen-plus (Bailian) | nous-hermes-4 |
| 备用2 | Qwen3.6-35B (SiliconFlow) | openrouter/auto |

### 嵌入模型
- 始终使用: SiliconFlow Qwen3-Embedding-8B (中国站可达)

### 图片生成
- FAL (Nous 订阅，需代理 → 海外模式)

## 切换命令

### 交互式切换

```bash
# DeepSeek (中国)
hermes config set model deepseek-v4-flash
hermes config set provider deepseek

# Gemini (海外)  
hermes config set model gemini-2.5-flash
hermes config set provider gemini

# Bailian (中国备选)
hermes config set model qwen-plus
hermes config set provider bailian

# SiliconFlow (中国备选2)
hermes config set model Qwen/Qwen3.6-35B-A3B
hermes config set provider siliconflow-cn
```

### 自动切换脚本 (network-doctor 联动)

```python
def auto_switch():
    mode = detect_network_mode()
    if mode == "overseas":
        set_provider("gemini", "gemini-2.5-flash")
    elif mode == "china":
        if check_provider("deepseek"):
            set_provider("deepseek", "deepseek-v4-flash")
        elif check_provider("siliconflow-cn"):
            set_provider("siliconflow-cn", "Qwen/Qwen3.6-35B-A3B")
        else:
            set_provider("bailian", "qwen-plus")
    else:
        print("无网络连接，无法切换")
```

## Provider 健康检查

```bash
# DeepSeek → 期望 401
curl -s -o /dev/null -w "%{http_code}" https://api.deepseek.com/v1/models

# SiliconFlow → 期望 200
curl -s -o /dev/null -w "%{http_code}" https://api.siliconflow.cn/v1/models

# Bailian → 期望 200
curl -s -o /dev/null -w "%{http_code}" https://dashscope.aliyuncs.com/compatible-mode/v1/models
```

## ⚠️ 安全规则：只输出命令，不修改配置文件

**永远不要直接编辑 `~/.hermes/config.yaml` 或 `~/.hermes/.env`。**

只输出 `hermes config set` 命令，让用户手工执行。例如：

```
hermes config set provider deepseek
hermes config set model deepseek-v4-flash
```

**为什么：**
- 配置文件是敏感安全边界，直接修改可能触发安全策略拦截
- 用户需要看到并确认每个变更
- `hermes config set` 自带值校验和格式处理

**适用所有配置变更场景：** 切换 provider、修改模型、设置 MCP 服务器、改 Discord/Telegram 参数等，一律输出命令。

## 切换前验证

切换 provider 前必须先 curl 测试目标模型连通性，确认返回有效 content 后再输出切换命令：

```bash
# 测试目标模型
curl -X POST https://api.deepseek.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(grep DEEPSEEK_API_KEY ~/.hermes/.env | cut -d= -f2)" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"hi"}]}' \
  --max-time 10 | python3 -c "import sys,json;d=json.load(sys.stdin);print('OK:', d['choices'][0]['message']['content'][:50])"
```

未验证连通性不得输出切换命令。

## 切换验证

切换后必须验证：

```bash
# 测试新 Provider
hermes status

# 或者 curl 直接测试
curl -X POST https://api.deepseek.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(grep DEEPSEEK_API_KEY ~/.hermes/.env | cut -d= -f2)" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"hi"}]}' \
  --max-time 10 | head -c 200
```

## 旅行模式

出差海外时执行：

```bash
hermes-net-doctor --mode overseas
provider-switch --auto
```

回国后执行：

```bash
hermes-net-doctor --mode china
provider-switch --auto
```
