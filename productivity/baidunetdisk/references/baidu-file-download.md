# 百度网盘 PDF 文档下载到本地

通过 xpan API 获取文件下载链接（dlink），然后下载到本地。

## 获取文件列表和 fs_id

```python
import os, json, urllib.request, urllib.parse
os.environ.pop('HTTP_PROXY', None); os.environ.pop('HTTPS_PROXY', None)

with open(os.path.expanduser('~/.bypy/bypy.json')) as f:
    token = json.load(f)['access_token']

def list_dir(path):
    params = urllib.parse.urlencode({
        'method': 'list', 'dir': path, 'start': 0, 'limit': 200,
        'web': 1, 'folder': 0, 'access_token': token, 'desc': 1
    })
    req = urllib.request.Request(
        f'https://pan.baidu.com/rest/2.0/xpan/file?{params}',
        headers={'User-Agent': 'pan.baidu.com'})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read())

data = list_dir('/LI-STAND')
for item in data.get('list', []):
    if item.get('isdir') != 1:
        print(f"{item['server_filename']}  fs_id={item['fs_id']}  {item.get('size',0)}字节")
```

## 获取下载链接 (dlink) 并下载

```python
def download_file(fs_id, save_path):
    # 1. 获取 dlink
    params = urllib.parse.urlencode({
        'method': 'filemetas', 'fsids': f'[{fs_id}]', 'dlink': 1, 'access_token': token
    })
    meta_url = f'https://pan.baidu.com/rest/2.0/xpan/multimedia?{params}'
    req = urllib.request.Request(meta_url, headers={'User-Agent': 'pan.baidu.com'})
    with urllib.request.urlopen(req, timeout=20) as resp:
        meta = json.loads(resp.read())
    
    dlink = meta['list'][0]['dlink']
    
    # 2. dlink 需要加 access_token 参数才可下载
    dl_req = urllib.request.Request(
        f"{dlink}&access_token={token}",
        headers={'User-Agent': 'pan.baidu.com'})
    with urllib.request.urlopen(dl_req, timeout=120) as dl_resp:
        with open(save_path, 'wb') as f:
            f.write(dl_resp.read())
    print(f"下载完成: {save_path}")
```

## 注意事项

1. **禁用 HTTP_PROXY**: 必须 `os.environ.pop('HTTP_PROXY', None)`，否则卡死无响应
2. **dlink 时效性**: 获取后尽快下载（通常有效 1-2 小时）
3. **Token 时效**: access_token 有效期 30 天（`expires_in: 2592000`），过期后自动 refresh_token 续期
4. **大文件下载**: 可能超时，调大 timeout 参数（建议 120s+）
5. **下载限速**: 百度网盘免费账号下载限速约 100-200KB/s 大文件需考虑此限制

## 下载后处理

下载的 PDF 建议立即用 markitdown 转换为 MD 并存入知识库：
```bash
markitdown doc.pdf > ~/knowledge/baidu-netdisk/parsed/文档名.md
```

如果 PDF 是扫描件（无文本层），markitdown 无法提取文本，需改用 OCR 工具（如 ocrmypdf + tesseract）。华为 LI 文档有文本层，markitdown 可直接提取。
