# xpan API 文件搜索工作流

通过百度网盘 xpan API 的 `method=search` 按文件名搜索整个网盘，快速定位特定文件/照片。

## 搜索 API

### 基本搜索

```python
import urllib.request, urllib.parse, json, os

os.environ.pop('HTTP_PROXY', None)  # ⚠️ 必须禁用代理
os.environ.pop('HTTPS_PROXY', None)

with open(os.path.expanduser('~/.bypy/bypy.json')) as f:
    token = json.load(f)['access_token']

params = urllib.parse.urlencode({
    'method': 'search',
    'access_token': token,
    'key': '搜索关键词',
    'recursion': 1,   # 递归搜索子目录
    'limit': 100,      # 每页结果数
    'web': 1
})
url = f'https://pan.baidu.com/rest/2.0/xpan/file?{params}'
req = urllib.request.Request(url, headers={'User-Agent': 'pan.baidu.com'})
with urllib.request.urlopen(req, timeout=20) as resp:
    data = json.loads(resp.read())
```

### 响应解析

```python
if data.get('errno') == 0:
    items = data.get('list', [])
    for i in items:
        isdir = '📁' if i.get('isdir') == 1 else '📄'
        name = i['server_filename']
        path = i.get('path', '?')
        mtime = datetime.datetime.fromtimestamp(i.get('server_mtime', 0))
        size = i.get('size', 0)
        print(f"{isdir} [{mtime}] {name} ({size} bytes) path={path}")
```

### 搜索要点

- `key` 参数支持中文文件名搜索
- `recursion=1` 递归搜索所有子目录
- `limit` 最大 100，搜索结果超过需要分页（通过 `start` 参数）
- `isdir=1` 表示目录，`isdir=0/无` 表示文件
- 搜索的是 **整个网盘**（不限于 /apps/bypy/），需要 access_token 有 `netdisk` scope

## 按目录结构查找照片

当文件名不包含搜索关键词时，可按目录结构查找：

1. **列出根目录**：`method=list&dir=/&start=0&limit=200&folder=0&web=1`
2. **找到照片目录**：常见的目录名如 `iphone照片`、`来自：iPhone`、`来自：KB2000` 等
3. **查看目录内容**：`method=list&dir=/来自：iPhone&start=0&limit=200`
4. **分页获取全部**：当 `list` 返回 200 条时，递增 `start` 参数继续获取

### 完整分页示例

```python
def list_all(path, label):
    all_items = []
    start = 0
    while True:
        params = urllib.parse.urlencode({
            'method': 'list', 'access_token': token,
            'dir': path, 'start': start, 'limit': 200,
            'web': 1, 'folder': 0, 'desc': 1
        })
        url = f'https://pan.baidu.com/rest/2.0/xpan/file?{params}'
        req = urllib.request.Request(url, headers={'User-Agent': 'pan.baidu.com'})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
        if data.get('errno') != 0:
            break
        batch = data.get('list', [])
        all_items.extend(batch)
        if len(batch) < 200:
            break
        start += 200
    return all_items
```

## 照片类型识别

iPhone 备份目录 `/来自：iPhone/` 中的照片按时间戳命名：

| 后缀 | 类型 | 说明 |
|------|------|------|
| `.jpg` / `.jpeg` | 普通照片 | 可直接查看 |
| `.heic` | HEIC 格式 | iPhone 高效率格式 |
| `.livp` | 实况照片 | iPhone Live Photo 包 |
| `.mov` / `.mp4` | 视频 | iPhone 录制视频 |
| `.png` | 截图/PNG | 截屏或导出图片 |

按修改时间筛选近期照片：
```python
import datetime
recent = [f for f in files if 
    datetime.datetime.fromtimestamp(f['server_mtime']).year >= 2026]
```

## HEIC 格式处理

iPhone 备份中的 `.heic` 格式照片无法直接被 VLM 分析，需用 ImageMagick 转换：

```bash
convert /path/to/photo.heic /path/to/photo.jpg
```

也支持批量转换：
```bash
for f in *.heic; do convert "$f" "${f%.heic}.jpg"; done
```

转换后即可使用 SiliconFlow VLM 或 vision_analyze 分析内容。

## 照片内容验证（VLM 过滤）

从网盘批量下载照片后，用 SiliconFlow Qwen3-VL 逐一验证内容是否为目标宠物/人物。详见 `references/photo-verification-heic.md`。

## 文件下载（已验证可靠的方式）

### 方式一：method=download（推荐，已验证可用）

`method=download` 直接返回文件内容（HTTP 200），无需获取 dlink 再跳转：

```python
import urllib.request, urllib.parse, json, os

os.environ.pop('HTTP_PROXY', None)   # ⚠️ 禁用代理
os.environ.pop('HTTPS_PROXY', None)

with open(os.path.expanduser('~/.bypy/bypy.json')) as f:
    token = json.load(f)['access_token']

filepath = '/来自：iPhone/2026-06-11 190655.jpg'  # 完整路径
params = urllib.parse.urlencode({
    'access_token': token,
    'path': filepath
})
url = f'https://pan.baidu.com/rest/2.0/xpan/file?method=download&{params}'
req = urllib.request.Request(url, headers={'User-Agent': 'pan.baidu.com'})
with urllib.request.urlopen(req, timeout=30) as resp:
    img_data = resp.read()
    with open('/tmp/downloaded.jpg', 'wb') as f:
        f.write(img_data)
```

- ⚠️ `method=download` 阻塞式读取完整个文件，大文件注意内存
- 响应头含 `Content-Disposition: attachment;filename="..."`、`Content-Length`、`Content-MD5`
- **已验证可下载根目录文件**（不限于 /apps/bypy/）

### 方式二：filemetas + dlink（可能返回 errno=2）

```python
params = urllib.parse.urlencode({
    'method': 'filemetas',
    'access_token': token,
    'targets': json.dumps([{'path': '/path/to/file'}]),  # 或改用 fs_ids
    'dlink': 1,
    'web': 1
})
```

**已知问题**：`method=filemetas` 使用 `targets`（path 方式）或 `fs_ids`（fs_id 方式）都可能在部分 token 上返回 `errno=2`。可能是 bypy token scope 对 xpan 文件元数据 API 的权限不足。如果 filemetas 不通，**直接改用 method=download**。

### 缩略图预览

列表 API 响应含 `thumbs.icon` 字段，可直接在浏览器中打开预览（8小时有效）。
