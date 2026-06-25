#!/usr/bin/env python3
"""
小红书爆款笔记查询脚本 — 调用红狐 API 获取热门笔记
用法:
  python fetch_xhs_hot_articles.py --keyword "减脂餐" --start-date 2026-06-05
  python fetch_xhs_hot_articles.py --keyword "" --start-date 2026-06-05
  python fetch_xhs_hot_articles.py --keyword "减脂餐,健身" --start-date 2026-06-05 --page-size 50
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta

API_BASE = "https://api.redfoxapi.com"  # 请替换为实际红狐API地址
API_KEY = os.environ.get("REDFOX_API_KEY", "")


def fetch_hot_articles(keyword: str, start_date: str, page_num: int = 1, page_size: int = 10) -> dict:
    """调用红狐 API 查询小红书热门笔记"""
    if not API_KEY:
        return {"error": "REDFOX_API_KEY 未配置，请先设置环境变量"}

    params = {
        "keyword": keyword,
        "start_date": start_date,
        "page_num": page_num,
        "page_size": page_size,
    }

    url = f"{API_BASE}/xhs/hot/articles?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {API_KEY}"})

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.read().decode()}"}
    except Exception as e:
        return {"error": str(e)}


def generate_html_report(articles: list, keyword: str) -> str:
    """自动生成 HTML 可视化报告"""
    filename = f"{keyword if keyword else '全站热门'}_热门数据.html"
    items_html = ""
    for i, a in enumerate(articles[:30]):
        score = a.get("totalScore", a.get("interactionCount", 0))
        items_html += f"""
        <div class="card">
          <div class="num">{i+1}</div>
          <div class="score">{score}</div>
          <div class="info">
            <a href="{a.get('url', '#')}" target="_blank">{a.get('title', '无标题')}</a>
            <div class="meta">
              <span>👤 {a.get('author', '未知')}</span>
              <span>🔥 {a.get('interactionCount', 0)}</span>
              <span>📅 {a.get('publishTime', '')}</span>
            </div>
          </div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{keyword or '全站热门'} - 小红书热门数据</title>
<style>
body{{font-family:system-ui;background:#f5f5f5;margin:0;padding:20px;color:#333}}
h1{{font-size:1.4rem;margin-bottom:8px}}
.sub{{color:#666;font-size:.85rem;margin-bottom:20px}}
.card{{display:flex;gap:12px;background:#fff;border-radius:8px;padding:14px;margin-bottom:10px;align-items:center;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
.num{{width:24px;font-weight:700;color:#999;text-align:center;flex-shrink:0}}
.score{{min-width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#ff2442,#ff6b81);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.8rem;flex-shrink:0;padding:0 4px}}
.info{{flex:1}}
.info a{{color:#333;text-decoration:none;font-weight:500;font-size:.9rem}}
.info a:hover{{color:#ff2442}}
.meta{{display:flex;gap:16px;font-size:.8rem;color:#999;margin-top:4px;flex-wrap:wrap}}
</style>
</head>
<body>
<h1>🔥 {keyword or '全站热门'} — 小红书热门数据</h1>
<p class="sub">共 {len(articles)} 条结果 · 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
{items_html}
</body>
</html>"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    return filename


def main():
    parser = argparse.ArgumentParser(description="小红书爆款笔记查询")
    parser.add_argument("--keyword", default="", help="搜索关键词，多个用逗号分隔")
    parser.add_argument("--start-date", default=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"), help="起始日期 YYYY-MM-DD")
    parser.add_argument("--page-num", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=10)
    args = parser.parse_args()

    result = fetch_hot_articles(args.keyword, args.start_date, args.page_num, args.page_size)

    if "error" in result:
        print(json.dumps({"error": result["error"]}, ensure_ascii=False))
        sys.exit(1)

    articles = result.get("articles", result.get("data", []))
    if articles:
        html_file = generate_html_report(articles, args.keyword)
        result["html_report"] = html_file

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
