# xpan API 全盘扫描百度网盘文件

本文件记录了通过百度开放平台 xpan API 绕过 bypy 限制扫描网盘全盘的技术。

## 背景

bypy 基于百度 PCS API，只能访问 `/apps/bypy/` 子目录。而 xpan API (`pan.baidu.com/rest/2.0/xpan/file`) 使用同一个 access_token，但可以访问**网盘根目录**。

## API 端点

```
GET https://pan.baidu.com/rest/2.0/xpan/file
```

### 必需参数

| 参数 | 值 | 说明 |
|------|-----|------|
| method | list | 列出目录内容 |
| dir | / | 根目录，可替换为任何路径 |
| start | 0 | 起始偏移 |
| limit | 200 | 每页最多200条 |
| web | 1 | 返回缩略图等附加信息 |
| folder | 0 | 返回所有类型 |
| access_token | \<token\> | from ~/.bypy/bypy.json |

### 可选参数

| 参数 | 值 | 说明 |
|------|-----|------|
| order | time/name/size | 排序字段 |
| desc | 1 | 降序 |
| showempty | 1 | 返回 dir_empty 属性 |

## 关键陷阱

### ⚠️ 代理问题（必须处理）

通过 urllib/curl 调用 xpan API 时，HTTP_PROXY/HTTPS_PROXY 环境变量会导致**请求卡死**，因为流量走了 clash 代理(:7897)而百度 API 不需要。

**Python解决方法：**
```python
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
```

**Shell解决方法：**
```bash
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy
```

### ⚠️ Token获取
```python
with open(os.path.expanduser('~/.bypy/bypy.json')) as f:
    token = json.load(f)['access_token']
```
scope 必须含 `netdisk` 权限（bypy 授权时已包含）。

### ⚠️ API限制
- 每200条一页，超过需分页
- 建议两次请求间隔 0.15~0.2s，避免 429
- 根目录约300个目录，全盘递归约600~1800次API调用，耗时3~15分钟

## method=search — 全盘文件搜索

按关键词搜索整个网盘（比逐层 list 目录高效得多）：

```
GET https://pan.baidu.com/rest/2.0/xpan/file
```

| 参数 | 值 | 说明 |
|------|-----|------|
| method | search | 搜索模式 |
| key | 搜索词 | 文件名中包含的关键词 |
| recursion | 1 | 递归搜索所有子目录 |
| limit | 100~200 | 每页返回条数 |
| web | 1 | 返回完整信息 |
| access_token | \<token\> | from ~/.bypy/bypy.json |

**Python 示例：**
```python
params = urllib.parse.urlencode({
    'method': 'search', 'access_token': token,
    'key': '2016', 'recursion': 1, 'limit': 200, 'web': 1
})
url = f'https://pan.baidu.com/rest/2.0/xpan/file?{params}'
req = urllib.request.Request(url, headers={'User-Agent': 'pan.baidu.com'})
with urllib.request.urlopen(req, timeout=20) as resp:
    data = json.loads(resp.read())
```

**关键用法：**
- 搜索年份关键词快速定位历史上的照片——比 BFS 目录扫描快 100 倍
- 搜索宠物名直接找到相关目录
- 搜索返回的 path 字段可直接用于 method=list
- 搜索比 list 更宽松：即使目录名不含关键词，子文件中含关键词也能命中

### 照片搜索与 AI 分类典型场景

快速定位照片 → 下载 → AI 视觉识别 → 自动分类保存：

```python
for year in ['2016', '2017']:
    params = urllib.parse.urlencode({
        'method': 'search', 'access_token': token,
        'key': year, 'recursion': 1, 'limit': 200, 'web': 1
    })
    # 筛选图片文件
    items = [i for i in data['list'] if i.get('server_filename','').lower().endswith(('.jpg','.png','.heic'))]
    # 下载 → HEIC 转换（convert 命令）→ AI 视觉分析 → 按内容分类保存
```

**HEIC 转换：** 百度网盘下载的 HEIC 照片需转为 JPG 才能被 AI 视觉 API 识别：
```bash
convert input.heic output.jpg
```

## 响应字段说明

| 字段 | 类型 | 含义 |
|------|------|------|
| errno | int | 0=成功 |
| list | array | 文件/目录列表 |
| server_filename | string | 文件名 |
| isdir | int | 1=目录 |
| dir_empty | int | 1=空目录 |
| size | int | 文件大小(字节) |
| path | string | 完整路径 |
| fs_id | int | 文件唯一ID |
| category | int | 6=目录, 4=文档 |

## 文件下载

获取 dlink 需要额外 API：

```python
meta_url = 'https://pan.baidu.com/rest/2.0/xpan/multimedia'
params = {'method': 'filemetas', 'fsids': f'[{fs_id}]', 'dlink': 1, 'access_token': token}
# 响应中的 dlink 需要追加 &access_token=token 才能下载
```

## 参考

更详细的分类索引和知识库构建流程见 baidunetdisk 主 SKILL.md。
