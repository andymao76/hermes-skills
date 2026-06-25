---
name: safe-exit
description: Bash 终端安全退出确认机制 — 防止意外关闭终端/会话 (exit/Ctrl+D/鼠标关闭窗口/SIGHUP)
author: Hermes Agent
tags: [bash, terminal, safety, exit, confirmation]
---

# 安全退出确认

当用户提到"退出提示"、"关闭确认"、"防止误关终端"、"安全退出"等话题时加载本 skill。

## 安装方法

将以下内容追加到 `~/.bashrc` 末尾：

```bash
# ── 安全退出确认 ──
# 防止意外关闭终端/会话 (exit/Ctrl+D/鼠标关闭窗口/SIGHUP)

IGNOREEOF=1

__hermes_safe_exit() {
  trap - EXIT HUP TERM
  if [[ ! -o interactive ]]; then
    builtin exit $?
    return
  fi
  echo ""
  echo "╔══════════════════════════════════════════════╗"
  echo "║  ⚠️  确定要关闭当前终端/会话吗？              ║"
  echo "╠══════════════════════════════════════════════╣"
  echo "║  y / yes        → 确认关闭                    ║"
  echo "║  其他任意键      → 取消                       ║"
  echo "╚══════════════════════════════════════════════╝"
  read -r -p "> " __hermes_confirm
  if [[ "$__hermes_confirm" == "y" || "$__hermes_confirm" == "yes" ]]; then
    builtin exit 0
  else
    echo "✅ 已取消退出"
    trap __hermes_safe_exit EXIT HUP TERM
  fi
}

trap __hermes_safe_exit EXIT
trap __hermes_safe_exit HUP
trap __hermes_safe_exit TERM
```

## 实现原理

在 `~/.bashrc` 末尾追加三层防护：

```
1. IGNOREEOF=1       → Ctrl+D 首次提示"Use exit"，不退出
2. trap EXIT          → exit / Ctrl+D 触发确认提示
3. trap HUP TERM      → 鼠标关闭窗口/SIGHUP 触发确认提示
```

### 核心函数

```bash
__hermes_safe_exit() {
  trap - EXIT HUP TERM          # 先解绑避免循环
  if 非交互模式: 直接退出        # 不干扰脚本运行
  显示确认框                      # 彩色 ASCII 边框
  用户输入 y/yes → 退出
  用户输入其他 → 取消，重新注册 trap
}
```

### 覆盖场景

| 触发方式 | 信号/SHELL 机制 | 是否捕获 |
|----------|----------------|----------|
| `exit` 命令 | EXIT trap | ✅ |
| `Ctrl+D` | EXIT trap + IGNOREEOF=1 | ✅ (两次 Ctrl+D 才退) |
| 鼠标关闭窗口 | SIGHUP | ✅ |
| `kill` 命令 | SIGTERM | ✅ |
| SSH 断连 | SIGHUP | ✅ |
| 子 shell 退出 | 非交互不触发 | ✅ 自动跳过 |

### 不影响

- 脚本运行（非交互模式自动跳过）
- `tmux` pane 关闭（HUP 信号同样捕获）
- 正常 `exit 0` 在确认后正常执行

## 验证方法

```bash
# 1. 确认配置加载
source ~/.bashrc

# 2. 测试 Ctrl+D
# 按 Ctrl+D → 显示确认框，输入 y 退出，其他取消

# 3. 测试 exit 命令
exit
# → 同样显示确认框

# 4. 查看 IGNOREEOF 值
echo $IGNOREEOF  # 应输出 1
```
