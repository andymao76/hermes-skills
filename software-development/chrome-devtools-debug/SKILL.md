---
name: chrome-devtools-debug
description: Chrome DevTools 前端调试与 API 请求跟踪 — Network/Initiator/Timing 分析，适用 WEB-UI 前后端问题排查
priority: normal
category: software-development
---

# Chrome DevTools 调试与 API 请求跟踪 Skill

当用户需要排查 WEB 前端问题（API 请求失败、数据不匹配、响应慢、调用链不明确）时，使用本 Skill。

---

## 1. 打开 DevTools

| 操作 | 快捷键/方式 |
|------|-------------|
| 打开 DevTools | `F12` 或 `Ctrl+Shift+I` (Win/Linux) / `Cmd+Option+I` (Mac) |
| 切换到 Network 面板 | 点击 `Network` Tab |
| 清空请求记录 | 点击 🗑 图标 |
| 保留跨页面请求 | 勾选 `Preserve log` |
| 禁用缓存 | 勾选 `Disable cache`（模拟首次访问） |

---

## 2. Network 面板核心功能

### 2.1 录制与筛选

**请求类型过滤按钮**（点击多个可组合，按住 Ctrl/Cmd）：
`All` | `Fetch/XHR` | `JS` | `CSS` | `Img` | `Media` | `Font` | `Doc` | `WS` | `Wasm`

**高级筛选（Filter 框）**：
| 语法 | 示例 |
|------|------|
| `domain:` | `domain:example.com` |
| `status-code:` | `status-code:200` / `status-code:4..` |
| `method:` | `method:POST` |
| `mime-type:` | `mime-type:application/json` |
| `larger-than:` | `larger-than:1000` (字节) |
| `has-response-header:` | `has-response-header:Content-Type` |
| `is:` | `is:running` (WebSocket) |
| `url:` | `url:/api/query` |
| 组合 | `status-code:200 method:POST url:/query` |

### 2.2 请求详情面板

点击一个请求后，在右侧面板查看：

| Tab | 用途 |
|-----|------|
| **Headers** | 请求 URL、方法、状态码、请求头、响应头 |
| **Payload** | 请求体参数（POST 表单/JSON） |
| **Preview** | 响应数据格式化预览 |
| **Response** | 原始响应内容 |
| **Initiator** | 调用链（谁触发了这个请求） |
| **Timing** | 各阶段耗时明细 |
| **Cookies** | 请求携带的 Cookie |

---

## 3. Initiator 调用链分析

### 3.1 定位调用链

1. Network 面板 → 点击目标请求
2. 点击 **Initiator** Tab
3. 查看调用栈（由下往上读，底部是最外层触发源，顶部是实际发请求的位置）

### 3.2 调用栈解读

```
Promise.then
  Dr @ request.ts:107         ← Axios/HTTP 请求封装（实际发请求）
  s  @ targetQuery.ts:24      ← 业务逻辑层（封装参数）
  Pe @ middle.vue:1056        ← 中间处理层
  be @ QTable.vue:537         ← 组件触发层（用户交互）
```

### 3.3 Initiator 类型

| 类型 | 说明 |
|------|------|
| **Parser** | 由 HTML/CSS 解析触发（如图片、样式表加载） |
| **Script** | 由 JavaScript 代码触发（最常见，API 调用一般属此类） |
| **Redirect** | 由重定向触发（301/302） |
| **Other** | 初始导航、preload、favicon 等 |

---

## 4. Timing 响应时间分析

### 4.1 各阶段含义

| 阶段 | 说明 | 异常阈值 |
|------|------|----------|
| Queueing | 请求排队等待 | > 100ms |
| Stalled | 请求停滞 | > 100ms |
| DNS Lookup | DNS 解析 | > 50ms |
| Initial Connection | TCP 连接 | > 100ms |
| SSL | SSL 握手 | > 200ms |
| Request Send | 发送请求 | > 10ms |
| Waiting (TTFB) | 等待服务器首个字节 | > 3s（后端耗时长） |
| Content Download | 下载响应内容 | > 500ms |

### 4.2 排查思路

```
TTFB 过长 → 后端/数据库问题
Content Download 过长 → 返回数据量过大
DNS/TCP/SSL 过长 → 网络/基础设施问题
Queueing/Stalled 过长 → 浏览器并发限制或前序请求阻塞
```

---

## 5. 后端接口排查流程

当 WEB UI 数据异常（无数据、报错、响应慢）时：

```
用户报告 WEB UI 异常
        ↓
F12 → Network → 找到目标 API 请求
        ↓
检查状态码
  ├── 200 → 检查 Response 数据是否完整正确
  ├── 4xx → 参数错误/权限不足（检查 Payload）
  ├── 500 → 后端服务异常（查服务器日志）
  └── 404 → 接口路径错误
        ↓
检查 Payload 参数
  └── 参数是否正确（如 tid、mapId 等）
        ↓
检查 Initiator 调用链
  └── 确认请求从哪个组件、哪个函数触发
        ↓
查看 WEB LOG（后端日志）
  └── grep 请求 ID 或关键参数查运行时信息
        ↓
数据库验证
  └── 根据参数查数据库确认数据是否存在
```

---

## 6. 常用技巧

### 重发 XHR 请求
- 选中请求 → 按 `R` 键，或右键 → `Replay XHR`

### 模拟慢速网络
- Network 面板顶部 **Throttling** 下拉框 → `Slow 3G` / `Fast 3G`
- 可自定义：Throttling → `Custom → Add...`

### 模拟离线
- Throttling → `Offline`

### 搜索请求内容
- `Ctrl+F` → 搜索请求 URL、Header、Payload、Response

### 导出 HAR 文件
- 右键任意请求 → `Save all as HAR with content` → 分享给后端排查

### 覆盖响应头（本地调试）
- Headers Tab → 响应头值旁边出现编辑按钮 → 点击可本地覆盖

---

## 7. 与 WEB LOG 关联调试

1. 在 WEB UI 执行操作（如查询）
2. DevTools 记录到请求 URL
3. 登录服务器搜索 WEB LOG：

```bash
# 搜索相关日志
grep "detailQuery" /path/to/logs/*.log | tail -20

# 提取请求参数（如 tid、mapId）
grep "15_8e2598c1db7667c0a133d8b1495616a1" /path/to/logs/*.log
```

4. 用日志中的参数查数据库验证：
```sql
SELECT * FROM hts_lig_hi2 WHERE tid = '<tid>' AND clue_id = <mapId>;
```

5. 对比 WEB UI 数据与数据库数据是否一致

---

## 8. 快速参考

| 场景 | 操作 |
|------|------|
| 打开 DevTools | F12 |
| 筛选 API 请求 | 点击 `Fetch/XHR` 按钮 |
| 查看请求参数 | Headers / Payload Tab |
| 查看返回数据 | Preview / Response Tab |
| 查看调用链 | Initiator Tab |
| 查看耗时 | Timing Tab |
| 重发请求 | 选中 → 按 R |
| 模拟慢网 | Throttling → Slow 3G |
| 保留日志 | 勾选 Preserve log |
| 搜索请求 | Ctrl+F |
| 导出 HAR | 右键 → Save all as HAR |
| 搜索后端日志 | `grep <参数> <日志文件>` |
## 关联数据库 | 从日志提取参数后查 SQL |

## 9. 项目参考文件

本 skill 包含以下项目特定参考文件，加载 skill 后按需查看：

| 文件 | 说明 |
|------|------|
| `references/owls-web-debug.md` | OWLS (A1 项目苏丹) WEB-UI 跟踪 — API 端点、调用链、WEB LOG 关联、数据库验证 |
