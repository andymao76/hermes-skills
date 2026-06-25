# GitHub 项目上传清单

适用于上传 Python/Flask 工具到 `github.com/andymao76/ops-monitoring` 的操作规范。

## 必包含文件

| 文件 | 用途 | 说明 |
|------|------|------|
| `README.md` | 项目说明 | 快速部署、功能列表、结构图 |
| `requirements.txt` | 依赖清单 | `pip install -r requirements.txt` 可用 |
| `.gitignore` | 排除项 | venv/, __pycache__, logs/, uploads/, *.pdf, .vscode/ |
| `docs/VERSION_HISTORY.md` | 版本历史 | 记录每次版本变更摘要 |

## .gitignore 示例

```
venv/
__pycache__/
*.pyc
*.pyo
src/logs/
src/uploads/
backup/
build/
.vscode/
*.pdf
.DS_Store
```

## Flask 项目特殊处理

### static_folder 404 问题

当 Flask app 放在 `src/` 子目录时：

```python
# ❌ 会找 src/static/，但 static/ 在项目根目录
app = Flask(__name__)

# ✅ 显式指定 static 目录路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=os.path.join(BASE_DIR, '..', 'static'), static_url_path='/static')
```

### dpkt 导入命名冲突陷阱

当项目中同时使用 `dpkt` 和其他操作 `data` 变量的代码时，**不要在全局作用域 import dpkt**。dpkt 的 `Packet.__getitem__` 会拦截 `data[slice]` 操作并抛出 `KeyError`，导致 `bytes[offset:]` 切片意外失败：

```
# ❌ 全局导入 — data 变量可能被 dpkt 污染
import dpkt

def pre_decode(data):
    single_len = data[14:]   # ← 触发 KeyError: slice(14, None, None)

# ✅ 局部导入 — 隔离作用域
def pre_decode(data):
    import dpkt
    ...
```

需要在函数或方法内部局部 `import dpkt`，避免 dpkt 的 `__getitem__` 覆盖 bytes 对象的切片操作。

### .vscode/settings.json

创建 `.vscode/settings.json` 指定 venv 路径：

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.terminal.activateEnvironment": true,
    "files.exclude": {
        "venv/": true,
        "**/__pycache__": true,
        "src/logs/": true,
        "src/uploads/": true
    }
}
```

## 上传步骤

```bash
# 1. 克隆仓库
cd /tmp && rm -rf ops-monitoring
git clone https://github.com/andymao76/ops-monitoring.git

# 2. 复制文件到对应子目录
cp <src_file> ops-monitoring/<subdir>/<dest_file>

# 3. 提交推送
cd ops-monitoring
git add -A
git commit -m "类型: 描述信息"
git push origin main

# 4. 清理
cd /tmp && rm -rf ops-monitoring
```

### Commit 信息格式

- 新功能: `feat: 功能描述`
- bug修复: `fix: 修复内容`
- UI/样式: `style: 修改内容`
- 文档: `docs: 文档描述`
- 版本发布: `release: bump to VX.Y — 标题`

## 常见陷阱

### list_input_files 扫描目录时误入假 .gz 文件

`list_input_files()` 列出目录下所有文件，包括 `.gz` 后缀的假压缩文件。如果文件实际是纯文本但扩展名为 `.gz`，`iter_lines_from()` 会调用 `gzip.open()` 导致 `BadGzipFile` 崩溃：

```
BadGzipFile: Not a gzipped file (b'[2')
```

**规避方式**：
- 用带 `.txt` 后缀的文件名做输入，或用 `--limit` 限定文件列表
- 修改 `list_input_files` 跳过已知的假 `.gz` 文件（`.endswith('.gz')` 且不是真正 gzip 头 `\\x1f\\x8b`）
- 更好的方式：建一个只含 `.txt` 文件的临时目录，软链过去
