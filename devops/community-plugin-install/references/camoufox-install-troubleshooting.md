# Camoufox / camofox-browser 安装故障排查记录

## 环境

- Ubuntu 24.04 Wayland
- Node.js 24.15.0 (snap)
- Clash Verge 代理 :7897
- Hermes Agent 插件目录：`~/.hermes/plugins/camofox-browser/`

## 已知问题与修复

### 1. Node.js undici 内置 fetch 不走 HTTP_PROXY

**症状**：`pnpm install` 后 postinstall 脚本卡住，日志显示 `ConnectTimeoutError: github.com:443`

**根因**：Node.js 内置 fetch（基于 undici 库）不识别 `HTTP_PROXY`/`HTTPS_PROXY`/`ALL_PROXY` 环境变量。

**修复**：用 `curl` 走代理直接下载 ZIP，然后手动解压到缓存目录。

```bash
# 1. 找到最新 release tag
gh release list -R daijro/camoufox -L 3

# 2. 获取具体文件列表
gh release view <tag> -R daijro/camoufox --json assets --jq '.assets[].name'

# 3. 找到 Linux x86_64 版本的 ZIP
# 4. 用 curl 走代理下载（662MB）
curl -L --proxy http://127.0.0.1:7897 -o camoufox.zip \
  "https://github.com/daijro/camoufox/releases/download/<tag>/<file>" \
  -# --max-time 600

# 5. 解压并复制到 camoufox-js 的 INSTALL_DIR
mkdir -p ~/.cache/camoufox-js
unzip -q -o camoufox.zip -d ~/.cache/camoufox-js/camoufox
rm -rf ~/.cache/camoufox
cp -r ~/.cache/camoufox-js/camoufox ~/.cache/camoufox
```

**注意**：`gh` CLI 使用 GITHUB_TOKEN 避免 GitHub API 限流（403 错误）。

### 2. camoufox-js 版本约束导致自动删除缓存

**症状**：缓存目录 `~/.cache/camoufox/` 被 `CamoufoxFetcher.cleanup()` 自动清空

**根因**：`Version.buildSortedRel()` 将 release 字段中字母转为负数（`charCodeAt(0) - 1024`），导致新版本被判定为"低于" `MIN_VERSION`，触发 `camoufoxPath()` → `install()` → `cleanup()` 链路。

**修复**：修改 `__version__.js` 的 CONSTRAINTS 范围：

```js
// 位置：node_modules/.pnpm/camoufox-js@*/node_modules/camoufox-js/dist/__version__.js
export class CONSTRAINTS {
    static MIN_VERSION = "0";
    static MAX_VERSION = "999.999.999";
}
```

### 3. uBlock Origin addon 缺失

**症状**：`manifest.json is missing. Addon path must be a path to an extracted addon.`

**修复**：

```bash
mkdir -p ~/.cache/camoufox/addons/UBO
curl -L --proxy http://127.0.0.1:7897 -o /tmp/ubo.xpi \
  "https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi"
cd ~/.cache/camoufox/addons/UBO && unzip -q -o /tmp/ubo.xpi
```

### 4. better-sqlite3 原生模块未编译

**症状**：`Could not locate the bindings file`

**根因**：pnpm 不自动编译 C++ addon。需手动编译。

**修复**：

```bash
cd ~/.hermes/plugins/camofox-browser/node_modules/.pnpm/better-sqlite3@*/node_modules/better-sqlite3
node-gyp rebuild
```

编译 SQLite amalgamation（~9MB C 代码）需 ~1-2 分钟，CPU 单核 100%，内存 ~350MB。

### 5. server.js Xvfb await 缺失 bug

**症状**：`Error: cannot open display: [object Promise]`

**修复**：

```patch
// server.js 第 954-955 行
-        vdDisplay = localVirtualDisplay.get();
+        vdDisplay = await localVirtualDisplay.get();
```

### 6. Hermes 集成配置

camofox-browser 安装完成后，需将 Hermes 的 browser engine 从 `auto` 改为 `camofox`：

```bash
hermes config set browser.engine camofox
```

### 7. systemd 用户服务（开机自启）

```ini
# ~/.config/systemd/user/camofox-browser.service
[Unit]
Description=Camofox Browser Server - Anti-detection browser for AI agents
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/snap/node/11579/bin/node /home/andymao/.hermes/plugins/camofox-browser/server.js
WorkingDirectory=/home/andymao/.hermes/plugins/camofox-browser
Restart=on-failure
RestartSec=10
Environment=ALL_PROXY=http://127.0.0.1:7897
Environment=CAMOUFOX_EXECUTABLE=/home/andymao/.cache/camoufox/camoufox-bin
Environment=NODE_ENV=production

[Install]
WantedBy=default.target
```

启用：
```bash
systemctl --user daemon-reload
systemctl --user enable camofox-browser.service
systemctl --user start camofox-browser.service
```
