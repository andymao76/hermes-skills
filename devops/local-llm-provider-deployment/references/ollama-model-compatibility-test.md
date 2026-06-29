# Ollama 模型兼容性验证方法

验证一个 Ollama 模型是否能作为 Hermes Agent 主模型的标准化流程。

## 零、查看当前模型状态

```bash
# 查看所有可用模型
curl -s http://<ollama_host>:11434/api/tags | python3 -m json.tool

# 查看当前加载到内存中的模型（空 = 按需加载）
curl -s http://<ollama_host>:11434/api/ps | python3 -m json.tool
```

## 一、检查工具调用支持（`tools` capability）

```bash
curl -s http://<ollama_host>:11434/api/tags \
  | python3 -c "import sys,json; data=json.load(sys.stdin)
for m in data['models']:
    name = m['name']
    caps = m.get('capabilities', [])
    ctx = m['details'].get('context_length', '?')
    print(f'{name:30s} ctx={str(ctx):>7} tools={\"tools\" in caps}')
"
```

Hermes 主模型必须包含 `tools` 能力，否则无法进行函数调用。

## 二、检查 `content` 字段是否正常（Qwen3/DeepSeek-R1 检查）

```bash
# Qwen3/DeepSeek-R1 的问题：回复进入 reasoning 字段，content 为空
curl -s -X POST http://<ollama_host>:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"<model_name>","messages":[{"role":"user","content":"say hi in 3 words"}],"max_tokens":50,"stream":false}' \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
msg = d['choices'][0]['message']
content = msg.get('content','')
reasoning = msg.get('reasoning','')
print('content: ', repr(content[:100]))
print('reasoning:', repr(reasoning[:100]) if reasoning else '(empty)')
if content.strip():
    print(' content 正常 → 可做主模型')
elif reasoning.strip():
    print(' reasoning 才有内容，content 为空 → 不能做主模型')
else:
    print(' 无任何回复')
"
```

**测试结果（本机 Ollama 192.168.250.83:11434, 2026-06-29）：**

| 模型 | content | reasoning | 工具调用 | 能否做主模型 |
|:-----|:--------|:----------|:---------|:------------|
| qwen2.5:7b | 正常 | (空) | ✅ | ✅ |
| qwen2.5-coder:7b | 正常 | (空) | ✅ | ✅ |
| qwen2.5-coder:14b | 正常 | (空) | ✅ | ✅ |
| qwen2.5-7b-64k:latest | 正常 | (空) | ✅ | ✅ |
| **qwen3:8b** | `""` | **有内容** | ✅ | **❌ 不能** |
| **qwen3:14b** | `""` | **有内容** | ✅ | **❌ 不能** |
| **qwen3:32b** | `""` | **有内容** | ✅ | **❌ 不能** |
| deepseek-r1:7b | `""` | 有内容 | ❌ 无 | ❌ |
| deepseek-r1:8b | `""` | 有内容 | ❌ 无 | ❌ |
| deepseek-r1:14b | `""` | 有内容 | ❌ 无 | ❌ |

**已知原因：** Qwen3 系列和 DeepSeek-R1 系列在 Ollama 的 OpenAI 兼容 API 中，将 thinking/reasoning 阶段的内容放入 `reasoning` 字段，但最终回复没有汇总回 `content` 字段。Hermes Agent 从 `content` 读取回复，因此这两个系列都不适合作为主模型。

DeepSeek-R1 系列适合作为离线代码审查或根因分析的 reasoning 模型备用（通过 curl 直连调用）。

## 三、检查 context_length 并验证覆写生效

### 3.1 查看模型声明的 context_length（旧方式）

```bash
curl -s http://<ollama_host>:11434/api/show -d '{"model":"<model_name>"}' \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
# 从 model_info 查找 context_length
info = d.get('model_info', {})
for k, v in info.items():
    if 'context_length' in k.lower():
        print(f'{k} = {v}')
"
```

### 3.2 查看 tags 接口报告的 context_length（推荐）

```bash
curl -s http://<ollama_host>:11434/api/tags \
  | python3 -c "import sys,json; [print(f'{m[\"name\"]:30s} ctx={m[\"details\"].get(\"context_length\",\"?\")}') for m in json.load(sys.stdin)['models']]"
```

### 3.3 验证 num_ctx 覆写是否生效

Hermes 全局配置 `ollama_num_ctx: 65536` 和 provider 的 `context_length: 65536` 只是跳过 Hermes 的 64K 门槛检查，实际是否生效取决于模型能力。验证方法：

```bash
# 传入 options 中的 num_ctx 参数进行测试
curl -s -X POST http://<ollama_host>:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "<model_name>",
    "messages": [{"role":"user","content":"Hello"}],
    "max_tokens": 10,
    "options": {"num_ctx": 65536}
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if d['choices'][0]['message'].get('content','') else 'FAIL')"
```

**注意：** 
- qwen2.5 系原生仅 32K 上下文，覆写到 64K 可能在高位出现质量下降
- qwen3:8b 原生 40K，可安全扩展到 64K（RoPE 支持）
- deepseek-r1:7b/8b 原生 131K，完全满足 64K 要求

