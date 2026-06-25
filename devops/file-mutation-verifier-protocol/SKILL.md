---
name: file-mutation-verifier-protocol
description: File-mutation verifier 触发时的强制响应协议。当 patch/write_file 工具被安全策略拦截时必须执行。
version: 1.0.0
author: Hermes Agent (user directive)
metadata:
  hermes:
    tags: [safety, file-mutation, protocol, devops]
---

# File-Mutation Verifier 响应协议

## 触发条件

当 `patch` 或 `write_file` 工具返回结果中**包含以下任一关键词**时，立即触发本协议：

- `File-mutation verifier`
- `were NOT modified`
- `Refusing to write`
- `Write denied`

## 强制响应流程 (Checklist)

触发后**必须按顺序**执行以下步骤，不可跳过：

### 第 1 步：红色警告（多行框）

在终端输出红色粗体多行警告框，完整告知用户拦截详情和替代方案：

```bash
echo -e '\033[1;31m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠  File-mutation verifier 安全拦截
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hermes 安全策略已拦截以下文件修改：
  • {文件路径} → [{工具名}] 被拒绝
    原因：{具体原因}

处理规则：
  1. Hermes 工具(patch/write_file)的修改未生效
  2. 必须以终端命令(cat/grep/sed)实际读取文件内容为准
  3. .env 修改请用 sed/重定向，config.yaml 用 hermes config set

⚠  不要相信工具返回的"已修改"状态，以终端输出为唯一真相来源！
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m'
```

> 模版脚本见 `scripts/warning-display.sh`

### 第 2 步：终端命令验证

**禁止使用 `read_file` 工具**验证 —— 必须使用终端命令：

```bash
# 查看文件内容
cat <受影响的文件路径>

# 或查看关键行
sed -n '<起始行>,<结束行>p' <文件路径>

# 或搜索关键内容
grep -n '<关键词>' <文件路径>
```

### 第 3 步：以终端输出为准

- 终端输出的内容 = 文件的**唯一真相来源**
- `patch`/`write_file` 工具返回的 "修改成功" 或 "已拒绝" 状态**不可信**
- 如果文件确实需要修改，告知用户手动编辑或使用 `hermes config` 等专用命令

## 核心原则：输出命令，不修改配置

**最重要规则**：任何配置修改场景，Agent 只输出命令让用户执行，绝不直接修改文件。

```
用户：切换模型到 deepseek
→ 错误：Agent 直接改 config.yaml ❌
→ 正确：Agent 输出命令让用户执行 ✅
  hermes config set provider deepseek
  hermes config set model deepseek-v4-flash
```

## 受保护文件类型

以下类型的文件被 Hermes 安全策略保护，`patch`/`write_file` 工具无法直接修改：

- `~/.hermes/config.yaml` — **输出** `hermes config set <key> <value>` 命令让用户手工执行
- `~/.hermes/.env` — 通过终端追加
- `~/.ssh/*` — 手动编辑
- `~/.gitconfig` — 手动编辑
- `~/.bashrc` — 手动编辑
- 任何包含 API Key 的文件

## 克隆上游仓库处理规则

当修改从 GitHub 克隆的上游仓库时（如 langgenius/dify、googleapis/python-genai），直接 commit 会导致 git pull 冲突：

1. **自定义脚本** → 移到 `~/scripts/{项目名}/` 统一管理，不入库
2. **日志/临时文件** → 直接删除，不入版本控制
3. **.gitignore** → 追加通配符模式，防止同类文件再出现
4. **配置修改** → 只改本地 `.env`，不改 `docker-compose.yaml` 等跟踪文件

## 反例（禁止行为）

❌ 看到 verifier 警告后仍然说 "修改成功"
❌ 用 `read_file` 替代终端命令验证
❌ 忽略 verifier 警告直接继续下一步
❌ 声称文件内容已改变但未用终端验证

## 非安全拦截的写入失败

当 `write_file` / `patch` 失败但**不是**安全策略拦截（无 `Refusing to write` / `Write denied`），
而是 `[Command interrupted]` 或 `bytes_written: 0` 时：

1. 用 `ls -lh` 确认文件实际是否存在
2. 用 `read_file` 或 `head/wc` 检查内容完整性
3. 如需重新生成，优先用 `cat <<'EOF'` heredoc 写入（不受 tool 中断影响）
4. 完整诊断流程见 `references/write-failure-diagnosis.md`

## 正确示例

```
1. patch 工具返回 ⚠️ File-mutation verifier: config.yaml was NOT modified
2. 立即执行：echo -e '\033[31m⚠ 安全策略：Hermes工具未生效，以终端命令(cat/grep)验证为准\033[0m'
3. 执行：cat ~/.hermes/config.yaml | grep -A5 'model:'
4. 报告：终端输出显示 model 段内容为 {...}，确认 patch 未生效
5. 建议：请使用 hermes config set model.provider xxx 手动修改
```
