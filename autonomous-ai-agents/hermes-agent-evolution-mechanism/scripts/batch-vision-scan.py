#!/usr/bin/env python3
"""批量图片视觉扫描模板
用法: python3 batch-vision-scan.py <图片目录> [模型名]
功能: 遍历目录图片，用AI视觉模型逐张识别，输出结果JSON

依赖: pip install requests pyyaml
"""

import json, base64, os, sys, glob, time, yaml

# === CONFIG ===
TARGET_DESC = "贵宾犬/泰迪犬（叫丢丢）"
PROMPT_TEMPLATE = '这张照片里有{TARGET}吗？回答"是"或"否"，并简单描述。'
OUTPUT_FILE = "scan_results.json"
API_TIMEOUT = 45
BATCH_DELAY = 0.3  # 秒，防限流

# === PROVIDER SELECTION ===
PROVIDERS = {
    "bailian": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen3-vl-plus",
        "key_source": "env:DASHSCOPE_API_KEY",
        "key_fallback": "env_file:~/.hermes/.env",
    },
    "siliconflow": {
        "base_url": "https://api.siliconflow.cn/v1",
        "default_model": "Qwen/Qwen3-VL-32B-Instruct",
        "key_source": "yaml:~/.hermes/config.yaml:providers.siliconflow-cn.api_key",
    },
}

def load_api_key(source):
    """从env/yaml/env_file加载API key"""
    if source.startswith("env:"):
        return os.environ.get(source[4:], "")
    elif source.startswith("env_file:"):
        path = os.path.expanduser(source[9:])
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    k = line.strip()
                    if k.startswith(source.split(":")[-1].split("=")[0]):
                        parts = k.split("=", 1)
                        if len(parts) == 2:
                            return parts[1].strip("'\" ")
    elif source.startswith("yaml:"):
        parts = source[5:].split(":", 2)
        yaml_path, key_path = os.path.expanduser(parts[0]), parts[1].split(".")
        with open(yaml_path) as f:
            cfg = yaml.safe_load(f)
            val = cfg
            for k in key_path:
                val = val.get(k, "")
                if not val:
                    break
            return val
    return ""

def analyze_image(img_path, api_key, base_url, model):
    """单张图片分析"""
    with open(img_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    
    prompt = PROMPT_TEMPLATE.format(TARGET=TARGET_DESC)
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
        ]}],
        "max_tokens": 100,
        "temperature": 0.01,
    }
    
    import requests
    r = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=API_TIMEOUT)
    result = r.json()
    if "choices" in result:
        return result["choices"][0]["message"]["content"]
    return json.dumps(result)

def main():
    if len(sys.argv) < 2:
        print("用法: python3 batch-vision-scan.py <图片目录> [provider]")
        sys.exit(1)
    
    img_dir = sys.argv[1]
    provider_name = sys.argv[2] if len(sys.argv) > 2 else "bailian"
    
    if provider_name not in PROVIDERS:
        print(f"不支持的provider: {provider_name}，可用: {list(PROVIDERS.keys())}")
        sys.exit(1)
    
    provider = PROVIDERS[provider_name]
    api_key = load_api_key(provider["key_source"])
    if not api_key:
        api_key = load_api_key(provider.get("key_fallback", ""))
    
    if not api_key:
        print("无法加载API key，请检查配置")
        sys.exit(1)
    
    model = provider["default_model"]
    img_exts = ("*.jpg", "*.jpeg", "*.png", "*.gif", "*.bmp")
    photos = []
    for ext in img_exts:
        photos.extend(glob.glob(os.path.join(img_dir, ext)))
    photos = sorted(set(photos))
    
    print(f"Provider: {provider_name} / Model: {model}")
    print(f"图片数: {len(photos)}")
    
    results = {}
    results_file = os.path.join(os.path.dirname(img_dir.rstrip("/")), OUTPUT_FILE)
    
    # 加载已有结果（断点续扫）
    if os.path.exists(results_file):
        with open(results_file) as f:
            results = json.load(f)
        print(f"已有缓存结果: {len(results)}张")
    
    found = []
    for i, p in enumerate(photos):
        fname = os.path.basename(p)
        if fname in results:
            continue
        
        try:
            desc = analyze_image(p, api_key, provider["base_url"], model)
        except Exception as e:
            desc = f"ERROR: {e}"
        
        results[fname] = desc
        is_target = any(k in desc[:2] for k in ["是", "有"])
        icon = "✅" if is_target else "❌"
        print(f"{i+1}/{len(photos)} {icon} {fname}: {desc[:60]}")
        
        if is_target:
            found.append({"file": p, "desc": desc})
        
        # 每张保存一次缓存
        with open(results_file, "w") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        time.sleep(BATCH_DELAY)
    
    print(f"\n=== 完成 ===")
    print(f"扫描: {len(photos)}张 | 命中: {len(found)}张")
    for f in found:
        print(f"  🎯 {f['file']}: {f['desc'][:80]}")

if __name__ == "__main__":
    main()
