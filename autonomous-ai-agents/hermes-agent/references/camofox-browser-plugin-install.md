# camofox-browser 插件安装指南

camofox-browser 是一个基于 Camoufox（反检测 Firefox 分支）的浏览器服务器，为 AI Agent 提供隐身浏览能力。

## 安装概述

插件路径：`~/.hermes/plugins/camofox-browser/`

安装步骤：
1. `pnpm install`（或 `npm install` — 触发 postinstall 脚本）
2. postinstall 脚本自动执行 `npx camoufox-js fetch`（下载 ~662MB 的 Camoufox 浏览器二进制）
3. 启动服务器：`node server.js`（默认端口 9377）

## 已知问题与解决方案

### 1. Node.js undici fetch 不走代理（被墙环境）

**问题现象：** `camoufox-js` 使用 Node.js 内置 fetch（undici 库），它 **不识别** 环境变量 `HTTP_PROXY`/`HTTPS_PROXY`/`ALL_PROXY`。在被墙环境下，下载 Camoufox 二进制和 uBlock Origin 时一直超时重试。

**解决方案：**

a) **下载二进制**：用 curl 通过代理手动下载：
```bash
gh release view v150.0.2-beta.25 -R daijro/camoufox --json assets --jq '.assets[].name'
# 找到 linux x86_64 版本，然后：
curl -L --proxy http://127.0.0.1:7897 -o camoufox.zip \
  "https://github.com/daijro/camoufox/releases/download/v150.0.2-beta.25/camoufox-150.0.2-alpha.26-lin.x86_64.zip" \
  --max-time 600
```

b) **解压到正确位置**：`~/.cache/camoufox/`（Linux 默认缓存目录）
```bash
mkdir -p ~/.cache/camoufox
unzip -q camoufox.zip -d ~/.cache/camoufox
```

c) **创建 version.json**：
```bash
echo '{"release":"150.0.2-beta.25","version":"150.0.2-alpha.26"}' > ~/.cache/camoufox/version.json
```

d) **下载 uBlock Origin（AMO）**：
```bash
curl -L --proxy http://127.0.0.1:7897 -o /tmp/ubo.xpi \
  "https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi"
mkdir -p ~/.cache/camoufox/addons/UBO
cd ~/.cache/camoufox/addons/UBO
unzip -q -o /tmp/ubo.xpi
```

### 2. camoufox-js 版本约束不兼容

**问题现象：** 启动 server.js 后，创建标签页失败，日志显示：
```
Version information not found at .../version.json. Please run `camoufox fetch` to install.
```
或者 `camoufoxPath()` 的 `CamoufoxFetcher.cleanup()` 删除了整个 `~/.cache/camoufox/` 目录。

**根因：** `camoufox-js` 内置版本约束（`__version__.js` 中的 `CONSTRAINTS` 类）的 **MIN_VERSION 版本比较算法有 bug**。对于 beta/alpha 版本号（如 `150.0.2-beta.25`），`buildSortedRel()` 将字母解析为负数，导致较新的版本被认为比 MIN_VERSION 还老，从而触发重新下载+cleanup。

**解决方案：** 放宽版本约束：
```bash
cat > node_modules/.pnpm/camoufox-js@0.11.0_playwright-core@1.60.0/node_modules/camoufox-js/dist/__version__.js << 'EOF'
export class CONSTRAINTS {
    static MIN_VERSION = "0";
    static MAX_VERSION = "999.999.999";
    static asRange() {
        return `>=${CONSTRAINTS.MIN_VERSION}, <${CONSTRAINTS.MAX_VERSION}`;
    }
}
EOF
```

### 3. server.js Xvfb await 缺失

**问题现象：** 创建标签页时 Firefox 报错：
```
Error: cannot open display: [object Promise]
```

**根因：** `server.js` 第 955 行缺少 `await`：
```js
// 错误：
vdDisplay = localVirtualDisplay.get();
// 正确：
vdDisplay = await localVirtualDisplay.get();
```

**解决方案：** patch server.js：
```bash
# 将第 955 行的 vdDisplay = localVirtualDisplay.get() 改为：
vdDisplay = await localVirtualDisplay.get();
```
注意 `launchBrowserInstance()` 已是 `async function`，所以加 await 是安全的。

### 4. better-sqlite3 原生模块编译

**问题现象：** 启动 server.js 后报错：
```
Could not locate the bindings file. ... better_sqlite3.node
```

**根因：** `pnpm install` 时 better-sqlite3 的原生 C++ 扩展未编译（网络原因或 pnpm 跳过 prebuild）。

**解决方案：**
```bash
cd node_modules/.pnpm/better-sqlite3@12.10.0/node_modules/better-sqlite3
node-gyp rebuild
```

### 5. 服务器启动后浏览器自动预热

server.js 启动后会自动创建 Xvfb 虚拟显示并启动 Camoufox 浏览器进程。首次启动可能需要 5-10 秒才能就绪。监控健康状态：

```bash
curl -s http://localhost:9377/
# 返回：{"ok":true,"enabled":true,"running":true,...}
```

## 集成到 Hermes

### 配置 browser engine

```bash
hermes config set browser.engine camofox
```

这会让 Hermes 的 `browser_navigate`/`browser_click` 等工具使用 camofox-browser API 而非 Playwright。

### systemd 用户服务（开机自启）

```bash
cat > ~/.config/systemd/user/camofox-browser.service << 'EOF'
[Unit]
Description=Camofox Browser Server
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
EOF

systemctl --user daemon-reload
systemctl --user enable camofox-browser.service
systemctl --user start camofox-browser.service
```

### 环境变量说明

| 变量 | 说明 |
|------|------|
| `ALL_PROXY` | 必须设置！Node.js undici 依赖此变量走代理 |
| `CAMOUFOX_EXECUTABLE` | 指向已下载的 camoufox-bin，跳过版本检查 |
| `NODE_ENV=production` | 减少日志噪音 |

## 验证

```bash
# 服务器状态
curl -s http://localhost:9377/

# 创建标签并导航
curl -s -X POST http://localhost:9377/tabs \
  -H "Content-Type: application/json" \
  -d '{"userId": "hermes", "sessionKey": "test", "url": "https://httpbin.org/get"}'

# 获取页面快照
curl -s "http://localhost:9377/tabs/<tabId>/snapshot?userId=hermes"
```
