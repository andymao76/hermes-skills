# 百度网盘文档导入知识库 — 完整操作路线图

> 当用户的通信/3GPP/厂商文档（doc/docx/pdf/chm/html/md）存在于百度网盘中时，
> 通过 bypy 下载后批量转换导入 knowledge-base。

## 执行步骤（按顺序）

### 0. 前提条件
- Python 3.8+（已满足）
- pandoc（已安装 3.1.3）
- LibreOffice Writer（已安装 24.2.7）
- p7zip：`apt install p7zip-full`（CHM 解压用）
- 百度网盘账号

### 1. 安装 bypy
```bash
pip3 install --user --break-system-packages bypy
export PATH="$HOME/.local/bin:$PATH"   # 确保 PATH 包含用户 bin
```

### 2. 授权（手动交互）
```bash
python3 -m bypy info
```
打开输出的 OAuth URL → 浏览器登录百度 → 粘贴授权码。

### 3. 网盘准备
在百度网盘网页端把要导入的文件移到 `/apps/bypy/` 目录下。
（bypy 只能操作此目录）

### 4. 下载到本地
```bash
python3 -m bypy downdir / ~/baidupan_docs/
```
大文件可分批：`python3 -m bypy list` 先看目录结构，然后逐个子目录下载。

### 5. 转换导入
```bash
# 预览
python3 ~/.hermes/scripts/baidupan_convert.py --dry-run

# 分批执行（避免一次处理太多 PDF 超时）
python3 ~/.hermes/scripts/baidupan_convert.py --limit 20
python3 ~/.hermes/scripts/baidupan_convert.py --limit 20   # 第二次
```

### 6. 验证
```bash
python3 ~/.hermes/scripts/knowledge/search_knowledge.py "3GPP" --limit 5
python3 ~/.hermes/scripts/knowledge/search_knowledge.py "5G" --limit 5
```

## 预期数据量

用户描述"大概5GB"通信/3GPP类文档（.md .doc .docx .pdf .chm .html）。

导入后知识库：
- 文件数：从当前 24 个增加到约 200~500 个
- 总大小：从当前 9.6MB 增加到约 100~200MB（转换后文本膨胀）
- 转换耗时：约 30min~2h（取决于 PDF 数量和文件大小）

## 备选方案：BaiduPCS-Go（推荐大批量/全目录访问）

当 bypy 因为以下原因不满足需求时，改用 BaiduPCS-Go：

| 场景 | bypy | BaiduPCS-Go |
|------|------|-------------|
| 文件在 `/apps/bypy/` 内 | 可用 | 可用 |
| 文件在网盘任意目录 | 不可用（需手动移动） | **可用** |
| 免费下载速度 | 80~200 KB/s | 速度快（社区优化） |
| 安装方式 | pip 安装 | 下载二进制 |
| 授权方式 | OAuth 授权码 | BDUSS/STOKEN/cookies |

### 安装

```bash
export https_proxy=http://127.0.0.1:7897   # GitHub 可能被墙
wget "https://github.com/qjfoidnh/BaiduPCS-Go/releases/download/v4.0.1/BaiduPCS-Go-v4.0.1-linux-amd64.zip" -O /tmp/BaiduPCS-Go.zip
unzip /tmp/BaiduPCS-Go.zip -d /tmp/baidupcs
mkdir -p ~/.local/bin
cp /tmp/baidupcs/BaiduPCS-Go-v4.0.1-linux-amd64/BaiduPCS-Go ~/.local/bin/
chmod +x ~/.local/bin/BaiduPCS-Go
# 确认安装
~/.local/bin/BaiduPCS-Go help
```

### 登录方式

BaiduPCS-Go 提供三种登录方式：

**方式 A：交互式登录（PTY 模式，不推荐）**
```bash
BaiduPCS-Go login
```
需要在 pty 模式下按提示输入用户名和密码。在非交互式 CLI 环境中 PTY 模式下仍然可能 EOF 失败。

**方式 B：BDUSS + STOKEN 登录（推荐）**
从浏览器获取 BDUSS 和 STOKEN：
1. 在 Chrome 打开 `https://pan.baidu.com`（需已登录）
2. F12 → Application → Cookies → `https://pan.baidu.com`
3. 找到 `BDUSS` 和 `STOKEN` 两个 cookie 的值
4. 登录：
```bash
BaiduPCS-Go login -bduss="BDUSS值" -stoken="STOKEN值"
```

**方式 C：cookies 字符串登录**
```bash
BaiduPCS-Go login -cookies="BDUSS=xxxxx; BAIDUID=yyyyyy; STOKEN=***"
```

### 登录验证

