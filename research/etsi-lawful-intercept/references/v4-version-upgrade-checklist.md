# V4 版本升级文档检查清单

用户习惯：每次版本升级时必须同步更新 **全部** 相关文档，不能只改代码。

---

## 一、版本升级文档更新

### 必须更新的文档

| # | 文件 | 类型 | 更新内容 |
|---|------|------|---------|
| 1 | `VERSION_HISTORY.md` | Markdown | 新增版本条目，逐项列出所有新增功能/修复/变更 |
| 2 | `README.md` | Markdown | V4新增功能列表、解码模式表、架构变化 |
| 3 | `ETSI_ASN1_Assistant_V{n}_系统设计文档.md` | Markdown | 修订记录表追加新版本行 + frontmatter版本号更新 |
| 4 | `ETSI_ASN1_Assistant_V{n}_系统设计文档.pdf` | PDF | 从 .md 重新生成（pandoc + wkhtmltopdf） |
| 5 | `LI_ASN1解码工具_架构文档.md` | Markdown | 新增 V{n} 扩展章节（新增模块表/增强功能/解析能力表） |
| 6 | `v{n}_architecture.html` | HTML | 更新架构图（新增模块卡片、扩展层、版本号） |
| 7 | `v{n}_architecture.svg` | SVG | 从 HTML 提取 SVG 元素 |
| 8 | `v{n}_architecture_a4.pdf` | PDF | wkhtmltopdf 从 HTML 生成 |
| 9 | `v{n}_architecture_a4.png` | PNG | Chrome headless 截图 |

### 代码修改检查清单

| # | 修改项 | 说明 |
|---|--------|------|
| 1 | `app_linux_v{n}.py` import | 添加新模块 import |
| 2 | 新增路由 | `@app.route("/x-interface")` 渲染页 + API |
| 3 | vmap 扩展 | 新增解码模式映射 |
| 4 | decode 分支 | PCAP/IRI 解码分支区分 x3/hi1/常规 三种路径 |
| 5 | 模板版本号 | 版本徽章更新 + 导航链接 |

---

## 二、BugFix 文档工作流

每次修复 Bug 时，必须按以下流程记录，缺一不可：

### 步骤

```
1. 测试报告    → docs/tests/V{版本}_{功能}_测试报告.md
2. 变更日志    → docs/changelog/{日期}-fix-{问题描述}.md
3. 经验沉淀    → ~/knowledge/知识/技能/hermes-asn1/{topic}.md
4. 软件日志    → docs/changelog/ (同文件, 含根因分析)
5. 本地 Git    → git add + commit (ops-monitoring 仓库)
6. GitHub      → git push (注意代理: HTTPS_PROXY=http://127.0.0.1:7897)
```

### 各文档模板说明

**测试报告** (`docs/tests/`):
- YAML frontmatter (title/version/date/tester/test_type)
- 测试环境表（OS/浏览器/服务端版本/日志路径）
- 每个 TC 一个表格：文件名/行数/LIID数/ERROR数/接口/时间范围/结论
- 修复记录：根因分析 + 修改文件清单 + commit hash
- 测试结论汇总

**变更日志** (`docs/changelog/`):
- YAML frontmatter (tags/changelog/project/version/date)
- 问题描述
- 根因分析（逐层深入）
- 修改文件清单（含每处改动的说明）
- 验证结果

**经验库** (`~/knowledge/知识/技能/hermes-asn1/`):
- 问题+现象
- 根因（重点）
- 解决方案（可复现的步骤）
- 数据佐证
- 最佳实践（下次如何避免）

### GitHub 推送注意

```bash
cd /tmp/ops-monitoring
git add -A && git commit -m "type: 描述"
HTTPS_PROXY=http://127.0.0.1:7897 git push origin main
```

如果 `git push` 报 `gnutls_handshake() failed`，重试即可（网络波动）。

---

## 三、单元测试

### 创建测试

```bash
mkdir -p src/tests/
```

测试文件: `src/tests/test_all.py` — 每个模块一个 TestClass:

```python
class TestHW14ByteHeader:
    def setup_method(self):
        from asn_decode_api_v4 import parse_hw_14byte_header
        self.parse = parse_hw_14byte_header

    def test_valid_sbc_header(self):
        ...
```

### 运行测试

