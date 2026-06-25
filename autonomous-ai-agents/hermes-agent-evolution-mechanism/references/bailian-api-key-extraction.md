# 阿里百炼 API Key 提取模式

## 背景

阿里百炼（DashScope）API key 在 config.yaml 中配置为：

```yaml
providers:
  bailian:
    api_key: ''           # 空字符串
    api_key_env: DASHSCOPE_API_KEY    # 实际 key 在 .env 中
    base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
```

这意味着 `api_key` 字段为**空字符串**，真实 key 通过 `api_key_env` 引用 `.env` 文件中的 `DASHSCOPE_API_KEY`。

## 问题

当在 Python 脚本中直接调用百炼 API 时：
- `os.environ.get('DASHSCOPE_API_KEY', '')` **返回空** — 终端/后台进程的 shell 环境不自动加载 `.env`
- 即使 `source ~/.hermes/.env` 也不可靠（`*.env` 文件输出被系统红action机制遮蔽）

## 正确做法：直接读 .env 文件

```python
import os

def get_key_from_env(env_var):
    """从 ~/.hermes/.env 读取环境变量值"""
    env_path = os.path.expanduser('~/.hermes/.env')
    if not os.path.exists(env_path):
        return ''
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith(env_var + '='):
                parts = line.split('=', 1)
                if len(parts) == 2 and parts[1]:
                    return parts[1].strip("'\" ")
    return ''

# 使用
api_key = get_key_from_env('DASHSCOPE_API_KEY')
```

## 完整调用模板

```python
import json, base64, requests, yaml, os

# 1. 读 config.yaml 获取 api_key_env 字段名
config_path = os.path.expanduser('~/.hermes/config.yaml')
with open(config_path) as f:
    cfg = yaml.safe_load(f)

provider = cfg.get('providers', {}).get('bailian', 
            cfg.get('custom_providers', {}).get('bailian', {}))
env_var = provider.get('api_key_env', 'DASHSCOPE_API_KEY')
base_url = provider.get('base_url', 'https://dashscope.aliyuncs.com/compatible-mode/v1')

# 2. 读 .env 获取实际 key
api_key = get_key_from_env(env_var)

# 3. 调用
headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
payload = {
    'model': 'qwen3-vl-plus',  # 或其他模型
    'messages': [{'role': 'user', 'content': [
        {'type': 'text', 'text': '描述这张图片'},
        {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{b64}'}}
    ]}],
    'max_tokens': 500
}
r = requests.post(f'{base_url}/chat/completions', headers=headers, json=payload, timeout=45)
```

## 适用场景

- 所有使用 `api_key_env` 的 provider（非直接 `api_key`）
- Python 脚本通过终端执行时
- cron 任务中的脚本调用
- 注意：Hermes gateway/agent 内部已自动加载 `.env`，此问题仅出现在 `terminal()` 工具启动的独立 Python 进程中