登录成功后：
- 输出：`百度帐号登录成功: username`
- 可用 `BaiduPCS-Go ls /` 验证目录列表
- 配置文件保存在 `~/.config/BaiduPCS-Go/pcs_config.json`
- 登录一次后无需重复授权，token 持久化

### 常用命令

```bash
BaiduPCS-Go ls /                   # 列出根目录
BaiduPCS-Go cd /通信技术            # 切换目录
BaiduPCS-Go download /目标目录/    # 下载整个目录到 savedir
BaiduPCS-Go download /目标目录/文件.docx  # 下载单个文件
BaiduPCS-Go who                     # 查看当前登录用户
BaiduPCS-Go logout                  # 退出登录
```

### savedir 陷阱（重要）

BaiduPCS-Go 的 `download` 使用全局 `savedir` 配置（在 `~/.config/BaiduPCS-Go/pcs_config.json` 中设置）：

```bash
BaiduPCS-Go config set -savedir=/home/user/baidupan_docs/
```

下载后的文件路径为：`$savedir/<user_id>/<网盘路径>`，例如：
- 下载 `/5g/5G_NSA组网信令.docx` → 实际保存到 `baidupan_docs/364769201_andymao76/5g/5G_NSA组网信令.docx`
- 每个 BaiduPCS-Go 登录用户有不同 `user_id` 前缀

这意味着：
1. 不同目录的下载文件会混合在同一个 `<user_id>/` 子目录下
2. 网盘路径的子目录结构会被保留
3. 转换脚本用 `--input` 指向 `<user_id>/` 子目录即可递归扫描

**配置优化**（非VIP下载性能）：
```bash
BaiduPCS-Go config set -max_parallel=5         # 下载总并发量（非SVIP不可>1，但设5也有效果）
BaiduPCS-Go config set -max_download_load=10    # 同时下载文件数（默认1）
BaiduPCS-Go config set -cache_size=262144       # 256KB 下载缓存
```

### 注意事项

- BDUSS 和 STOKEN 是敏感凭据，必须确保安全
- 配置文件保存在 `~/.config/BaiduPCS-Go/`（BaiduPCS-Go v4.0+）
- 登录一次后无需重复授权，token 持久化

## 已知问题与排障

1. **bypy 下载慢**：免费 API 80~200KB/s，5GB 约需 8~15 小时。建议夜间后台运行或改用 BaiduPCS-Go
2. **中文文件名**：某些 3GPP 文档含中文名，bypy 和 filname 编码在部分 Shell 下可能有乱码，不影响转换
5. **PDF 转换**：pandoc 不支持 `pdf` 作为输入格式（`Unknown input format pdf`）。必须使用 `pdftotext` 替代：
   - `baidupan_convert.py` 的 `convert_pdf_to_md` 函数使用 `pdftotext -layout` 提取文本
   - `pdftotext` 来自 `poppler-utils` 包：`apt install poppler-utils`
   - PDF 转出的 markdown 用 ````text` 块包装，保留原始格式
6. **patch 工具误删行**：使用 `old_string` 做替换时，如果 `old_string` 和 `new_string` 行尾不一致（如空行数不同），patch 可能多删或漏行。替换后务必用 `read_file` 或 `grep` 验证文件完整性，特别检查：
   - 被替换段落前后的空行
   - 文件尾部的换行符
   - 是否意外删除了附近的独立变量定义（如 `SKIP_EXT`、`stats` 等）
4. **重复导入**：脚本已处理目标文件已存在的情况，会加 `_v2.md` 后缀，不会覆盖
5. **授权令牌陷阱**：
   - `echo "code" | python3 -m bypy info` 会超时（管道输入不工作）
   - pty 模式下交互输入也会超时
   - **正确做法**：直接运行 `python3 -m bypy info`，在终端粘贴授权码按 Enter
   - **部分授权的残留 token**：如果 `bypy info` 被中断，`~/.bypy/bypy.json` 可能已写入不完整的 token。此时再次运行 `bypy info` 仍然要求授权，但旧 token 可能已可用——直接用 `python3 -m bypy list` 测试
   - Token 位置是 `~/.bypy/bypy.json` 而非 `~/.bypy.json`（bypy 不同版本有差异）
6. **文件在网盘根目录/其他目录**：bypy **只能访问** `/apps/bypy/` 目录。如果文档在网盘别的文件夹，必须手动移动到「我的应用数据→bypy」目录下。这是最常见的"空结果"原因
7. **BaiduPCS-Go GitHub 下载需代理**：`export https_proxy=http://127.0.0.1:7897`，否则因 GFW 超时
8. **BaiduPCS-Go PTY 登录失败**：非交互式 CLI 环境中 PTY 模式仍然可能 EOF，改用 BDUSS + STOKEN 方式
