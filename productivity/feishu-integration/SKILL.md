---
name: feishu-integration
description: 飞书（Lark）集成全链路——Hermes Gateway WebSocket 连接、API 消息发送、feishu-docx 工具安装配置及文档/知识库导出管理
category: productivity
tags:
  - feishu
  - lark
  - feishu-docx
  - document-export
  - wiki
  - websocket
  - gateway
triggers:
  - 飞书
  - feishu
  - lark
  - 文档导出
  - 知识库
  - wiki
---

# Feishu Integration

飞书集成工作流，覆盖三大路径：Hermes Gateway WebSocket、REST API、feishu-docx 工具。

## 1. feishu-docx 工具

### 安装

```bash
# 系统 Python 环境（externally-managed）
pip install --break-system-packages feishu-docx

# SOCKS 代理支持（如果走代理）
pip install --break-system-packages socksio
```

### 配置凭证

```bash
# 凭证据 ~/.hermes/.env 中的 FEISHU_APP_ID / FEISHU_APP_SECRET
feishu-docx config set --app-id YOUR_APP_ID --app-secret YOUR_APP_SECRET
```

配置保存在 `~/.feishu-docx/config.json`，认证模式 tenant_access_token。

### 常用命令

```bash
# 导出单个文档为 Markdown
feishu-docx export "https://xxx.feishu.cn/docx/xxx" -o ./output

# 导出到指定目录并命名
feishu-docx export "URL" -o ./docs -n my_doc

# 直接输出内容（适合 AI Agent 管道）
feishu-docx export "URL" --stdout

# 导出知识库（整个空间）
feishu-docx export-wiki-space <space_id_or_url> -o ./wiki_backup

# 导出知识库，限制深度
feishu-docx export-wiki-space <space_id> --max-depth 2

# 导出"我的空间"
feishu-docx export-wiki-space my_library -o ./my_docs

# 列举应用云空间文件
feishu-docx drive ls --type docx

# 设置文档公开权限
feishu-docx drive perm-set "URL" --share-entity anyone_can_view

# 启动 TUI
feishu-docx tui
```

### Python API

```python
from feishu_docx import FeishuExporter

exporter = FeishuExporter(app_id="xxx", app_secret="xxx")
path = exporter.export("https://xxx.feishu.cn/wiki/xxx", "./output")
content = exporter.export_content("URL")  # 不保存文件
```

### 浏览器导出（公开文档）

需要 Playwright：
```bash
pip install playwright
playwright install chromium

feishu-docx export-browser "URL" -o ./browser_docs
```

### 权限排查

| 错误码 | 含义 | 解决方法 |
|--------|------|---------|
| 99991672 | 应用缺少所需 scope | 飞书响应中附带授权链接，直接访问即可：`https://open.feishu.cn/app/<app_id>/auth?q=<scopes>&op_from=openapi&token_type=tenant` |
| 131006 | scope 已开通但无权访问该知识空间 | 将应用添加到具体知识空间的成员列表中（去飞书客户端 → 知识库 → 设置 → 成员管理 → 添加机器人/应用） |
| SOCKS 错误 | 代理需要 socksio | `pip install socksio` |

**知识空间授权要点**：
- 应用需两步授权：①在开放平台开通 wiki scope（修复 99991672）②把应用添加到知识空间成员列表（修复 131006）
- 即使 scope 开通了，`my_library` 快捷方式也可能因为应用未加入空间而返回 131006
- 如果用具体知识空间的 URL 或 space_id 替代 `my_library`，可以绕过加入空间成员的问题

### 注意事项
- 所有 feishu-docx 命令走 SOCKS/HTTP 代理（用户环境 127.0.0.1:7897），需要 socksio
- 文件路径含空格需引号包裹
- 导出 Sheet 时用 `--sheet-value-mode display|formula` 控制输出

## 2. Hermes Gateway WebSocket

飞书已通过 Hermes Gateway WebSocket 直连，支持消息接收和指令处理。

无需额外配置。Gateway 进程由 systemd 管理。

## 3. REST API 消息发送

飞书 API 消息发送流程：

```bash
# 1. 获取 tenant_access_token
POST https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal
{
  "app_id": "cli_xxx",
  "app_secret": "xxx"
}
# 响应: {"code":0, "tenant_access_token":"xxx", "expire":7200}

# 2. 发送消息
POST https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id
Authorization: Bearer <token>
{
  "receive_id": "ou_a74c0eb0ff0f216d5036c2300a213d22",
  "msg_type": "text",
  "content": "{\"text\":\"消息内容\"}"
}
```

