# Copilot 模型发现方法

> 用于回答"我当前 Copilot 背后是什么模型"类问题。

## 原理

Copilot Auto 模式并不固定使用某个模型。每次会话的 `selectedModel` 记录在 VS Code 工作区存储中，可从 JSONL 文件中直接读取。

## 操作步骤

### 1. 找最新会话

```bash
ls -lt ~/.config/Code/User/workspaceStorage/*/chatSessions/*.jsonl | head -5
```

### 2. 读取模型信息

```bash
cat /path/to/most-recent.jsonl | python3 -c "
import sys,json
d = json.loads(sys.stdin.read())
m = d['v']['inputState']['selectedModel']
fam = m['metadata'].get('family','?')
ver = m['metadata'].get('version','?')
name = m['metadata'].get('name','?')
print(f'Model: {m[\"identifier\"]}')
print(f'Family: {fam}')
print(f'Version: {ver}')
print(f'Display: {name}')
"
```

### 3. 查看 Copilot CLI 可用模型

```bash
copilot --help | grep -A2 'model'
copilot -p "hello" 2>&1 | head -3
```

### 4. 查看 VS Code 配置中启用的 Copilot 模型

```bash
grep -r 'github.copilot.chat' ~/.config/Code/CachedConfigurations/ 2>/dev/null | grep -v History
```

## 已知模型池（2026-06 实测）

| 模型标识 | Family | 说明 |
|----------|--------|------|
| `copilot/auto` | `gpt-5-mini` | Auto 最近一次选的 GPT 轻量模型 |
| `copilot/auto` | `claude-haiku-4.5` | Auto 选的 Claude 轻量模型 |
| `copilot/auto` | `oswe-vscode` (raptor-mini) | Copilot 内部模型 |
| 手动设置 | `claude-sonnet-4` | 通过 `--model` 锁定 |
| 手动设置 | `gpt-5.2` | 通过 `--model` 锁定 |

**关键发现：** Copilot Auto 不等于固定 Claude。它会根据任务复杂度在 GPT 和 Claude 之间动态切换。`github.copilot.chat.claude47OpusPrompt.enabled: true` 表示 Claude 4.7 Opus 在池中可用，但不一定被选中。

## 场景

- 用户问"我 Copilot 现在用的什么模型" → 步骤 1+2
- 用户问"能不能换模型" → 说明 Auto 模式 + `--model` 锁定选项
- 用户问"为什么不是 Claude" → 展示 Auto 动态选择机制
