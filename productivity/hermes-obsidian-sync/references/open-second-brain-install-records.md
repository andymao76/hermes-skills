# Open Second Brain 安装记录

## 当前状态

| 项目 | 状态 |
|------|------|
| 插件安装 | ✅ 已安装 v1.0.1 (`hermes plugins install itechmeat/open-second-brain`) |
| 插件启用 | ✅ `hermes plugins enable open-second-brain` |
| Bun 运行时 | ✅ v1.3.14 (`curl -fsSL https://bun.sh/install \| bash`) |
| o2b CLI 发布 | ✅ `o2b install-cli` → `~/.local/bin/` (`o2b`, `vault-log`, `o2b-hook`) |
| vault 初始化 | ✅ `o2b init --vault ~/Documents/Obsidian\ Vault` |
| memory provider | ✅ 已设置为 `open-second-brain` (config.yaml 中 `memory.provider: open-second-brain`) |
| o2b doctor | ✅ 全部 OK |

## memory provider 切换

从 holographic 切换到 open-second-brain：
```bash
# 修改 config.yaml
sed -i 's/provider: holographic/provider: open-second-brain/' ~/.hermes/config.yaml

# 验证
hermes memory status
# → Provider: open-second-brain, available ✓

# 当前已安装的 memory provider 列表
# × holographic（原活跃，现在非活跃）
# * open-second-brain (local) ← active
```

## 已知限制

### symlink 文件不被索引

O2B 的索引器（`o2b search index`）默认不跟踪 symlink 目录。你的 vault 有 `knowledge → ~/knowledge/` symlink，422 个 knowledge 文件不被索引。

验证：
```bash
sqlite3 ~/Documents/Obsidian\ Vault/.open-second-brain/brain.sqlite "SELECT count(*) FROM documents;"
# → 1（仅 欢迎.md）
```

这意味着：
- O2B 不会搜索 knowledge 中已有的 422 个文件
- 但 Hermes 的 memory provider 功能正常——新写入 `Brain/` 的记忆会正常工作
- 旧知识的搜索仍然靠你的 FTS5 搜索脚本

## 恢复为 holographic

```bash
sed -i 's/provider: open-second-brain/provider: holographic/' ~/.hermes/config.yaml
hermes gateway restart
```
