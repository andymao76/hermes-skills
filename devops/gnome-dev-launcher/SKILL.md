---
name: gnome-dev-launcher
description: 为本地开发工具（Vite/Next.js dev server 等）创建 GNOME 桌面快捷方式，双击启动 + 自动打开浏览器
category: devops
tags: [gnome, desktop, launcher, shortcut, ubuntu]
---

# GNOME 开发工具桌面快捷方式

## 适用场景

为本地运行的开发工具创建 Ubuntu 桌面快捷方式，双击即可：
- 启动 dev server（如 `npm run dev`、`pnpm dev`）
- 等待服务就绪
- 自动打开浏览器

## 架构

```
~/Desktop/<tool>.desktop
    │  Type=Application
    │  Exec=<wrapper script>
    └─ ~/projects/start-<tool>.sh
          │  # 检查端口是否已监听
          │  # 未监听 → 后台启动 dev server
          │  # 等待就绪 → xdg-open 打开浏览器
          └─ cd <project> && npm run dev
```

## 创建步骤

### 1. 编写启动脚本

模板 `~/projects/start-<tool>.sh`：

```bash
#!/bin/bash
DIR="$HOME/projects/<项目目录>"
PORT=<端口>

# 如果 server 没在运行，启动它
if ! ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
  cd "$DIR" && <启动命令> &
  # 等 server 就绪
  for i in $(seq 1 <超时秒数>); do
    sleep 1
    if ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
      break
    fi
  done
fi

# 打开浏览器
xdg-open "http://localhost:$PORT/<路径>"
```

**端口与超时对照：**

| 工具类型 | 启动命令 | 默认端口 | 建议超时 |
|---------|---------|---------|---------|
| Vite | `npm run dev` | 5173 | 30s |
| Next.js | `pnpm dev` | 3000-3001 | 60s（首编译较慢） |
| 其他 dev server | 按实际 | 按实际 | 10-30s |

### 2. 创建 .desktop 文件

`~/Desktop/<tool>.desktop`：

```ini
[Desktop Entry]
Type=Application
Name=<显示名称>
Comment=<描述>
Exec=/home/andymao/projects/start-<tool>.sh
Icon=<图标路径或图标名>
Terminal=false
Categories=Development;Utility;
StartupNotify=true
```

### 3. 授权并标记可信

```bash
chmod +x ~/Desktop/<tool>.desktop
gio set ~/Desktop/<tool>.desktop metadata::trusted true
chmod +x ~/projects/start-<tool>.sh
```

## 案例

### my-file-viewer (Vite + React)

| 项 | 值 |
|---|---|
| 端口 | 5173 |
| 启动 | `npm run dev` |
| 超时 | 30 秒 |
| 访问路径 | `/` |

### jsoncrack.com (Next.js + TurboRepo)

| 项 | 值 |
|---|---|
| 端口 | 3001 |
| 启动 | `pnpm dev` |
| 超时 | 60 秒 |
| 访问路径 | `/editor`（首页即编辑器） |

### Grafana (Docker 常驻)

Grafana 是 Docker 容器常驻运行，launcher 只需打开浏览器：

```bash
Exec=xdg-open http://localhost:3000/
```

无需检查端口，直接用 `xdg-open` 打开即可。

## 常见陷阱

### ❌ 浏览器打开根路径无页面

Next.js 项目可能有自定义路由，根路径 `/` 可能空。确认正确路径：

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:<端口>/<路径>
```

### ❌ 多个 next-server 进程冲突

`pkill -f "next-server"` 后再重启。launcher 脚本中的 `ss -tlnp` 检测能防止重复启动。

### ❌ .desktop 文件双击提示"未信任"

```bash
gio set ~/Desktop/<tool>.desktop metadata::trusted true
```

### ❌ 双击无反应，终端却正常（桌面 PATH 陷阱）

`.desktop` 中 `Terminal=false` 时，进程继承的是系统默认 PATH：
```
/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin
```

装在用户目录的工具（`~/.npm-global/bin/pnpm`、`~/.local/bin/` 等）不在这个 PATH 里，导致 `command not found`。

**症状：** 终端 `bash start-tool.sh` 能跑，桌面双击没反应/闪退。

**诊断方法：** 用桌面环境相同的受限 PATH 运行脚本，看是否报 `not found`：
```bash
# 模拟桌面 PATH
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin
bash ~/projects/start-<tool>.sh
# 如果报 command not found → PATH 问题确认
```

**修复：** 启动脚本中用绝对路径：

```bash
# 错误：桌面找不到
cd "$DIR" && pnpm dev &

# 正确：绝对路径
PNPM="$HOME/.npm-global/bin/pnpm"
cd "$DIR" && "$PNPM" dev &
```

### ❌ 桌面图标显示为默认图标（而非自定义图标）

GNOME 对 `.ico` 格式兼容性不如 `.png`。如果图标显示异常，换成同名的 `.png` 文件（通常在 `public/assets/` 下找）。

## 已创建的桌面快捷方式

| 快捷方式 | 项目 | 功能 |
|---------|------|------|
| `~/Desktop/my-file-viewer.desktop` | `~/projects/my-file-viewer/` | CSV/JSON/XML/Excel 预览 |
| `~/Desktop/jsoncrack.desktop` | `~/projects/jsoncrack.com/` | JSON 可视化编辑器 |
| `~/Desktop/grafana.desktop` | Docker 常驻 | Grafana 监控看板 |

## 关联

- 知识库: `02_AREAS/ubuntu-ops/jsoncrack-local-setup.md`
- 知识库: `02_AREAS/ubuntu-ops/grafana-dns-resolve-fix.md`
- 技能: `monitoring-stack-setup`
