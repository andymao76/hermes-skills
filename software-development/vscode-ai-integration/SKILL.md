---
name: vscode-ai-integration
description: VS Code AI 助手集成配置 — Copilot + Continue.dev 安装、配置、验证。覆盖中文用户场景（硅基流动/DeepSeek 模型提供商）、内置扩展处理、环境变量引用、默认 Chat Agent 设置
---

# VS Code AI 集成配置

配置 VS Code 的 AI 编程助手（Copilot + Continue.dev），适配中文用户使用硅基流动/DeepSeek 等国产模型提供商。

## 主要组件

| 组件 | 说明 |
|------|------|
| **GitHub Copilot** | 内联补全 + Chat。VS Code snap 版 1.124+ 已内置，无需手动安装 |
| **Continue.dev** | 开源 AI 编程助手，支持多模型后端。通过 VS Code 扩展安装 |

## 安装步骤

### 1. 安装 VS Code 扩展

```bash
# Copilot - snap 版 VS Code 1.124+ 已内置，直接登录即可
# 若需要手动安装：
code --install-extension GitHub.copilot

# Continue.dev
code --install-extension Continue.continue
```

**注意**: snap 版 VS Code 1.124 已将 Copilot + Copilot Chat 作为内置扩展（路径 `/snap/code/<version>/usr/share/code/resources/app/extensions/copilot`）。尝试通过 CLI 安装会报 `Extension 'github.copilot-chat' is a built-in extension` 错误，这是正常行为——扩展已内置无需重复安装。

### 2. 设置 Copilot 为默认 Chat Agent

编辑 `~/.config/Code/User/settings.json`:

```json
{
    "chat.defaultAgent": "copilot"
}
```

### 3. 配置 Continue.dev

编辑 `~/.continue/config.yaml`:

```yaml
name: Main Config
schema: v1
models:
  - name: DeepSeek V4 Flash
    provider: openai
    model: deepseek-v4-flash
    apiKey: ${env:...Y}
    apiBase: https://api.deepseek.com/v1
    completionOptions:
      maxTokens: 8192
      temperature: 0.7
  - name: DeepSeek V2 (硅基流动)
    provider: openai
    model: deepseek-v2.5
    apiKey: ${env:...Y}
    apiBase: https://api.siliconflow.cn/v1
    completionOptions:
      maxTokens: 4096
      temperature: 0.7
  - name: Qwen2.5-Coder-32B (硅基流动)
    provider: openai
    model: Qwen/Qwen2.5-Coder-32B-Instruct
    apiKey: ${env:...Y}
    apiBase: https://api.siliconflow.cn/v1
    completionOptions:
      maxTokens: 4096
      temperature: 0.5
tabAutocompleteModel:
  title: Tab Autocomplete
  provider: openai
  model: deepseek-v2.5
  apiKey: ${env:...Y}
  apiBase: https://api.siliconflow.cn/v1
  completionOptions:
    maxTokens: 256
    temperature: 0.1
```

### 4. 环境变量设置

在 `~/.bashrc` 中添加：

```bash
export DEEPSEEK_API_KEY="sk-xxx"
export SILICONFLOW_API_KEY="sk-xxx"
```

Continue.dev 通过 `${env:...Y}` 语法引用环境变量，启动 VS Code 时会读取。

## 验证方法

使用以下验证脚本确认配置正确：

1. 检查 `settings.json` 中 `chat.defaultAgent` 是否为 `copilot`
2. 检查 `config.yaml` YAML 语法正确且包含模型定义
3. 检查 Copilot 内置扩展目录是否存在
4. 检查 Continue.dev 扩展目录是否存在
5. 检查必要环境变量是否已设置

## 常见问题

### Copilot 安装报 "built-in extension" 错误
不需要处理——snap 版 VS Code 1.124+ 已将 Copilot 内置。打开 VS Code 点击 Copilot 图标登录即可。

### Continue.dev 不显示模型
- 确认环境变量已设置且 VS Code 能读到
- 检查 `config.yaml` 语法（YAML 缩进敏感）
- VS Code 启动后右下角 Continue 图标点开看是否有报错

### Tab 自动补全不工作
- 确认 `tabAutocompleteModel` 配置正确
- 硅基流动的 deepseek-v2.5 适合做补全模型（低 temperature + 少 tokens）

## 参考

- Continue.dev 官方配置文档: https://docs.continue.dev
- Copilot 内置扩展路径: `/snap/code/<version>/.../extensions/copilot/`
- Continue 配置目录: `~/.continue/config.yaml`
