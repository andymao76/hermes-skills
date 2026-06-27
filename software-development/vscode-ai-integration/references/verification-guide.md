# VS Code AI 扩展验证指南

## 验证清单

### 1. VS Code 设置
- 文件: `~/.config/Code/User/settings.json`
- 检查: `chat.defaultAgent` 是否为 `"copilot"`
- 验证: `python3 -c "import json; s=json.load(open('~/.config/Code/User/settings.json')); print(s['chat.defaultAgent'])"`

### 2. Continue 配置
- 文件: `~/.continue/config.yaml`
- 检查: YAML 语法正确
- 检查: 至少包含 1 个模型定义
- 检查: 环境变量引用正确（`${env:...Y}`, `${env:...Y}`）
- 验证: `python3 -c "import yaml; cfg=yaml.safe_load(open('~/.continue/config.yaml')); print(f'{len(cfg[\"models\"])} models')"`

### 3. Copilot 内置扩展
- 路径: `/snap/code/<version>/.../extensions/copilot/`
- 验证: `ls /snap/code/*/usr/share/code/resources/app/extensions/copilot/`

### 4. Continue.dev 扩展安装
- 路径: `~/.vscode/extensions/continue.continue-*/`
- 验证: `ls ~/.vscode/extensions/ | grep continue`

### 5. 环境变量
- `SILICONFLOW_API_KEY` — 必选
- `DEEPSEEK_API_KEY` — 可选（DeepSeek 模型时使用）

## 快速验证脚本 (Python)

```python
import json, yaml, os

errors, passes = [], []
with open(os.path.expanduser("~/.config/Code/User/settings.json")) as f:
    s = json.load(f)
if s.get("chat.defaultAgent") == "copilot":
    passes.append("Copilot 为默认 Chat Agent")
else:
    errors.append("Copilot 未设为默认")

with open(os.path.expanduser("~/.continue/config.yaml")) as f:
    cfg = yaml.safe_load(f)
if cfg.get("models"):
    passes.append(f"Continue: {len(cfg['models'])} 个模型")
else:
    errors.append("Continue: 无模型配置")
```
