---
name: baidunetdisk
category: productivity
description: 百度网盘 Baidu Netdisk - 官方GUI客户端、bypy命令行工具、xpan API全盘访问，以及文档索引生成和Hermes协同
---

# 百度网盘 (Baidu Netdisk) Hermes 集成

本技能覆盖百度网盘官方客户端（GUI）和 bypy 命令行工具的安装、使用及与 Hermes Agent 的协同工作。

## 两种访问方式

### 1. 官方客户端（GUI）- baidunetdisk

- **安装路径**: `~/.local/opt/baidunetdisk/`（免 sudo 安装）
- **启动脚本**: `~/bin/baidunetdisk`（自动添加 `--no-sandbox` 和 `GDK_BACKEND=x11`）
- **桌面文件**: `~/.local/share/applications/baidunetdisk.desktop`
- 需要桌面环境（X11/Wayland）才能显示图形界面
- 默认下载目录：客户端设置中指定

### 2. 命令行工具 - bypy

- **安装路径**: `~/venvs/bypy/`（Python venv）
- **可执行文件**: `~/bin/bypy`（软链接）
- **别名**: `bypy`（在 ~/.bashrc 中配置）
- **授权状态**: 已授权（Token 存储在 `~/.bypy/bypy.json`）
- **限制**: 只能访问 `/apps/bypy/` 目录，**无法看到网盘根目录和其他目录**

### 3. xpan API — 全盘访问（推荐）

bypy 的同一个 access_token 可以用于百度开放平台的 xpan API，**访问整个网盘根目录**：

- **端点**: `https://pan.baidu.com/rest/2.0/xpan/file`
- **参数**: `method=list&dir=/&start=0&limit=200&web=1&folder=0&access_token=<TOKEN>&desc=1`
- **认证**: 使用 `~/.bypy/bypy.json` 中的 `access_token`（scope 需含 `netdisk`）  
- **关键**: 调用时**必须禁用 HTTP_PROXY**！否则通过 clash 代理 (:7897) 会卡死无响应  
- **引用**: 详见 `references/xpan-file-search.md`（快速搜索+下载）| `references/photo-finding-workflow.md`（AI照片识别+知识库入库）| `references/iphone-photo-discovery-pitfalls.md`（iPhone备份照片关键陷阱）

#### bypy 常用命令

| 命令 | 说明 |
|------|------|
| `bypy list` | 列出 /apps/bypy/ 目录下的文件 |
| `bypy quota` | 查看网盘配额（当前 30TB/2.85TB） |
| `bypy upload <本地文件>` | 上传文件到 /apps/bypy/ |
| `bypy download <网盘文件>` | 下载文件到当前目录 |
| `bypy downdir <网盘目录>` | 下载目录到本地 |
| `bypy upload <文件> <远程目录>` | 上传到指定远程目录 |
| `bypy compare` | 比较本地与远程目录差异 |
| `bypy cat <远程文件>` | 查看远程文件内容 |

---

## xpan API 全盘访问（核心工作流）

### 快速文件搜索（按名称）

通过 `method=search` 按文件名搜索整个网盘，无需递归扫描。**这是找照片的第一步**——先搜命名目录，再搜备份：

```python
# 第一步：搜专门的命名目录
for kw in ['丢丢', '宠物', '狗狗', 'dog', 'puppy']:
    params = urllib.parse.urlencode({
        'method': 'search', 'access_token': token,
        'key': kw, 'recursion': 1, 'limit': 100, 'web': 1
    })
    # 检查 isdir=1 → 说明有专门的命名目录，直接下载（无需 AI 验证）

# 第二步：如果命名目录不够，再扫备份目录（需要 AI 验证）
params = urllib.parse.urlencode({
    'method': 'list', 'access_token': token,
    'dir': '/来自：iPhone', 'start': 0, 'limit': 200, 'web': 1
})
```

**用户偏好：** 当照片位于以宠物/人名命名的目录（如 `/2025-丢丢/`）时，**默认都是该目标的照片**，无需逐张 AI 验证。仅对 iPhone 备份等无分类的通用目录需要逐张验证。

### 从命名目录下载文件

找到命名目录后，用 `method=list` 列出内容，再用 `method=filemetas` 获取下载链接：

