# 百度网盘照片 → AI 视觉识别 → 知识库工作流

本文件记录从百度网盘批量查找、下载、AI 识别、自动分类保存照片的完整工作流。

## 典型场景

用户有大量历史照片在百度网盘（如宠物照片），需要自动找到带特定内容（如宠物狗）的照片并保存到本地知识库。

## 搜索策略：名字搜索 → 目录扫描两步法

### 常见错误：直接用宠物名搜索

```
method=search&key=丢丢  ← 只找到 3 个文件
```

原因：bypy token 的 xpan search 作用域有限，且 iPhone 备份的照片以时间戳为文件名（如 `2016-06-12 183504.jpg`），**不会包含宠物名字**。

### 正确策略：两步搜索

**第一步：搜命名目录**（宠物/人物名作目录名的情况）

```python
data = baidu_request({'method':'search', 'key':'丢丢', 'recursion':1, 'limit':100})
for item in data.get('list', []):
    if item.get('isdir') == 1:
        print(f"发现命名目录: {item['path']}")
        # 直接列出该目录，默认全部为目标照片
```

**第二步：按时间范围扫描备份目录**（当命名目录不够时）

```python
data = baidu_request({'method':'list', 'dir':'/来自：iPhone', 'start':0, 'limit':200})
photos = [f for f in data.get('list',[]) if f.get('server_filename','').startswith('201') or f.get('server_filename','').startswith('202')]
# 按年份/月份筛选后逐张下载 + AI 验证
```

### 搜索效率对比

| 方式 | 速度 | 适用场景 |
|------|:----:|----------|
| method=search by name | 快 (~1s) | 找命名目录、找已知文件名 |
| method=list 目录扫描 | 中 (~1s/200条) | 扫描备份目录的所有文件 |
| BFS 递归遍历所有目录 | 慢 (250~400s) | 首次全盘扫描（不推荐做照片搜索） |

## 核心难点

1. **照片分布分散**：iPhone 备份目录 `/来自：iPhone/` 包含多年照片混合存放
2. **格式问题**：iPhone 的 HEIC 格式不能直接用于 AI 视觉 API
3. **批量处理慢**：大量照片需要逐张下载 + AI 识别

## 工作流

### 阶段一：搜索定位

用 xpan API 的 `method=search` 按年份关键词找到所有照片：

```
method=search&key=2016&recursion=1&limit=200
```

这比 BFS 扫描目录快 100 倍。照片通常在 `/来自：iPhone/` 目录中，文件名形如 `2016-07-05 172637.jpg`。

### 阶段二：下载与格式转换

```python
# 下载
dl_params = urllib.parse.urlencode({'access_token': token, 'path': item['path']})
dl_url = f'https://pan.baidu.com/rest/2.0/xpan/file?method=download&{dl_params}'
# HEIC → JPG 转换
convert input.heic output.jpg
```

**注意：** 每次下载前必须禁用代理：
```python
os.environ.pop('HTTP_PROXY', None)
```

### 阶段三：AI 视觉识别

使用 SiliconFlow CN 国内站（直连，不需要代理）的 Qwen-VL 模型：

```python
payload = json.dumps({
    "model": "Qwen/Qwen3-VL-8B-Instruct",
    "messages": [{"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
        {"type": "text", "text": "这张照片里有宠物狗（贵宾犬/泰迪）吗？只用两个字回答：有 或 无"}
    ]}],
    "max_tokens": 10, "temperature": 0.01
})
```

**提示词技巧：** 用二分类提示（"有 或 无"）+ 低 temperature 可获得最准确的分类结果。

### 阶段四：自动保存到知识库

```python
shutil.copy2(local, f"/home/andymao/knowledge/丢丢/照片/{timestamp}_{filename}")
```

同时更新 `_index.md` 索引文件。

## 批量处理模板

完整模板见脚本 `scripts/batch-photo-scan.py`（限速 0.2s/张，HEIC 自动转换，进度显示，后台运行）。

关键参数：
- 建议后台运行（background=true, notify_on_complete=true）
- timeout=600（200 张照片约需 3~5 分钟）
- 输出重定向到日志文件方便追溯