## 四、Token 级性能测试（新增）

通过 `/api/chat` 流式接口获取详细的 token 指标：

```bash
curl -s -X POST http://<ollama_host>:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "<model_name>",
    "messages": [{"role":"user","content":"Hello, respond in 3 words"}],
    "options": {"num_predict": 20}
  }' 2>&1 | tail -1 | python3 -c "
import sys, json
d = json.loads(sys.stdin.read().strip().rsplit('\n',1)[-1] if '\n' in sys.stdin.read() else sys.stdin.read())
# Actually let's capture properly
"
```

更好的方式：

```bash
curl -s -X POST http://<ollama_host>:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "<model_name>",
    "messages": [{"role":"user","content":"Hello"}],
    "options": {"num_predict": 20}
  }' | grep -o '{.*"done_reason"[^}]*}' | head -1 | python3 -c "
import sys, json
raw = sys.stdin.read().strip()
if not raw: print('No done response')
else:
    d = json.loads(raw)
    print(f'加载时间:   {d.get(\"load_duration\",0)/1e9:.2f}s')
    print(f'Prompt tokens: {d.get(\"prompt_eval_count\",\"?\")}')
    print(f'Prompt评估:  {d.get(\"prompt_eval_duration\",0)/1e6:.0f}ms')
    print(f'生成tokens:  {d.get(\"eval_count\",\"?\")}')
    print(f'生成耗时:   {d.get(\"eval_duration\",0)/1e6:.0f}ms')
    print(f'总耗时:     {d.get(\"total_duration\",0)/1e9:.2f}s')
    pps = d.get('prompt_eval_count',0)/(d.get('prompt_eval_duration',1)/1e9) if d.get('prompt_eval_duration',0) > 0 else 0
    tps = d.get('eval_count',0)/(d.get('eval_duration',1)/1e9) if d.get('eval_duration',0) > 0 else 0
    print(f'Prompt速度: {pps:.1f} tok/s')
    print(f'生成速度:   {tps:.1f} tok/s')
    print(f'完成原因:   {d.get(\"done_reason\",\"?\")}')
"
```

**性能参考（qwen2.5-coder:7b, Q4_K_M, CPU only）：**

| 指标 | 冷启动（首次） | 热调用 |
|:-----|:-------------|:-------|
| 加载时间 | ~5.6s | 0s（已在内存） |
| Prompt 评估 | ~846ms / 40 tok | ~21ms / tok |
| 生成速度 | ~413ms / 6 tok | ~69ms / tok |
| 总耗时 | ~6.9s | ~0.5s |
| Prompt 速度 | ~47 tok/s | — |
| 生成速度 | ~14.5 tok/s | — |

## 五、OpenAI 兼容端点完整测试

```bash
curl -s -X POST http://<ollama_host>:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "<model_name>",
    "messages": [
      {"role": "system", "content": "You are a test assistant."},
      {"role": "user", "content": "Say hello"}
    ],
    "max_tokens": 50,
    "options": {"num_ctx": 65536}
  }' | python3 -c "
import sys, json
d = json.load(sys.stdin)
u = d.get('usage', {})
print(f'Prompt tokens:    {u.get(\"prompt_tokens\",\"?\")}')
print(f'Completion tokens: {u.get(\"completion_tokens\",\"?\")}')
print(f'Total tokens:     {u.get(\"total_tokens\",\"?\")}')
print(f'Content: {d[\"choices\"][0][\"message\"][\"content\"]}')
print(f'Finish reason: {d[\"choices\"][0][\"finish_reason\"]}')
print(f'Model: {d.get(\"model\",\"?\")}')
"
```

## 六、完整一键验证

```bash
# 验证所有模型的 tools 支持 + content 字段
curl -s http://<ollama_host>:11434/api/tags | python3 -c "
import sys, json, urllib.request

data = json.load(sys.stdin)
host = sys.argv[1] if len(sys.argv) > 1 else '192.168.250.83:11434'

for m in data['models']:
    name = m['name']
    caps = m.get('capabilities', [])
    ctx = m['details'].get('context_length', '?')
    has_tools = 'tools' in caps

    # 验证 content 字段
    payload = json.dumps({
        'model': name,
        'messages': [{'role': 'user', 'content': 'say hi in 3 words'}],
        'max_tokens': 50,
        'stream': False
    }).encode()

    content_ok = '?'
    try:
        req = urllib.request.Request(
            f'http://{host}/v1/chat/completions',
            data=payload,
            headers={'Content-Type': 'application/json'}
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
        msg = resp['choices'][0]['message']
        c = msg.get('content', '').strip()
        r = msg.get('reasoning', '').strip()
        if c: content_ok = ' content'
        elif r: content_ok = ' reasoning only'
        else: content_ok = ' empty'
    except Exception as e:
        content_ok = f' {str(e)[:30]}'

    print(f'{name:30s} ctx={str(ctx):>7} tools={has_tools}  {content_ok}')
" 192.168.250.83:11434
```
