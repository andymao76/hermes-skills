# DeepL API 配置参考

## 套餐信息

| 项目 | Free 版 | Pro 版 |
|------|---------|--------|
| 月额度 | 500,000 字符 | 无限 |
| 价格 | 免费 | $5.49/月起 |
| Key 格式 | `xxx:fx` | `xxx` |
| 端点 | `https://api-free.deepl.com/v2/translate` | `https://api.deepl.com/v2/translate` |
| 重置日 | 每月 14 号 | — |
| 术语表 | ❌ | ✅ |
| 文档翻译 | ❌ | ✅ |

## 申请步骤

### 有国外信用卡

1. 打开 https://www.deepl.com/zh/pro#developer
2. 选「DeepL API Free」→「免费注册」
3. 填写 VISA/MasterCard 验证（仅验证，不扣费）
4. 登录 → 账户 → API 密钥 → 复制 Key

### 无国外信用卡

1. 淘宝/闲鱼搜索「DeepL API Free 账号」
2. 购买已开通的账号（约 5-20 元）
3. 登录修改密码，获取 API Key

> 国内发行的 VISA/MasterCard 无法通过 DeepL 验证，必须境外卡或购买。

## Key 写入配置

获取 Key 后，写入 `~/.hermes/.env`：

```bash
# DeepL API Free
DEEPL_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx:fx
```

## Python 调用脚本

`~/.hermes/scripts/deepl-translate.py`（获取 Key 后创建）：

```python
#!/usr/bin/env python3
"""DeepL 翻译脚本。用法: python deepl-translate.py "文本" --target ES"""
import os, sys, json, argparse
import urllib.request

API_KEY = os.environ.get("DEEPL_API_KEY", "")
API_URL = "https://api-free.deepl.com/v2/translate"

SUPPORTED_LANGS = {
    "ZH": "中文", "EN": "英语", "ES": "西班牙语",
    "FR": "法语", "DE": "德语", "JA": "日语",
    "KO": "韩语", "PT": "葡萄牙语", "RU": "俄语",
}

def translate(text, target_lang="ES"):
    data = json.dumps({
        "text": [text],
        "target_lang": target_lang,
    }).encode()
    req = urllib.request.Request(API_URL, data=data, headers={
        "Authorization": f"DeepL-Auth-Key {API_KEY}",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
    return result["translations"][0]["text"]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("text", help="要翻译的文本")
    parser.add_argument("--target", "-t", default="ES", help="目标语言代码")
    args = parser.parse_args()
    
    if not API_KEY:
        print("❌ 请先设置 DEEPL_API_KEY 环境变量", file=sys.stderr)
        sys.exit(1)
    
    result = translate(args.text, args.target)
    print(result)
```

## API 关键错误码

| 状态码 | 含义 | 处理 |
|--------|------|------|
| 403 | 认证失败/额度耗尽 | 检查 Key 是否正确，查看额度 |
| 456 | 超出月配额 | 等 14 号重置或升级 Pro |
| 400 | 参数错误 | 检查 target_lang 代码是否正确 |

## 第三方集成

- **沉浸式翻译**：设置页 → 翻译服务 → DeepL → 填入 API Key
- **Zotero 翻译插件**：首选项 → 翻译 → DeepL → 填入 Key
- **Bob (macOS)**：偏好设置 → 服务 → 翻译 → DeepL
- **Pot (跨平台)**：设置 → 接口设置 → DeepL
