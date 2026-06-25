# Enzyme — 编译时语义记忆插件

安装日期: 2026-06-08
版本: v0.5.15
仓库: https://github.com/jshph/enzyme-skill

## 安装步骤（已验证）

```bash
# 1. 克隆插件到 Hermes plugins 目录
git clone --depth 1 https://github.com/jshph/enzyme-skill ~/.hermes/plugins/enzyme-skill

# 2. 安装 CLI 二进制
bash ~/.hermes/plugins/enzyme-skill/install.sh
# 自动下载 ~33MB Linux x86_64 二进制到 ~/.local/bin/enzyme
# 自动打开浏览器完成 enzyme.garden 账号注册

# 3. 启用 Hermes 插件
hermes plugins enable enzyme
systemctl --user restart hermes-gateway

# 4. 初始化 vault（在 ~/knowledge 目录）
cd ~/knowledge && enzyme init

# 5. 验证
enzyme status
enzyme petri
enzyme catalyze "测试关键词"
```

## 选项: `--use-env-llm`

```bash
enzyme init --quiet --use-env-llm    # 使用 OPENROUTER_API_KEY 或 OPENAI_API_KEY
enzyme refresh --quiet --use-env-llm # 同上
```

不传 `--use-env-llm` 则使用 enzyme 托管的免费 credits。

## 凭据位置

- 账号: 通过 install.sh 浏览器流程完成
- 凭据文件: `~/.enzyme/auth.json`
- 配置: `~/.enzyme/config.toml`

## 性能

| 阶段 | 时间 |
|------|------|
| init（418文件） | ~22s |
| refresh（无变更） | ~100ms |
| catalyze 搜索 | <1ms |
| petri 概览 | <50ms |

## Pitfalls

- `enzyme refresh` 对大 vault（400+文件）可能超时（>30s），旧索引始终有效
- 不要编辑 `~/.hermes/plugins/enzyme-skill/` 下的文件——从 enzyme-rust 同步，CI 覆盖
- `ENZYME_VAULT_ROOT` 环境变量可指定 vault 路径，否则用当前目录
- `hermes plugins enable enzyme` 需要重启 gateway 才生效
