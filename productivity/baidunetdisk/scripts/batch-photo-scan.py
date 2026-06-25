#!/usr/bin/env python3
"""Batch photo scanner: 百度网盘 → 下载 → HEIC转换 → AI验证 → 知识库入库
Source dir: /来自：iPhone/
Target: 宠物狗/丢丢
"""
import urllib.request, urllib.parse, json, os, base64, yaml, subprocess
import datetime, shutil, sys, re, glob, time

# === CONFIG ===
BAIDU_TOKEN_FILE = os.path.expanduser('~/.bypy/bypy.json')
SILICONFLOW_API = 'https://api.siliconflow.cn/v1/chat/completions'
SILICONFLOW_MODEL = 'Qwen/Qwen3-VL-8B-Instruct'
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.expanduser('~/.hermes/config.yaml')
BAIDU_SOURCE_DIR = '/来自：iPhone'
TARGET_NAME = '丢丢'
TARGET_DESC = '宠物狗（贵宾犬/泰迪）'
KNOWLEDGE_DIR = os.path.expanduser('~/knowledge')
PROXY_FREE = True

os.environ.pop('HTTP_PROXY', None); os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None); os.environ.pop('https_proxy', None)

def get_token():
    with open(BAIDU_TOKEN_FILE) as f:
        return json.load(f)['access_token']

def get_sf_key():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)['providers']['siliconflow-cn']['api_key'].strip()

def baidu_request(params):
    params['access_token'] = get_token()
    qs = urllib.parse.urlencode(params)
    req = urllib.request.Request(
        f'https://pan.baidu.com/rest/2.0/xpan/file?{qs}',
        headers={'User-Agent': 'pan.baidu.com'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())

def download_file(item):
    params = urllib.parse.urlencode({'access_token': get_token(), 'path': item['path']})
    url = f'https://pan.baidu.com/rest/2.0/xpan/file?method=download&{params}'
    req = urllib.request.Request(url, headers={'User-Agent': 'pan.baidu.com'})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()

def analyze_image(img_data, sf_key):
    b64 = base64.b64encode(img_data).decode("utf-8")
    payload = json.dumps({"model": SILICONFLOW_MODEL, "messages": [{"role":"user","content":[
        {"type":"image_url","image_url":{"url":"data:image/jpeg;base64,"+b64}},
        {"type":"text","text":f"这张照片里有{TARGET_DESC}吗？只用两个字回答：有 或 无"}
    ]}], "max_tokens":10, "temperature":0.01})
    jf = "/tmp/_bat_scan.json"
    with open(jf,"w") as f: f.write(payload)
    r = subprocess.run(["curl","-s","--max-time","20", SILICONFLOW_API,
        "-H", f"Authorization: Bearer ***     "-H","Content-Type: application/json","-d","@"+jf],
        capture_output=True, text=True, timeout=25)
    os.unlink(jf)
    if r.stdout:
        try:
            rd = json.loads(r.stdout)
            if 'choices' in rd:
                return rd['choices'][0]['message']['content'].strip()[:5]
        except: pass
    return None

def main():
    sf_key = get_sf_key()
    out_dir = f"/tmp/baidu_scan_{TARGET_NAME}"
    kb_dir = os.path.join(KNOWLEDGE_DIR, TARGET_NAME, '照片')
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(kb_dir, exist_ok=True)

    # 1. List source directory
    print(f"📁 Scanning: {BAIDU_SOURCE_DIR}")
    data = baidu_request({'method':'list','dir':BAIDU_SOURCE_DIR,'start':0,'limit':200,'web':1,'folder':0,'desc':1})
    all_items = data.get('list', [])
    img_exts = ('.jpg','.jpeg','.png','.heic','.gif')
    photos = [f for f in all_items if os.path.splitext(f.get('server_filename',''))[1].lower() in img_exts]
    print(f"   Found {len(photos)} photos\n")

    # 2. Process each
    found = 0; scanned = 0; errors = 0
    for i, item in enumerate(photos):
        name = item['server_filename'].replace(' ','_')
        fsize = item['size']
        if fsize < 100*1024:  # skip tiny files
            continue
        scanned += 1
        
        # Download
        try:
            img = download_file(item)
        except:
            errors += 1; continue
        
        local = os.path.join(out_dir, name)
        with open(local,'wb') as f: f.write(img)
        
        # HEIC convert
        if local.lower().endswith('.heic'):
            conv = local + '.jpg'
            r = subprocess.run(['convert', local, conv], capture_output=True, text=True, timeout=30)
            if r.returncode != 0: continue
            local = conv
        
        # Analyze
        try:
            with open(local,"rb") as f: result = analyze_image(f.read(), sf_key)
        except:
            continue
        
        mt = datetime.datetime.fromtimestamp(item.get('server_mtime',0))
        ts = mt.strftime('%Y-%m-%d')
        sz = f"{fsize/1024:.0f}KB" if fsize<1024*1024 else f"{fsize/1024/1024:.1f}MB"
        
        if result and '有' in result:
            found += 1
            kb_path = os.path.join(kb_dir, f"{ts}_{name.replace('.heic','.jpg')}")
            shutil.copy2(local, kb_path)
            print(f"[{i+1}] 🐕 {item['server_filename'][:40]} ({sz}) -> KB ✅")
        sys.stdout.flush()
        
        # Rate limit
        time.sleep(0.15)
    
    # 3. Index
    all_saved = sorted(glob.glob(os.path.join(kb_dir, "*.jpg")) + glob.glob(os.path.join(kb_dir, "*.png")))
    idx = os.path.join(kb_dir, "_index.md")
    with open(idx, "w") as f:
        f.write(f"# {TARGET_NAME}照片索引\n\n来源: 百度网盘 {BAIDU_SOURCE_DIR} | 更新: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n共 {len(all_saved)} 张\n\n| 文件 | 大小 |\n|------|------|\n")
        for p in all_saved:
            sz = f"{os.path.getsize(p)//1024}KB"
            f.write(f"| {os.path.basename(p)} | {sz} |\n")
    
    print(f"\n{'='*50}")
    print(f"📊 完成: 扫描{scanned}张 | 🐕 {TARGET_NAME}: {found}张 | 知识库: {kb_dir} ({len(all_saved)}张)")

if __name__ == '__main__':
    main()
