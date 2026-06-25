---
name: jsoncrack-local-dev
description: 在本地搭建并运行 jsoncrack.com 开发环境（Next.js monorepo），包括清理构建残留、安装依赖、启动 dev server、更改端口。
---

# jsoncrack.com 本地开发环境搭建

## 项目位置
`~/jsoncrack.com/`

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
curl -sL -o /dev/null -w "%{http_code}" http://localhost:<端口>
# 预期返回 200
```

## 加载本地 dump 数据到可视化编辑器

参见 `references/cdp-local-data-loading.md` — 使用 CDP + 本地 static server 的方式将 Hermes dump JSON 自动加载到 jsoncrack 编辑器。

## 注意事项

- dev server 是长时间运行的进程，用 Hermes `terminal(background=true)` 启动
- 重启后 Next.js 首次编译较慢（esbuild/Rust 编译），需要等十几秒才有响应
- 输出可能不会立即出现在 `process log` 中，但 `ss -tlnp` 可以看到监听端口
- monorepo 使用 pnpm workspaces + TurboRepo
