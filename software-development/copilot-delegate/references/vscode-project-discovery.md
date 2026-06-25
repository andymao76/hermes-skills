# VS Code 本地项目发现方法

当用户问"我有什么项目"或"在我的机器上找软件项目"时，按以下步骤系统化扫描。

---

## 步骤 1：检查 VS Code 工作区记录

VS Code 在 `~/.config/Code/User/workspaceStorage/` 下为每个打开的 workspace 保存一个目录，目录名是 hash。每个目录内有 `workspace.json`，记录打开的文件夹或 `.code-workspace` 文件路径。

```bash
for d in ~/.config/Code/User/workspaceStorage/*/; do
    wsfile="$d/workspace.json"
    if [ -f "$wsfile" ]; then
        python3 -c "import json; print(json.load(open('$wsfile')))"
    fi
done
```

输出示例：
```json
{"workspace": "file:///home/andymao/myprogram.code-workspace"}
{"folder": "file:///home/andymao/myprogram"}
```

**路径解码：** `file:///home/andymao/myprogram` → `/home/andymao/myprogram`

## 步骤 2：检查 VS Code 最近打开历史

`~/.config/Code/User/globalStorage/storage.json` 中存有最近打开的文件/项目列表：

```bash
python3 -c "
import json
st = json.load(open(os.path.expanduser('~/.config/Code/User/globalStorage/storage.json')))
paths = st.get('lastOpenedPaths', st.get('recentlyOpenedPathsList', []))
for p in paths:
    if isinstance(p, dict):
        folder = p.get('folderUri', p.get('path', str(p)))
    else:
        folder = str(p)
    if folder:
        print(folder)
"
```

## 步骤 3：扫描常见项目目录

```bash
for dir in ~/projects ~/code ~/dev ~/src ~/work; do
    if [ -d "$dir" ]; then
        echo "=== $dir ==="
        ls -la "$dir"
    fi
done
```

## 步骤 4：发现 Git 仓库

在找到的目录中检查 `.git` 子目录，确认是实际项目而非普通目录：

```bash
find ~/projects ~/code ~/myprogram -maxdepth 3 -name ".git" -type d 2>/dev/null | sed 's|/.git||'
```

## 步骤 5：项目分析和报告

对每个项目输出：
- **用途** — 该项目做什么的
- **技术栈** — 语言/框架/工具
- **文件结构** — 关键文件和目录
- **规模** — 代码行数、文件数
- **Git 源** — 如果是 clone 的，记录 upstream URL

**报告格式示例：**
```
| 项目 | 路径 | 技术栈 | 规模 | 类型 |
|------|------|--------|------|------|
| myprogram | ~/myprogram | Python + C | 2 文件/6KB | 自建工具 |
| Awesome-Dify-Workflow | ~/projects/github-workspace/... | YAML DSL | 46 文件/1MB | Clone 学习 |
```

## 已知限制

- VS Code snap 版和 deb 版的 config 路径不同：snap 版在 `~/.config/Code/`，deb 版也是这个路径；flatpak 版在 `~/.var/app/com.visualstudio.code/config/Code/`
- 远程 SSH/容器工作区不会出现在本地 workspaceStorage 中
- 如果用户用其他编辑器（vim, JetBrains, Zed），此方法无效