关键信息：
- 用户 open_id: `ou_a74c0eb0ff0f216d5036c2300a213d22`
- Token 有效期 2 小时，需自动刷新
- 文档 URL 加 `.md` 后缀可获取 AI 友好 Markdown

## 4. feishu-hermes 桥服务（Webhook 模式）

除了 Gateway WebSocket 连接，还有一个独立的 **feishu-hermes 桥服务**（Node.js + Express + Axios），以 Cloudflare Tunnel 暴露到公网，接收飞书事件回调。

### 4.1 架构

```
飞书开放平台 → Webhook → Cloudflare Tunnel → feishu-hermes (port 3010) → hermes CLI
```

- 接收飞书事件（消息、审批等）并转发给 Hermes CLI
- Hermes 处理完成后通过 `replyMessage()` 回复原始消息
- 默认只支持**回复**（responding），不支持主**动发送**

### 4.2 文件位置

```bash
~/feishu-hermes/
├── server.js                  # 主服务
├── .env                       # 凭证（FEISHU_APP_ID, FEISHU_APP_SECRET, VERIFY_TOKEN）
├── start_cloudflared_quick.sh # Cloudflare Tunnel 自启动脚本
├── logs/
│   └── app.log                # 运行日志
└── package.json / node_modules/
```

### 4.3 添加主动发送端点（补丁）

原版 server.js 只有 `replyMessage()`（回复已有消息），没有主动发送端点。以下端点可补丁添加：

```javascript
app.post("/feishu/send", async (req, res) => {
  try {
    const { receive_id, receive_id_type, text } = req.body;
    if (!receive_id || !text) {
      return res.status(400).json({ code: 400, msg: "receive_id and text are required" });
    }
    const token = await getTenantAccessToken();
    const idType = receive_id_type || "open_id";
    const result = await axios.post(
      `https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=${idType}`,
      { receive_id, msg_type: "text", content: JSON.stringify({ text }) },
      { headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" } }
    );
    res.json(result.data);
  } catch (err) {
    res.status(500).json({ code: 500, msg: err.message });
  }
});
```

添加到 `app.listen(...)` 之前即可。

### 4.4 获取 chat_id/open_id

飞书 Bot 没有主动发消息所需的 `chat_id` 或 `open_id`，需要：

1. **用户在飞书给 Bot 发一条消息** → 服务日志记录 `event.chat_id`
2. **或调用飞书 API 列表已知会话**：

```bash
curl -s -X POST http://localhost:3010/feishu/list_chats | python3 -m json.tool
```

3. **或通过飞书开放平台控制台查找用户 open_id**

### 4.5 使用 curl 发送消息

```bash
# 发送文本
curl -s -X POST http://localhost:3010/feishu/send \
  -H "Content-Type: application/json" \
  -d '{"receive_id":"ou_xxx","receive_id_type":"open_id","text":"消息内容"}'

# 发送图片
curl -s -X POST http://localhost:3010/feishu/send_image \
  -H "Content-Type: application/json" \
  -d '{"receive_id":"oc_xxx","receive_id_type":"chat_id","image_key":"img_v3_xxx"}'
```

### 4.6 启动/重启

```bash
# 查看端口
grep ^PORT= ~/feishu-hermes/.env  # 默认 3010

# 手动启动
cd ~/feishu-hermes && /snap/node/current/bin/node server.js &

# 通过 cloudflared 暴露到公网（自动脚本）
cd ~/feishu-hermes && bash start_cloudflared_quick.sh
```

### 4.7 调试

```bash
# 查看运行日志
tail -f ~/feishu-hermes/logs/app.log

# 检查进程
ps aux | grep feishu | grep -v grep

# 检查 Cloudflare Tunnel 外网地址
cat ~/feishu-hermes/logs/cloudflared.log | grep trycloudflare | tail -1
```

## 5. 知识管理 & 内容导入

- 从飞书文档学习新知识后，存到本地知识库 ~/knowledge/
- feishu-docx 导出的 Markdown 可作为 RAG 语料喂给 Hermes knowledge-base
- **外部内容源导入**（知识星球、微信文章等）→ 详见 `references/content-source-import.md`
  - MarkDownload 浏览器扩展（Chrome/Edge/Firefox）：一键下载页面到 .md
  - zsxq-spider：批量知识星球文章导出为 PDF
  - 飞书公开文档 `.md` 后缀快速获取纯文本