```python
params = urllib.parse.urlencode({
    'access_token': token, 'fsids': json.dumps([item['fs_id']]),
    'dlink': 1, 'thumb': 0, 'extra': 0
})
meta_url = f'https://pan.baidu.com/rest/2.0/xpan/multimedia?method=filemetas&{params}'
req = urllib.request.Request(meta_url, headers=headers)
with urllib.request.urlopen(req, timeout=20) as resp:
    meta = json.loads(resp.read())

dlink = (meta.get('list') or [{}])[0].get('dlink', '')
# 下载：{dlink}&access_token={token}
```

### 响应字段说明

```python
import urllib.request, urllib.parse, json, os

# ⚠️ 必须禁用代理
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)

with open(os.path.expanduser('~/.bypy/bypy.json')) as f:
    token = json.load(f)['access_token']

params = urllib.parse.urlencode({
    'method': 'list', 'dir': '/', 'start': 0, 'limit': 200,
    'web': 1, 'folder': 0, 'access_token': token, 'desc': 1
})
url = f'https://pan.baidu.com/rest/2.0/xpan/file?{params}'
req = urllib.request.Request(url, headers={'User-Agent': 'pan.baidu.com'})
with urllib.request.urlopen(req, timeout=20) as resp:
    data = json.loads(resp.read())
```

### 响应字段说明

| 字段 | 含义 |
|------|------|
| `server_filename` | 文件名 |
| `isdir` | 1=目录，无此字段或0=文件 |
| `dir_empty` | 1=空目录，0=有内容 |
| `size` | 文件大小（字节） |
| `path` | 完整路径 |
| `fs_id` | 文件唯一 ID |
| `category` | 6=目录；4=文档类 |
| `server_ctime/mtime` | 创建/修改时间戳 |

### 文档索引生成工作流

1. BFS 队列递归扫描所有非空目录（`dir_empty=0`）
2. 每个目录 0.15~0.2s 间隔（限速防 429）
3. 按文件扩展名白名单过滤文档类型：`.ppt .pptx .pdf .doc .docx .xls .xlsx .txt .md .mobi .epub .azw3`
4. 过滤条件：大小 >= 1KB，非 Python 2.7 相关
5. Python 2.7 过滤关键词: `python2, python2.7, py2, py27, "python 2", "python 2.7"`
6. 输出结构化 Markdown 索引到 `~/knowledge/baidu-netdisk-index.md`

**注意**: 全盘递归扫描约 600+ API 调用，耗时 250~400 秒。`time.sleep(0.15)` 可适当调整。

### 文档分类 → 知识库

扫描生成的原始索引可归类到 `~/knowledge/baidu-netdisk/` 知识库：

1. 解析 `~/knowledge/baidu-netdisk-index.md` 中的文档条目
2. 按目录路径关键词 → 文件名关键词双层映射分类
3. 检测同名+同大小的重复文件，标记去重信息
4. 输出 19 个分类 .md 文件 + `_index.md` 总索引
5. 重复处理规则：SAGE 多语言 HTML 自动清除；真实重复保留主条目，副本用 `↳` 引用

**引用**: `references/baidu-doc-index-classifier.md` | `references/baidu-file-download.md` | `references/baidu-doc-download-analysis.md` | `references/xpan-api-full-scan.md` | `references/pdf-to-md-workflow.md` | `references/hw-li-x1-ne-type-table.md` | `references/3gpp-spec-download-and-convert.md`

### 知识库中的技术文档二次使用

解析后的华为 LI 协议 PDF 存储在 `~/knowledge/baidu-netdisk/parsed/`：
- `LI-HW.md` — 华为 CS ETSI 合法监听 X 接口规范 V5.03 (259页, 含第12章 ASN.1 PER 语法)
- `HW_NGN_X1X2.md` — 华为 NGN X1/X2 接口协议 v1.43 (含 C 帧结构和命令码表)
- `NGN_XPTU.md` — NGN XPTU 接口参数规范

可用于回答 HW X1 帧结构、NE type 编码、CS vs IMS X1 差异、X2-X3 关联等问题。

#### Verified Protocol Knowledge Summary

**HW CS ETSI X1 帧头** (14字节定长):
`0xAA` | 协议族(bit7-6, 00=ETSI)+保留(bit5)+版本(bit4-0=5) | NEtype(1字节) | 加密模式(bit7-6)+算法(bit5-0) | 明文长度(2B BigE) | 密文长度(2B BigE) | LEAID(1B) | 保留5B(0xFF) | 数据区

