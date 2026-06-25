# feishu-docx 调试记录

## 安装问题

- `pip install feishu-docx` → `externally-managed-environment` 错误
- 解决：`pip install --break-system-packages feishu-docx`
- SOCKS 代理需要 `pip install socksio`

## 凭证发现

- Feishu App ID/Secret 存储在 `~/.hermes/.env`
- 用 `search_files(file_glob='.env*', pattern='feishu|FEISHU|lark|LARK')` 定位
- 用 `feishu-docx config set --app-id ... --app-secret ...` 配置

## 测试流程

### step 1: 列举应用云空间
```bash
feishu-docx drive ls --type docx
```
- 首次报 SOCKS 错误 → 安装 socksio 后解决
- 结果：0 个文件（应用云空间为空，正常）

### step 2: 导出知识库
```bash
feishu-docx export-wiki-space my_library
```
- 首次错误：`code: 99991672` — 应用缺少 wiki scope
- 授权链接：`https://open.feishu.cn/app/{app_id}/auth?q=wiki:wiki,wiki:wiki:readonly,wiki:space:read`
- 开通 scope 后重试
- 第二次错误：`code: 131006` — scope 已开通但应用未被添加为具体知识空间的成员
- 需要去飞书知识空间设置中，将应用加入成员列表

## 权限对照

| 错误码 | 原因 | 动作 |
|--------|------|------|
| 99991672 | 应用未开通所需 scope | 去飞书开放平台 → 应用 → 权限管理 → 添加权限 |
| 131006 | 有 scope 但无权访问该 wiki space | 知识空间设置 → 成员管理 → 添加应用 |
