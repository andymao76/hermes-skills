---
name: hermes-root-isolation
description: Hermes Agent Root 与普通用户环境隔离 — 防止 sudo 运行导致 API Key/Skills/Memory 丢失误判
---

# Hermes Root Isolation

## 适用环境
- Ubuntu 24.04
- Hermes Agent v0.16+
- 单用户部署（用户：andymao）
- Root 管理模式

## 问题现象
升级 Hermes 后出现：
- API Key 丢失
- Skills 丢失
- Memory 丢失
- MCP 配置消失
- Portal 配置失效

**实际情况**：配置未丢失，只是进入了 root 环境，读取了 `/root/.hermes` 而非 `/home/andymao/.hermes`。

## 原因分析
Hermes 配置按 Linux 用户隔离：
```
andymao  └── /home/andymao/.hermes
root     └── /root/.hermes
```
`sudo hermes` → 读取 `/root/.hermes` → 误认为配置被覆盖。

## 排查三步法
```bash
whoami          # 确认当前用户
echo $HOME      # 确认 Home 路径
ls ~/.hermes    # 确认配置目录
```

## Root 环境加固

### 1. Root Shell 告警（/root/.bashrc）
```bash
# Root shell warning
if [ "$USER" = "root" ]; then
    echo "⚠️ WARNING: 当前是 ROOT SHELL"
    echo "⚠️ Hermes 会读取 /root/.hermes"
    echo "⚠️ 正常工作环境应为 /home/andymao/.hermes"
fi
```

### 2. Root 红色提示符（/root/.bashrc）
```bash
export PS1='\[\033[1;31m\][ROOT@\h \W]#\[\033[0m\] '
```

### 3. 禁止 Root 运行 Hermes（/root/.bashrc）
```bash
hermes() {
    echo "❌ 不要在 root 下运行 Hermes"
    echo "👉 请执行 exit"
    echo "👉 切换到 andymao 用户"
    return 1
}
```

### 4. 处理登录 shell（/root/.profile）
`su -` / `sudo su -` 优先读取 `/root/.profile` 而非 `.bashrc`，需在 `.profile` 中 source `.bashrc`：
```bash
if [ "$USER" = "root" ]; then
    echo "⚠️ WARNING: 当前是 ROOT SHELL"
    echo "⚠️ Hermes 会读取 /root/.hermes"
fi
if [ -f /root/.bashrc ]; then
    . /root/.bashrc
fi
```

## 普通用户环境美化（/home/andymao/.bashrc）
```bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "👤 User : $(whoami)"
echo "🏠 Home : $HOME"
echo "🤖 Hermes: $HOME/.hermes"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━"

export PS1='\[\033[1;32m\][AndyMao@\h \W]\$\[\033[0m\] '
```

## 推荐运维规范

| 任务范围 | 使用用户 |
|----------|----------|
| apt, systemctl, fdisk, parted, mount, umount, 磁盘管理, 网络配置 | **root** |
| Hermes, Memory, Skills, MCP, Portal, Knowledge, Feishu, WhatsApp, Discord, OpenWebUI | **andymao** |

## 升级规范
```bash
# 正确
whoami          # 确认是 andymao
hermes update   # 或 python3 -m pip install -U hermes-agent

# 错误 ❌
sudo hermes update
```

## 经验总结
当 Hermes 升级后出现配置丢失假象时，90% 以上是进入了 root 环境。**不是真正的数据丢失**。优先运行排查三步法再做判断。
