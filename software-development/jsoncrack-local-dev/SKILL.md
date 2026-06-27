---
name: jsoncrack-local-dev
description: 在本地搭建并运行 jsoncrack.com 开发环境（Next.js monorepo），包括清理构建残留、安装依赖、启动 dev server、更改端口。
---

# jsoncrack.com 本地开发环境搭建

## 项目位置
`~/projects/jsoncrack.com/` (forked from `AykutSarac/jsoncrack.com` to `andymao76/jsoncrack.com`)

## 首次搭建 / 清理重建

```bash
cd ~/jsoncrack.com

# 1. 清理构建残留
rm -rf node_modules package-lock.json .turbo

# 2. 安装 pnpm（如尚无）
npm install -g pnpm

# 3. 安装依赖
pnpm install

# 4. 启动开发服务器（turbo monorepo）
pnpm dev
```

## 更改端口

默认 Next.js (www) 监听 **3000**。如需更换：

编辑 `apps/www/package.json`，在 `"dev"` 脚本中添加 `-p <端口>`：

```json
"dev": "next dev --webpack -p 3001"
```

然后**杀掉旧进程再重启**：

```bash
# 如果后台进程由 Hermes 管理
process action=kill session_id=<旧session_id>

# 重新启动
cd ~/jsoncrack.com && pnpm dev
```

## 启动后端口说明

| 端口 | 服务 |
|------|------|
| 3000/自定义 | Next.js (www app) |
| 5173 | Vite (VSCode Extension) |
| Chrome Extension | Vite build --watch 后台运行 |

## 验证

```bash
# 验证 /editor 页面（首页路由）
curl -sL -o /dev/null -w "%{http_code}" http://localhost:<端口>/editor
# 预期返回 200

# 查看监听端口
ss -tlnp | grep <端口>
```

> **注意：** jsoncrack 的首页路由是 `/editor`，根路径 `/` 无页面。
> 浏览器访问 `http://localhost:<端口>/editor`。

## 常见故障

### ❌ 浏览器 ERR_CONNECTION_REFUSED

- 确认访问路径是否包含 `/editor`
- 确认端口正确：`ss -tlnp | grep <端口>`
- 确认没有多个 next-server 进程冲突：

```bash
pkill -f "next-server"
sleep 2
cd ~/projects/jsoncrack.com && pnpm dev
```

### ❌ 端口占用

如果旧进程残留导致端口冲突，杀掉所有 next-server 后重启：

```bash
pkill -f "next-server"
sleep 2
cd ~/projects/jsoncrack.com && pnpm dev
```

## 桌面快捷方式启动

参见 `references/desktop-launcher-setup.md` — 在桌面创建双击即用的启动图标。

## 加载本地 dump 数据到可视化编辑器

参见 `references/cdp-local-data-loading.md` — 使用 CDP + 本地 static server 的方式将 Hermes dump JSON 自动加载到 jsoncrack 编辑器。

## 注意事项

- dev server 是长时间运行的进程，用 Hermes `terminal(background=true)` 启动
- 重启后 Next.js 首次编译较慢（esbuild/Rust 编译），需要等十几秒才有响应
- 输出可能不会立即出现在 `process log` 中，但 `ss -tlnp` 可以看到监听端口
- monorepo 使用 pnpm workspaces + TurboRepo

### 桌面环境 PATH 陷阱

桌面快捷方式 (`Terminal=false`) 运行时的 PATH 是系统默认路径，不包含 `~/.npm-global/bin/`。如果用 pnpm，启动脚本里必须用绝对路径：
```bash
PNPM="$HOME/.npm-global/bin/pnpm"
cd "$DIR" && "$PNPM" dev &
```
不能用裸 `pnpm`，否则桌面双击无反应（终端里可以正常跑）。
