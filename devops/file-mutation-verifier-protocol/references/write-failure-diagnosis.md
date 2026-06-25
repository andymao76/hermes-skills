# 文件写入失败诊断与恢复

当 `write_file` 或 `patch` 返回 `[Command interrupted]` 或
`bytes_written: 0` 时的系统化诊断方案。

## 错误模式与含义

| 错误关键词 | 含义 |
|-----------|------|
| `File-mutation verifier: N file(s) were NOT modified` | Hermes 自检发现工具声称写入但磁盘未变 |
| `[Command interrupted]` | 写操作执行中被中断（Ctrl+C / 新消息打断 / 工具循环超时） |
| `bytes_written: 0` | 文件完全未写入 |
| `same_tool_failure_warning` | 连续调用同一写入工具失败，循环保护触发 |

## 诊断步骤

### 第一步：确认文件实际状态

```bash
# 检查文件是否存在及大小
ls -lh <可疑文件路径>

# 同时检查预期文件和实际版本
ls -lh ~/knowledge/research/obsidian-tutorial-*.md /tmp/write_obsidian.py 2>/dev/null
```

| ls 输出 | 诊断结论 |
|---------|---------|
| 文件不存在 | 写入完全失败 |
| 文件大小为 0 | 写入被中断，0 字节文件是空壳 |
| 文件存在且 >0 | 可能部分写入，需检查内容 |
| 文件未列出 | 文件从未被创建 |

### 第二步：验证文件内容完整性

```bash
# 用 read_file 确认内容（优先于 cat，支持行号）
read_file(path="...")

# 或用头部/尾部快检
head -5 <路径>    # 检查 YAML frontmatter 是否完整
tail -5 <路径>    # 检查尾部是否截断
wc -l <路径>      # 行数是否符合预期
```

### 第三步：重新生成（选用）

如果文件确实丢失或损坏：

**方案 A**：让 AI 重新用 `write_file` 生成
- 风险：如果中断原因未消除，可能再次失败

**方案 B**：用终端 heredoc 写入（推荐，不受 write_file 工具中断影响）

```bash
mkdir -p ~/knowledge/research
cat > ~/knowledge/research/output-file.md <<'EOF'
# 标题

正文内容...
EOF
```

**方案 C**：先输出完整内容到屏幕确认，再让 AI 写入

## 注意事项

- `File-mutation verifier` 警告是 Hermes 的保护机制，拦截的是**中间失败的尝试**
- 同一轮中多次失败的 `write_file` 调用可能只有最后一次实际生效
- 写入工具返回 `"修改成功"` 但 verifier 报告 `NOT modified` → **以 verifier 为准**
- `/tmp/` 下的临时脚本文件在会话结束后被清理，不要依赖
