# 批量脱敏 API Key 实战记录

## 场景

Hermes Agent 运行过程中产生了 24 个 config.yaml.bak.* 历史备份文件，
累计 388 条明文 API Key 需要脱敏。

## 文件分布

- 路径: ~/.hermes/config.yaml.bak.*
- 数量: 24 个
- 密钥格式: sk-xxx (DeepSeek/SiliconFlow/DashScope)
- 总脱敏数: 388 条

## 脱敏脚本

```python
import re, os

files = os.popen("ls ~/.hermes/config.yaml.bak.*").read().strip().split()
total = 0

for fpath in files:
    with open(os.path.expanduser(fpath), 'r') as f:
        content = f.read()

    original = content
    content = re.sub(
        r'^(\s*api_key:\s*)(?!'"'"')(?!$)(.+)$',
        r'\1[REDACTED]',
        content,
        flags=re.MULTILINE
    )
    content = re.sub(
        r'^(\s*api_key:\s*["'"'"'])(?!\s*$)(.+?)(["'"'"'])$',
        r'\1[REDACTED]\3',
        content,
        flags=re.MULTILINE
    )

    count = content.count('[REDACTED]') - original.count('[REDACTED]')
    if count > 0:
        with open(os.path.expanduser(fpath), 'w') as f:
            f.write(content)
        total += count

print(f"处理 {len(files)} 个文件，脱敏 {total} 条密钥")
```

## 验证

```bash
# 确认备份文件无残留明文密钥
grep -h "api_key:" ~/.hermes/config.yaml.bak.* | \
  grep -v "api_key_env" | grep -v "\[REDACTED\]" | grep -v "api_key: ''"
# → 无输出即为通过
```

## 后续迁移

脱敏后执行 config.yaml api_key → api_key_env 迁移（参见 SKILL.md 第7章）：
1. 从 config.yaml 提取全量密钥
2. 写入 .env（权限 600）
3. 将 config.yaml 的 api_key 置空，使用 api_key_env
4. 重启 gateway