```bash
cd ~/projects/ETSI-ASN1-Assistant
venv/bin/python3 -m pip install pytest
venv/bin/python3 -m pytest src/tests/test_all.py -v --tb=short
```

### 验证测试覆盖率

每次代码修改后，确保：
- 新增功能有对应测试类
- BugFix 有回归测试（测试截断/错误输入/边界条件）
- 所有测试通过后才能标记完成

---

## 四、真实日志测试清单

每次版本完成后，必须用本地真实文件测试通过：

```bash
# SSF — SIP 信令日志
head -5000 ~/PCAP/.../ssf.1300.txt

# RVF — RTP 媒体日志  
cat ~/PCAP/.../rvf.1420.txt

# ZTLIG1 — X1 管理日志 (注意可能 521MB, 自动截断前5MB)
cat ~/PCAP/.../ztlig1.300.txt

# ZTLIG2 — X2 IRI 日志 (注意 .txt 后缀的文件可能是 gzip 压缩)
cat ~/PCAP/.../ztlig2.461.txt
```

---

## 五、文件命名规则

| 类型 | 命名规则 | 示例 |
|------|---------|------|
| 系统设计文档 | `ETSI_ASN1_Assistant_V{n}_系统设计文档.md/pdf` | `ETSI_ASN1_Assistant_V4_系统设计文档.md` |
| 架构图 | `v{n}_architecture.html/svg/pdf/png` | `v4_architecture.html` |
| 测试报告 | `docs/tests/V{版本}_{功能}_测试报告.md` | `V4_X接口日志分析_测试报告.md` |
| 变更日志 | `docs/changelog/{日期}-fix-{问题}.md` | `2026-06-27-fix-xinterface-sigill.md` |
| 经验库 | `知识/技能/hermes-asn1/{topic}.md` | `x-interface-large-file-handling.md` |
| README | 使用中文命名 `ETSI ASN.1 助手 V{n}` | 非英文的 `ETSI ASN.1 Assistant` |

旧版本文件保留不动，不删除。

---

## 六、文档生成命令

```bash
# 系统设计文档 PDF
pandoc ETSI_ASN1_Assistant_V4_系统设计文档.md -o /tmp/sd_v4.html --standalone
wkhtmltopdf --enable-local-file-access --page-size A4 --margin-top 15 \
  --margin-bottom 15 --margin-left 15 --margin-right 15 \
  /tmp/sd_v4.html ETSI_ASN1_Assistant_V4_系统设计文档.pdf

# 架构图 SVG 从 HTML 提取
python3 -c "
import re
with open('v4_architecture.html') as f:
    content = f.read()
m = re.search(r'<svg[^>]*>.*?</svg>', content, re.DOTALL)
if m:
    svg = '<?xml version=\"1.0\" encoding=\"UTF-8\"?>\\n' + m.group()
    with open('v4_architecture.svg', 'w') as f:
        f.write(svg)
"

# 架构图 PNG
google-chrome --headless --disable-gpu --no-sandbox \
  --screenshot="v4_architecture_a4.png" --window-size=1280,1100 \
  "file://$(pwd)/v4_architecture.html"
```

---

## 七、用户命名与风格偏好

- **README 用中文标题**：`ETSI ASN.1 助手 V4.0`
- **必须包含版本历史表**（V3.0 → V3.1 → V4.0 时间线）
- **解码模式数量必须标注**（如 "12 种解码模式"）
- **文档优先中文**，专业术语保留英文（LIID/CIN/SSF/RVF/ZTLIG）
- **新增功能用 EMOJI 分类**（🔌 📍 📡 📋 🛡️ ⚡ 🔬）
- **架构图用 L1-L5 分层** + V4 扩展模块独立标注

---

## 八、常见 VS Code 问题

| 问题 | 症状 | 修复 |
|------|------|------|
| 终端启动失败 | "终端进程启动失败: 启动目录不存在" | 创建缺失的项目目录即可（空目录也可） |
| Git 推送失败 | `gnutls_handshake() failed` | `git config --global http.proxy http://127.0.0.1:7897` 或重试 |
| Git SSH→HTTPS 冲突 | SSH remote 仍走 HTTPS | 检查 `git config --global url.https://github.com/.insteadof` |
| Settings Sync | VSCode 跨机同步未配置 | Ctrl+Shift+P → "Settings Sync: Turn On" 用 GitHub 登录 |
