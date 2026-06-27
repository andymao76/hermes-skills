# VS Code AI 扩展安装指南

## 概述

VS Code AI 扩展分为两类：**厂商绑定型**（GitHub Copilot）和 **多模型型**（Continue.dev / Cline）。前者与 Copilot CLI 互补，后者适配 DeepSeek/SiliconFlow 等自控模型。

## GitHub Copilot VS Code 扩展

### 安装（snap 版 VS Code 已内置）

**关键发现：** VS Code 1.124+ snap 版已将 **GitHub Copilot 主扩展和 Copilot Chat** 都内置为系统扩展，位于：

```
/snap/code/<version>/usr/share/code/resources/app/extensions/copilot/
```

执行 `code --install-extension GitHub.copilot` 会报错：

```
Error while installing extension github.copilot-chat:
Extension 'github.copilot-chat' is a built-in extension with version '0.52.0'
and cannot be downgraded to version '0.48.1'.
```

这个错误是**正常行为**，并不意味着安装失败——而是因为扩展已内置、试图安装的版本比内置版旧。忽略即可，Copilot + Copilot Chat 在 VS Code 侧边栏直接可用。

**验证方法：**

```bash
# 检查 snap 内置扩展目录
ls /snap/code/*/usr/share/code/resources/app/extensions/ | grep copilot
```

**重要：** 不要试图用 `--force` 或手动下载 VSIX 绕过——内置扩展不能被降级替换，且 snap 的沙箱环境限制了 marketplace 直连下载。如果确认内置但不可用（如缺少 GitHub 账号登录），在 VS Code 内登录即可。

**非 snap 版（deb/RPM/portable）：** 如果将来切换到非 snap 版本，使用标准方式安装：

```bash
code --install-extension GitHub.copilot
```

### 与 Copilot CLI 的关系

| 维度 | VS Code Copilot 扩展 | Copilot CLI |
|------|----------------------|-------------|
| 场景 | 实时补全、内联聊天、逐行编码 | 批量生成、全项目重构、Git 操作 |
| 计费 | GitHub Copilot 许可证额度 | AI Credits / 配额 |
| 调用方式 | 编辑器内自动触发 | terminal/委托 |
| 与 Hermes 关系 | 互补（用户手动使用） | 委托子代理（Agent 自动调用） |

两者不是替代关系，是互补。详见 SKILL.md 的「VS Code 配合模式」章节。

## Continue.dev（推荐给 DeepSeek/SiliconFlow 用户）

### 适用场景

用户主力模型为 **DeepSeek + 硅基流动 API** 时，Continue.dev 是最佳选择：
- 开源自托管，无许可证限制
- 原生支持 OpenAI 兼容 API（硅基流动、DeepSeek 官方 API 等）
- 支持 **Tab 补全** 和 **内联对话** 两种模式
- 可在 VS Code 和 JetBrains 中使用

### 安装

```bash
code --install-extension continue.continue
```

### 基本配置

安装后配置 `~/.continue/config.json`：

```json
{
  "models": [
    {
      "title": "DeepSeek V3 (SiliconFlow)",
      "provider": "openai",
      "model": "deepseek-ai/DeepSeek-V3",
      "apiKey": "YOUR_SILICONFLOW_API_KEY",
      "apiBase": "https://api.siliconflow.cn/v1"
    }
  ],
  "tabAutocompleteModel": {
    "title": "DeepSeek Coder (SiliconFlow)",
    "provider": "openai",
    "model": "deepseek-ai/deepseek-coder-6.7b-instruct",
    "apiKey": "YOUR_SILICONFLOW_API_KEY",
    "apiBase": "https://api.siliconflow.cn/v1"
  }
}
```

**注意：** 硅基流动国内站（`.cn`）与国际站（`.com`）端点不同，配置时需区分。

### Tab 补全模型选择

| 模型 | 速度 | 质量 | 推荐场景 |
|------|------|------|----------|
| DeepSeek Coder 6.7B | 快 | 良好 | 日常补全 |
| Qwen2.5-Coder 7B | 快 | 良好 | 中文优先 |
| DeepSeek Coder V2 Lite | 中 | 好 | 平衡之选 |
| SiliconFlow 托管的 Code 模型 | 取决于部署 | 良好 | 免本地部署 |

### 限制

- Continue.dev 的 Tab 补全对 OpenAI 兼容 API 的支持不如 Copilot 原生补全流畅（延迟略高）
- 需要 API Key 配置，不能像 Copilot 那样零配置开箱即用
- Codestral（Mistral）的补全质量最高但需 Mistral API

## Cline

Cline 是另一个流行的 VS Code AI 扩展，支持自主编程 Agent 模式（类似 Copilot CLI 的 `/fix`）。对于需要"帮我重构整个模块"的场景更合适。

```bash
code --install-extension saoudrizwan.claude-dev
```

**注意：** Cline 消耗的是 API 额度而非 GitHub 配额，可以在同一个 API Key 下与 Hermes 共享使用。

## 扩展对比速查

| 扩展 | 安装命令 | 模型 | 计费 | 主要用途 |
|------|---------|------|------|----------|
| GitHub Copilot | `code --install-extension GitHub.copilot` | GPT/Claude/Copilot | GitHub 许可证 | 补全+内联聊天 |
| Continue.dev | `code --install-extension continue.continue` | 自选（DeepSeek 等） | 自备 API | 自控模型补全+聊天 |
| Cline | `code --install-extension saoudrizwan.claude-dev` | 自选 | 自备 API | Agent 模式编程 |
