# Hermes 跨平台迁移指南

> 将 Hermes 从一台机器（或操作系统）迁移到另一台的完整流程。
> 适用场景：Linux → Windows / Linux → macOS / macOS → Windows 等。

## 核心原则

| 要迁移的内容 | `hermes backup` 覆盖？ | 需单独处理？ |
|-------------|----------------------|-------------|
| config.yaml / .env | ✅ 包含 | 路径、Python 路径需按目标 OS 适配 |
| Skills（~/.hermes/skills/） | ✅ 包含 | 跨平台兼容 |
| Sessions 历史 | ✅ 包含 | SQLite 跨平台兼容 |
| Memory / State DB | ✅ 包含 | SQLite 跨平台兼容 |
| Cron 作业 | ✅ 包含（--quick 模式） | 路径可能需适配 |
| 知识库（~/knowledge/） | ❌ **不包含** | 需单独打包 |
| Hermes 源码 / venv | ❌ 有意排除 | 目标机需全新安装 |
| MCP 服务 | ⚠️ 配置在 config.yaml 中 | 命令路径需改为目标 OS |

## 迁移步骤

### 第1步：源机器打包

```bash
# 1. Hermes 全量备份
hermes backup -o ~/hermes-full-backup.zip

# 2. 知识库单独打包（知识库在 ~/knowledge/，不在 ~/.hermes/ 下）
tar czf ~/knowledge-backup.tar.gz -C ~ knowledge/

# 3. 两个文件拷贝到目标机（SMB / scp / U 盘）
```

### 第2步：目标机器恢复

```bash
# 1. 先安装 Hermes（目标 OS 原生版）
# 参考 https://hermes-agent.nousresearch.com/docs/getting-started/installation

# 2. 方案 A：解压 hermes backup zip 到 ~/.hermes/
#    方案 B：用 profile export/import
hermes profile export default -o ~/profile-default.tar.gz   # 源机
hermes profile import ~/profile-default.tar.gz              # 目标机

# 3. 恢复知识库
tar xzf ~/knowledge-backup.tar.gz -C ~/
```

### 第3步：目标 OS 适配要点

| 需要适配的地方 | 原因 | 示例 |
|--------------|------|------|
| **config.yaml 路径** | Linux `/home/user/` → Windows `C:\Users\user\` | 检查所有涉及绝对路径的配置 |
| **MCP 服务 command 路径** | venv Python 路径不同 | Linux: `/home/user/.hermes/venv/bin/python3` → Windows: `C:\Users\user\.hermes\venv\Scripts\python.exe` |
| **terminal.backend** | Windows 原生需设为 `local` | 在 config.yaml 中检查 |
| **.env 换行符** | Windows CRLF 可能导致问题 | 用 VS Code 或 `dos2unix` 统一为 LF |
| **知识库语义索引** | 需在目标机重建 | `cd ~/knowledge && enzyme refresh` |

### 第4步：验证

```bash
hermes doctor               # 检查依赖和配置
hermes chat -q "test"       # 测试基本对话
hermes skills list          # 确认技能完整
```

## 已知问题与陷阱

### MCP 命令路径是最大隐患

config.yaml 中的 `mcp_servers` 配置会引用源机的 Python 路径：
```yaml
mcp_servers:
  db-query:
    command: "/home/andymao/.hermes/venv/bin/python3"  # ← 必须改为目标 OS 路径
```
Windows 上应改为：
```yaml
    command: "C:\\Users\\andymao\\.hermes\\venv\\Scripts\\python.exe"
```
或使用 forward slashes（Hermes 工具支持）：
```yaml
    command: "C:/Users/andymao/.hermes/venv/Scripts/python.exe"
```

### 知识库酶索引需重建

`enzyme refresh` 在 Windows 上可能需要额外适配。迁移后优先运行：
```bash
cd ~/knowledge && bash ~/.hermes/scripts/enzyme-init.sh
```

### .env 文件编码

Windows 的 Notepad 可能会给 `.env` 加上 UTF-8 BOM，导致 Hermes 解析失败。
解决方法：用 VS Code 以 UTF-8 without BOM 重新保存。

## 相关命令速查

| 命令 | 用途 |
|------|------|
| `hermes backup` | 全量备份（config、skills、sessions、memory） |
| `hermes backup --quick` | 快速备份（仅关键状态文件） |
| `hermes profile export <name>` | 导出指定 profile |
| `hermes profile import <file>` | 导入 profile |
