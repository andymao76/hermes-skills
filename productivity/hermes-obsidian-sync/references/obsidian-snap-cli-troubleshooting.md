# Obsidian snap CLI 排障指南

## 症状

```bash
$ obsidian search "关键词"
The CLI is unable to find Obsidian. Please make sure Obsidian is running and try again.
```

## 诊断步骤

### 第 1 步：检查 Obsidian 是否安装

```bash
which obsidian
# 预期: /snap/bin/obsidian

snap list obsidian
# 预期: obsidian 1.12.7
```

### 第 2 步：检查 CLI socket 是否存在

Obsidian 运行时会在 `/run/user/<uid>/` 下创建 `.obsidian-cli.sock` 文件：

```bash
ls -la /run/user/$(id -u)/.obsidian-cli.sock
```

- **文件存在** → Obsidian 之前运行过，但当前可能已退出
- **文件不存在** → Obsidian 从未在当前会话中启动过

### 第 3 步：检查 socket 是否活跃

```bash
# strace 诊断
strace -f -e trace=connect,socket,openat obsidian search "test" 2>&1 | grep -i "sock\|connect"

# 结果分析
# - connect() 返回 0 → 正常
# - connect() 返回 ECONNREFUSED → socket 残留，Obsidian 未实际运行
```

### 第 4 步：检查桌面环境

```bash
echo $DISPLAY
# 通常在桌面会话中是 :0

ps aux | grep "[o]bsidian" | grep -v grep
# 如果有输出 → Obsidian 在运行
# 如果无输出 → Obsidian 未运行
```

### 第 5 步：检查是否有其他 Obsidian 窗口

```bash
DISPLAY=:0 xdotool search --name obsidian 2>/dev/null || echo "无 Obsidian 窗口"
```

## 根因

Obsidian snap（v1.12.7）在 Ubuntu 24.04 上存在两个问题：

1. **后台启动限制**：snap 的 `obsidian` 命令包装了 Electron GUI 启动脚本，在 terminal background 或无 PTY 环境下无法正确初始化图形界面
2. **socket 残留**：Obsidian 正常退出后，`.obsidian-cli.sock` 文件可能留在 `/run/user/1000/` 中，新启动终端执行 `obsidian search` 时看到文件存在但 connect 被拒绝

## 解决方案

| 方案 | 操作 |
|------|------|
| **最简单的** | 在桌面中手动启动 Obsidian（点击图标），等几秒后 CLI 自动可用 |
| **重启 Obsidian** | 在桌面中关闭 Obsidian 后重新打开 |
| **清理残留 socket** | `rm -f /run/user/1000/.obsidian-cli.sock`（可选，不影响功能） |
| **使用 DEB 替代 snap** | 从 obsidian.md 下载 .deb 包安装，CLI socket 行为更稳定 |

## 注意事项

- 此问题**不影响 symlink 功能** — 图谱和文件浏览在桌面 Obsidian 中完全正常
- only CLI 命令（`obsidian search` / `eval` / `backlinks`）受此影响
- 如果你在桌面中同时使用 Obsidian，CLI 是可用的——只是从 Hermes 终端无法启动 Obsidian