**NE type 编码表** (1字节):
DEC=1 `0x01` MSCserver/MSC | 2 `0x02` HLR | 3 `0x03` SMSC | 4 `0x04` SGSN | 5 `0x05` GGSN | 6 `0x06` GMLC | 31 `0x1F` cMSC | 32 `0x20` cHLR | 34 `0x22` PDSN | 81 `0x51` MSE | 91 `0x5B` NGN | 101 `0x65` P-CSCF | 102 `0x66` I-CSCF | 103 `0x67` S-CSCF | 104 `0x68` HSS | 105 `0x69` CCTF | 106 `0x6A` MGCF | 111 `0x6F` IMS | 121 `0x79` TAS | 123 `0x7B` AGCF | 151 `0x97` SBC

**NGN 老版 X1 帧头** (8字节): `0xAA` | nCmdCode | nLEAID(2B LE) | dwLength(4B) | pData[DES加密]

**CS vs IMS**：X1 帧头完全一致，差异在 X2（CS=12种IRI消息，IMS=1种iMS-Gen-IRI-Report + SIP消息体）和 X3（CS=ISUP/PRA/SIP复制，IMS=RTP复制）。IMS 必须设置 SpeechOutputMode=SplitedOptionA。

**X2/X3 关联**：通过 LIID(谁) + CIN(哪通话) + CCLID(哪条链路) 关联。ISUP子地址承载：Calling Party Subaddress=LIID+Direction, Called Party Subaddress=CIN+CCLID。

**ASN.1 PER**: `X1 DEFINITIONS IMPLICIT TAGS`, 30种 X1MessageType CHOICE, PER ALIGNED, Big-endian。

### 文档转 Markdown（百度网盘 PDF → 知识库）

下载的 PDF 文档可转换为 Markdown 后存入 `~/knowledge/baidu-netdisk/parsed/`：

1. 通过 xpan API 获取 dlink 下载 PDF（见 references/baidu-file-download.md）
2. 安装转换工具：`pip install markitdown[pdf]`（轻量，无需 GPU）
3. 转换命令：`markitdown doc.pdf > doc.md`
4. 3GPP 标准文档（docx/doc 格式）：
   - 从 3GPP FTP 下载 zip：`wget "https://www.3gpp.org/ftp/Specs/archive/33_series/33.108/33108-i00.zip"`
   - 版本标记：`i`=R19, `h`=R18, `g`=R17
   - doc 格式转 docx：`libreoffice --headless --convert-to docx xxx.doc`
   - 转换：`markitdown xxx.docx > xxx.md`
5. ASN.1 格式的技术文档转换效果良好
6. 3GPP 规范的 ASN.1 附件在 zip 包的 attachments zip 中，需单独解压

**引用**: `references/pdf-to-md-workflow.md`

### 文档 → PDF 导出（知识库输出）

将写好的 Markdown 导出为 PDF。**在 Ubuntu 24.04 Wayland 环境下，Chromium snap/wkhtmltopdf/WeasyPrint 都无法正确渲染中文 PDF。唯一可靠方案是：**

```
pandoc report.md -f markdown -t docx -o report.docx
libreoffice --headless --convert-to pdf report.docx
```

详见 `references/md-to-pdf-export-note.md`。

### 文档去重合并（索引侧）

扫描生成的原始索引中 30%~50% 的文件可能是重复的（同文件出现在不同子目录）。重复处理流程：

1. 按 `(文件名小写, 文件大小)` 建立哈希表
2. 对每组 >1 的条目，分类处理：
   - **SAGE/HTML 文档**（如 `py-modindex.html`、`search.html` 等在同一软件不同语言文档子目录中反复出现）→ 整组清理
   - **真正的重复**（相同技术文档在多个目录存放）→ 保留主目录条目，副本用 `↳ 同文件见: 主路径` 替代
3. 分类文件中的重复标记格式：`⚠️ 重复(也在: /其他路径)`
4. 去重后更新每个分类文件的文档计数

### 与 knowledge-base 的关系

`baidunetdisk` 负责网盘侧的扫描/索引/分类；生成的知识库文件（`~/knowledge/baidu-netdisk/`）归入整体知识体系，受 `knowledge-base` 技能的 FTS5 搜索和 Obsidian 图谱管理。

---

## Hermes 协同工作

### 上传文件到百度网盘

```bash
bypy upload /path/to/local/file
```

### 从百度网盘下载文件

#### 方式一：xpan API method=download（推荐，根目录通用）

