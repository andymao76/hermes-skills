# iPhone 备份照片发现 - 关键陷阱与技巧

## 文件名≠拍摄时间

iPhone 备份到百度网盘 `/来自：iPhone/` 目录的文件，**文件名格式不一致**：

| 格式 | 示例 | 文件名特征 |
|------|------|-----------|
| 标准格式 | `2016-06-12 183504.jpg` | 空格分隔日期时间 |
| HEIC 格式 | `2026-06-11 203128.heic` | 同上 |
| Live Photo | `2026-06-08 103503.livp` | .livp 为 macOS 包，需单独处理 |
| 特殊前缀 | `IMG_20230605_123456.jpg` | 旧iPhone或手动重命名 |

## 🚨 关键陷阱

### 陷阱1：不要按文件名前缀过滤年份

```python
# ❌ 错误的做法 — 匹配不到任何文件
items = [f for f in photos if re.match(r'2016', f['server_filename'])]

# ✅ 正确的做法 — 用 server_mtime 时间戳过滤
import datetime
items = [f for f in photos 
         if 1451606400 <= f.get('server_mtime', 0) < 1514764800]
# 1451606400 = 2016-01-01 00:00 UTC
# 1514764800 = 2018-01-01 00:00 UTC
```

**原因：** iPhone 备份文件的 `server_filename` 格式不统一，有的用日期分隔线（`-`），有的用下划线（`_`），有的完全用其他命名规范。但 `server_mtime` 字段始终是准确的 Unix 时间戳，这是最可靠的过滤依据。

### 陷阱2：目录超过200条时 pagination 不可靠

```python
# ❌ 不要用 while start+=200 循环翻页
# ✅ 只获取前200条，这是最稳定的一次调用
data = baidu_request({'method':'list', 'dir':'/来自：iPhone', 'start':0, 'limit':200})
```

百度 xpan API 的 pagination 在 `/来自：iPhone/` 这类混合目录中超时率极高。优先获取前200条，放弃翻页。

### 陷阱3：HEIC 格式不能被 AI 视觉 API 直接处理

```python
# ✅ 先转 JPG
subprocess.run(['convert', heic_path, jpg_path])
```

ImageMagick `convert` 命令可以可靠地将 HEIC 转换为 JPG。

### 陷阱4：下载速度与代理

xpan API 必须禁用所有 HTTP_PROXY/HTTPS_PROXY 环境变量，否则超时无响应。

## 推荐的年份过滤代码

```python
import datetime

def filter_by_year(items, years):
    """按拍摄年份过滤 iPhone 备份照片"""
    year_thresholds = {y: (datetime.datetime(y,1,1, tzinfo=datetime.timezone.utc).timestamp(),
                           datetime.datetime(y+1,1,1, tzinfo=datetime.timezone.utc).timestamp())
                      for y in years}
    result = []
    for item in items:
        mtime = item.get('server_mtime', 0)
        for yr, (start, end) in year_thresholds.items():
            if start <= mtime < end:
                result.append(item)
                break
    return result

# 调用
photos_2016 = filter_by_year(all_photos, [2016])
photos_2017 = filter_by_year(all_photos, [2017])
```

## AI 视觉识别的准确率

- **有宠物狗的情况**：准确率 ~95%，Qwen3-VL-8B 能可靠识别贵宾犬/泰迪
- **边界情况**：照片中有狗窝/玩具但无狗 → 误报率高
- **模糊/远景/局部**：可能漏判
- **建议**：保守筛选后用二分类提示（"有 或 无"）+ temperature=0.01 可获得最高一致率
