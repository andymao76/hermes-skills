# 多 Provider 大模型连通性 & 时延表格化测试

## 概述

使用 curl 直接测试所有配置的 provider 模型，以表格形式输出连通状态和时延。

## 方法论

用 `curl -s -w '\n%{http_code}\n%{time_total}'` 直接调用 chat completions API，一次遍历所有 provider。

### 密钥读取

从 config.yaml 的 api_key 字段读取（比 env 变量更可靠，因为 config.yaml 中直接设置 api_key 优先级最高）：

```bash
DEEPSEEK_KEY=$(grep -A3 '^  deepseek:' ~/.hermes/config.yaml | grep 'api_key:' | head -1 | sed 's/.*api_key: //')
SF_KEY=$(grep -A3 '^  siliconflow:' ~/.hermes/config.yaml | grep 'api_key:' | head -1 | sed 's/.*api_key: //')
SF_CN_KEY=$(grep -A3 '^  siliconflow-cn:' ~/.hermes/config.yaml | grep 'api_key:' | head -1 | sed 's/.*api_key: //')
BL_KEY=$(grep -A3 '^  bailian:' ~/.hermes/config.yaml | grep 'api_key:' | head -1 | sed 's/.*api_key: //')
GEMINI_KEY=$(grep GEMINI_API_KEY ~/.hermes/.env | head -1 | cut -d= -f2- | tr -d '"' | tr -d "'")
```

### 测试脚本模板

完整脚本见 `scripts/multi-provider-latency-table.sh`

核心模式：
1. 遍历模型列表
2. `curl -s -w '\n%{http_code}\n%{time_total}' --max-time 30`
3. 解析返回：HTTP code + total_time + body
4. Python 一行解析 choices[0].message.content
5. ANSI 颜色标记状态（绿/红/黄）
6. 表格输出

## 推理模型陷阱 (deepseek-v4-pro)

**问题**: 对推理模型使用 `max_tokens=5`~`20` 时，返回的 `content` 为空字符串，`reasoning_content` 有内容，`finish_reason` 为 `length`。

**症状**: HTTP 200、choices 存在，但 `message.content: ""` — 解析脚本会将此判为"异常"。

**原因**: deepseek-v4-pro 是推理模型，会先输出思维链（reasoning_content），小 max_tokens 全被思维链消耗，没有剩余空间给 content。

**修复**: 测试推理模型时 `max_tokens` 需 ≥100，并同时检查 `content` 和 `reasoning_content`：
```python
c = msg.get('content', '') or msg.get('reasoning_content', '')
```

## Gemini API 可达性

2026-06-09 测试结果：Google Gemini API (`generativelanguage.googleapis.com`) 从当前网络环境完全不可达，无论挂代理还是不挂代理均超时。HTTP code 返回 000，curl 超时 20s。

## 示例输出

```
╔════════════════════════════╦══════════════╦════════════════════════╦═══════════╦══════════╗
║ 模型名称                    ║ 提供商        ║ 模型 ID                ║ 状态       ║ 时延     ║
╠════════════════════════════╬══════════════╬════════════════════════╬═══════════╬══════════╣
║ DeepSeek V4 Pro (主)       ║ deepseek     ║ deepseek-v4-pro        ║ ✅ 正常    ║ 3176 ms  ║
║ DeepSeek V3 (SF国际)       ║ siliconflow  ║ deepseek-ai/DeepSeek-V3║ ✅ 正常    ║ 5537 ms  ║
║ Qwen3.5 397B (SF国内)      ║ siliconflow-cn║ Qwen/Qwen3.5-397B-A17B║ ✅ 正常    ║ 7504 ms  ║
║ Qwen-Plus (百炼)           ║ bailian      ║ qwen-plus              ║ ✅ 正常    ║  901 ms  ║
║ Gemini 2.5 Flash           ║ gemini       ║ gemini-2.5-flash       ║ ❌ 不可达  ║    -     ║
╚════════════════════════════╩══════════════╩════════════════════════╩═══════════╩══════════╝
```

## Shell 转义问题

curl 在 bash 中传 JSON payload 时，单引号和双引号嵌套容易出错，尤其是当 API key 包含特殊字符时。

**推荐方案**: 将脚本写入临时文件再执行：
```bash
cat > /tmp/test_models.sh << 'SCRIPT_EOF'
#!/bin/bash
# ... 脚本内容 ...
SCRIPT_EOF
bash /tmp/test_models.sh
```

使用 `<< 'SCRIPT_EOF'` (引号) 阻止 heredoc 内的变量展开，确保 key 不会在写入时被注入。

## API Key 注入破坏 Python/Shell 源码

**问题**: 当 Python 源代码中包含 f-string 或字符串拼接引用 API key 变量时，Hermes 的代码处理管线会在写入沙箱前将 key 值内联，导致包含特殊字符的 key（如 `AIzaSy...` 中的 `Sy` 部分）破坏字符串语法。

**症状**: `SyntaxError: unterminated string literal` 

**修复**: 
- 在 execute_code 中，用 `subprocess.run(["bash", "-c", "grep ..."])` 运行时读取 key，不要在字符串模板中嵌入 key 变量
- 使用 header 变量拼接时，分两行构建：
  ```python
  header_value = "Bearer " + key  # key 值不会嵌入源码
  auth_header = "Authorization: " + header_value  # 整体拼接
  ```