```python
import urllib.request, urllib.parse, json, os
os.environ.pop('HTTP_PROXY', None); os.environ.pop('HTTPS_PROXY', None)
with open(os.path.expanduser('~/.bypy/bypy.json')) as f:
    token = json.load(f)['access_token']
filepath = '/来自：iPhone/filename.jpg'  # 完整的网盘路径
params = urllib.parse.urlencode({'access_token': token, 'path': filepath})
url = f'https://pan.baidu.com/rest/2.0/xpan/file?method=download&{params}'
req = urllib.request.Request(url, headers={'User-Agent': 'pan.baidu.com'})
with urllib.request.urlopen(req, timeout=30) as resp:
    data = resp.read()
    with open('/tmp/output.jpg', 'wb') as f:
        f.write(data)
```

详见 `references/xpan-file-search.md` 文件下载章节。

#### 方式二：bypy（仅限 /apps/bypy/ 目录）

```bash
bypy download filename
```

### 批量照片扫描 + AI验证 + 知识库入库

完整自动化流程：扫描网盘目录 → 逐张下载 → HEIC转JPG → VL识别 → 保存到知识库并生成索引。

**一键运行脚本：**
```bash
python3 ~/.hermes/skills/productivity/baidunetdisk/scripts/batch-photo-scan.py
```

该脚本将：
1. 列出 `/来自：iPhone/` 目录下所有照片
2. 每张照片下载到临时目录
3. 用 SiliconFlow Qwen3-VL 识别内容（"有狗/无狗"二分类）
4. 匹配的照片自动保存到 `~/knowledge/丢丢/照片/` 并生成 `_index.md` 索引

**配置项（在脚本顶部修改）：**
- `BAIDU_SOURCE_DIR` — 百度网盘扫描目录（默认 `/来自：iPhone`）
- `TARGET_NAME` — 目标名称（默认 `丢丢`）
- `TARGET_DESC` — VL 识别时的描述（默认 `宠物狗`）
- `KNOWLEDGE_DIR` — 知识库根目录（默认 `~/knowledge`）

源码详见 `scripts/batch-photo-scan.py`。

### 照片内容验证工作流

从百度网盘下载照片后，使用 VLM 验证是否为目标宠物/人物。支持两种后端：

| 后端 | 端点 | 时延 | 适用场景 |
|------|------|:----:|----------|
| **SiliconFlow** `Qwen/Qwen3-VL-32B-Instruct` | api.siliconflow.cn | ~500ms | 主力 |
| **阿里百炼** `qwen3-vl-plus` | dashscope.aliyuncs.com/compatible-mode/v1 | ~800-1500ms | SiliconFlow 失败时 fallback |

**调用方式：** Python 脚本直接调 VLM API（见本技能 `references/bailian-vision-alternative.md`）

**用户偏好：** 当照片位于以宠物/人名命名的目录（如 `/2025-丢丢/`）时，默认**都是该目标的照片**，无需逐张 AI 验证。仅对 iPhone 备份等无分类的通用目录需要逐张验证。

详见 `references/photo-verification-heic.md`

### 在技能/脚本中调用

```python
from hermes_tools import terminal
terminal("bypy upload /home/andymao/myfile.zip")
terminal("bypy download important.doc")
```

### 通过 Hermes task 批量处理

1. 先用 xpan API 列出文件 → 2. 筛选文档 → 3. 用 bypy download 下载 → 4. 写入知识库

---

## 故障排除

- **SUID sandbox 错误**: 使用 `--no-sandbox` 参数启动
- **GDK_BACKEND 错误**: 设置 `GDK_BACKEND=x11` 环境变量
- **bypy 授权过期**: 删除 `~/.bypy/bypy.json` 重新运行 `bypy` 授权
- **bypy 使用代理**: 自动读取 HTTP_PROXY/HTTPS_PROXY 环境变量
- **xpan API 无响应/卡死**: 调用前清除代理：`os.environ.pop('HTTP_PROXY', None)`
- **xpan API JSON 解析报错**: 用 `json.loads(raw, strict=False)` 处理非标准转义
- **全盘扫描目录过多**: 294 个根目录 + 深层子目录可达 600+ API 调用，建议限制递归深度或用 BFS 逐步扫描
- **BaiduPCS-Go 锁定文件**: 用 `BaiduPCS-Go quit` 或 `kill` 进程解除配置锁定