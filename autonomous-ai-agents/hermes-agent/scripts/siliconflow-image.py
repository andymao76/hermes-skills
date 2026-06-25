#!/usr/bin/env python3
"""
SiliconFlow 图片生成脚本
通过 SiliconFlow 国际站 API 生成图片并保存到本地。

用法:
  python3 siliconflow-image.py "一只可爱的猫" -m "black-forest-labs/FLUX.1-schnell" -o ~/images/output.png

可选模型:
  - black-forest-labs/FLUX.1-schnell  (快速, 默认)
  - black-forest-labs/FLUX.1-dev       (高质量)
  - black-forest-labs/FLUX-1.1-pro     (专业版)
  - black-forest-labs/FLUX.2-pro       (最新专业版)
  - black-forest-labs/FLUX.2-flex      (灵活版)
"""

import os
import sys
import json
import argparse
import urllib.request
from pathlib import Path

# SiliconFlow 配置
API_BASE = "https://api.siliconflow.com/v1"
API_KEY = os.environ.get("SILICONFLOW_API_KEY", "sk-ybhkgohjakcyogfcskzankpguugamzinawfvgualuhqpetvn")

# 代理配置（国际站需要代理）
PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or "http://127.0.0.1:7897"

AVAILABLE_MODELS = {
    "schnell": "black-forest-labs/FLUX.1-schnell",
    "dev": "black-forest-labs/FLUX.1-dev",
    "pro": "black-forest-labs/FLUX-1.1-pro",
    "pro-ultra": "black-forest-labs/FLUX-1.1-pro-Ultra",
    "pro2": "black-forest-labs/FLUX.2-pro",
    "flex": "black-forest-labs/FLUX.2-flex",
    "kontext-pro": "black-forest-labs/FLUX.1-Kontext-pro",
    "kontext-max": "black-forest-labs/FLUX.1-Kontext-max",
    "kontext-dev": "black-forest-labs/FLUX.1-Kontext-dev",
}


def generate_image(prompt, model="black-forest-labs/FLUX.1-schnell", size="1024x1024", n=1):
    """调用 SiliconFlow 图片生成 API"""
    url = f"{API_BASE}/images/generations"
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "n": n,
        "size": size,
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {API_KEY}")

    proxy_handler = urllib.request.ProxyHandler({
        "http": PROXY,
        "https": PROXY,
    })
    opener = urllib.request.build_opener(proxy_handler)

    try:
        resp = opener.open(req, timeout=120)
        result = json.loads(resp.read().decode("utf-8"))
        return result
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {"error": f"HTTP {e.code}: {body}"}
    except Exception as e:
        return {"error": str(e)}


def download_image(url, output_path):
    """下载图片到本地"""
    proxy_handler = urllib.request.ProxyHandler({
        "http": PROXY,
        "https": PROXY,
    })
    opener = urllib.request.build_opener(proxy_handler)

    try:
        resp = opener.open(url, timeout=60)
        data = resp.read()
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(data)
        return True
    except Exception as e:
        print(f"下载失败: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="SiliconFlow 图片生成")
    parser.add_argument("prompt", nargs="?", help="图片描述提示词")
    parser.add_argument("-m", "--model", default="black-forest-labs/FLUX.1-schnell",
                        choices=list(AVAILABLE_MODELS.values()),
                        help="模型名称（默认: FLUX.1-schnell）")
    parser.add_argument("-o", "--output", default="",
                        help="输出路径（默认: ~/图片/siliconflow_时间戳.png）")
    parser.add_argument("-s", "--size", default="1024x1024",
                        choices=["1024x1024", "768x1024", "1024x768"],
                        help="图片尺寸（默认: 1024x1024）")
    parser.add_argument("-n", "--count", type=int, default=1, choices=[1, 2, 3, 4],
                        help="生成数量（默认: 1）")
    parser.add_argument("--list-models", action="store_true",
                        help="列出可用模型")

    args = parser.parse_args()

    if args.list_models:
        print("可用模型:")
        for key, model in AVAILABLE_MODELS.items():
            print(f"  {key:12s} → {model}")
        return

    if not args.prompt:
        args.prompt = input("请输入图片描述: ").strip()
        if not args.prompt:
            print("描述不能为空")
            sys.exit(1)
        model_keys = list(AVAILABLE_MODELS.keys())
        print("\n可选模型:")
        for i, key in enumerate(model_keys):
            print(f"  {i+1}. {key} → {AVAILABLE_MODELS[key]}")
        try:
            choice = int(input(f"\n选择模型 [1-{len(model_keys)}, 默认1]: ") or "1") - 1
            args.model = AVAILABLE_MODELS[model_keys[choice]]
        except (ValueError, IndexError):
            args.model = AVAILABLE_MODELS["schnell"]

    print(f"🎨 正在生成图片...")
    print(f"   模型: {args.model}")
    print(f"   提示: {args.prompt[:80]}{'...' if len(args.prompt)>80 else ''}")

    result = generate_image(args.prompt, args.model, args.size, args.count)

    if "error" in result:
        print(f"❌ 生成失败: {result['error']}")
        sys.exit(1)

    images = result.get("images", [])
    if not images:
        print("❌ 返回结果中没有图片数据")
        print(json.dumps(result, indent=2)[:500])
        sys.exit(1)

    print(f"✅ 成功生成 {len(images)} 张图片")

    for i, img in enumerate(images):
        url = img["url"]
        if args.output:
            output_path = args.output.replace("{n}", str(i+1))
        else:
            from datetime import datetime
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path.home() / "图片"
            output_path = str(output_dir / f"siliconflow_{ts}_{i+1}.png")

        print(f"  📥 正在下载第 {i+1} 张...")
        if download_image(url, output_path):
            abs_path = os.path.abspath(output_path)
            print(f"  ✅ 已保存: {abs_path}")
        else:
            print(f"  ⚠️  下载失败，URL: {url}")


if __name__ == "__main__":
    main()
