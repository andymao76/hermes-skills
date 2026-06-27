# 桌面快捷方式启动开发服务器

创建 `.desktop` 文件放在 `~/Desktop/`，双击一键启动 dev server + 打开浏览器。

## 通用模板

### 启动脚本 (`~/projects/start-<app>.sh`)

```bash
#!/bin/bash
DIR="$HOME/projects/<项目目录>"
PORT=<端口>

# 如果 server 没在运行，启动它
if ! ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
  cd "$DIR" && <启动命令> &
  # 等 server 就绪（最多 N 秒）
  for i in $(seq 1 30); do
    sleep 1
    if ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
      break
    fi
  done
fi

# 打开浏览器
xdg-open "http://localhost:$PORT/<路由>"
```

### .desktop 文件 (`~/Desktop/<app>.desktop`)

```ini
[Desktop Entry]
Type=Application
Name=应用名称
Comment=描述
Exec=/home/andymao/projects/start-<app>.sh
Icon=<图标路径>
Terminal=false
Categories=Development;Utility;
StartupNotify=true
```

创建后执行：
```bash
chmod +x ~/Desktop/<app>.desktop
gio set ~/Desktop/<app>.desktop metadata::trusted true
```

## my-file-viewer 示例

| 项 | 值 |
|------|------|
| 启动脚本 | `~/projects/start-my-file-viewer.sh` |
| 端口 | 5173 |
| 路由 | `/` |
| 命令 | `npm run dev` |
| 等待时间 | 30s |
| .desktop | `~/Desktop/my-file-viewer.desktop` |
| 图标 | `~/projects/my-file-viewer/public/favicon.svg` |

## jsoncrack 示例

| 项 | 值 |
|------|------|
| 启动脚本 | `~/projects/start-jsoncrack.sh` |
| 端口 | 3001 |
| 路由 | `/editor` |
| 命令 | `pnpm dev` |
| 等待时间 | 60s（Next.js 首编译慢） |
| .desktop | `~/Desktop/jsoncrack.desktop` |
| 图标 | `~/projects/jsoncrack.com/apps/www/public/favicon.ico` |

## 注意

- `.desktop` 文件必须 `chmod +x` 并 `gio set ... trusted true` 才能双击运行
- 启动脚本会自动检测 server 是否已在运行，避免重复启动
- 再次双击图标只会打开浏览器（不会重复启动 server）
- 关闭服务按 `Ctrl+C` 停掉终端进程即可
