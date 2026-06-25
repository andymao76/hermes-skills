# PyInstaller EXE 反编译工作流 (Ubuntu 24.04)

从 Windows PyInstaller 打包的 .exe 中提取并反编译 Python 源码。

## 工具链

| 步骤 | 工具 | 用途 |
|------|------|------|
| 1 | `pyinstxtractor` | 从 .exe 提取 .pyc 和资源文件 |
| 2 | `uncompyle6` | 将 .pyc 反编译为 .py 源码 |
| 3 | `pyi-archive_viewer` | 从 PYZ 压缩包中提取自定义模块 |

## 完整流程

### 1. 提取 EXE

```bash
# 下载 pyinstxtractor
curl -sL -o /tmp/pyinstxtractor.py \
  https://raw.githubusercontent.com/extremecoders-re/pyinstxtractor/master/pyinstxtractor.py

# 提取（输出到 /tmp/xxx.exe_extracted/）
python3 /tmp/pyinstxtractor.py ~/path/to/app.exe
```

输出目录包含：
- `app.pyc` — 主入口脚本
- `PYZ-00.pyz` — 压缩的 Python 模块仓库
- `PYZ-00.pyz_extracted/` — pyinstxtractor 自动提取的 PYZ 内容（可能为空）
- `base_library.zip` — Python 标准库
- `*.pyd` / `*.dll` — C 扩展 / Windows DLL

### 2. 反编译主入口

```bash
pip install uncompyle6
uncompyle6 /tmp/app.exe_extracted/app.pyc > app_decompiled.py
```

### 3. 提取 PYZ 中的自定义模块

pyinstxtractor 可能跳过 PYZ 提取，需手动操作：

```bash
# 用 pyi-archive_viewer 查看 PYZ 内容
# 先列出所有模块名，找到自定义模块
pyi-archive_viewer /tmp/app.exe_extracted/PYZ-00.pyz

# 交互式提取：输入 X → 输入模块名 → 输入输出路径
```

### 4. 反编译 PYZ 模块

```bash
uncompyle6 /tmp/custom_module.pyc > custom_module.py
```

## 已知限制

| 问题 | 说明 |
|------|------|
| **Python 版本不匹配** | pyinstxtractor 在 py3.12 解析 py3.7 pyc 时会跳过 PYZ 提取（warning），需手动用 `pyi-archive_viewer` 提取 |
| **PYZ 非标准 zip** | PYZ 使用 PyInstaller 自定义压缩格式，不能用 `zipfile` 打开，需用 `pyi-archive_viewer` 或专用提取脚本 |
| **uncompyle6 兼容性** | py3.12 运行环境反编译 py3.7 pyc 时可能报 "Unknown magic number"，但仍可输出部分源码 |
| **PYZ 模块名含路径** | 提取时使用模块名（不含 `.py` 后缀），如 `asn_decode_api` 而非 `asn_decode_api.py` |

## 验证

反编译后的 .py 文件应可通过 Python 语法检查：

```bash
python3 -c "compile(open('decompiled.py').read(), 'decompiled.py', 'exec'); print('OK')"
```

## 应用场景

- 从 PE 格式的 Windows LI 工具中提取 ASN.1 规范和解码逻辑
- 恢复丢失的源码（PyInstaller 打包前的备份丢失时）
- 对比不同版本间的功能差异
