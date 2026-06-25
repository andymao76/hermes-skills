# DeepL API 注册与配置详细记录

## 注册流程

1. 访问 https://www.deepl.com/zh/pro#developer
2. 选择「DeepL API Free」计划
3. 点击「免费注册」
4. 填写邮箱、密码
5. **绑定国外信用卡**（VISA/MasterCard）验证身份
   - 中国发行的银联/VISA/MasterCard 均不支持
   - 需要卡片的发卡国在 DeepL 支持的国家列表中
   - 没有国外卡可考虑：淘宝/闲鱼购买已开通 API Free 的账号
6. 注册完成后登录 → 右上角头像 → 「账户」
7. 滚动到「API 密钥」区域
8. 复制 Key，格式如 `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx:fx`

## Key 格式说明

- Free 版 Key 以 `:fx` 结尾
- Pro 版 Key 无后缀或不同后缀
- 使用时必须包含完整 Key（含 `:fx`）
- 丢失 `:fx` 会导致 403 Forbidden

## API 端点

| 版本 | Free 端点 | Pro 端点 |
|------|-----------|----------|
| v2 | `https://api-free.deepl.com/v2/translate` | `https://api.deepl.com/v2/translate` |

## 免费额度

- **500,000 字符/月**
- 重置日：每月 **14 号**（不是月初！）
- 中文字符计数：1 个汉字 = 1 个字符
- 超出后返回 456 Quota Exceeded

## 403 错误排查清单

1. Key 是否完整（含 `:fx`）
2. 登录 DeepL 账户确认 Key 状态为「活跃」
3. 新注册可能需要几小时激活
4. API 端点是否匹配（Free key 用 api-free.deepl.com）
5. Authorization header 格式：`DeepL-Auth-Key <key>`
6. Content-Type: `application/json`

## Hermes 工具写 Key 的陷阱

`write_file` 和 `patch` 工具会检测并脱敏 API Key 模式。如果在脚本中硬编码 Key，实际写入的会是截断版本。解决方案：脚本中通过 `open()` 从 `~/.hermes/.env` 运行时读取。

## 实测验证（2024-06-08）

```
Key: 07061344-682d-4281-a27f-629b38b0de1b:fx (39 chars)
状态: 403 → 修复写入后 200 OK
中→西: "你好世界" → "Hola mundo" ✓
西→中: "Hola" → "你好" ✓
中→英: "学会西语用处大" → "Learning Spanish is really useful" ✓
```
