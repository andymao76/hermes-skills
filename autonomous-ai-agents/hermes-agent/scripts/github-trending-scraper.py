#!/usr/bin/env python3
"""
Template: GitHub Trending 日报 — 每日抓取 github.com/trending 前 N 个项目。

用法:
  1. 保存到 ~/.hermes/scripts/ 目录
  2. 创建 cron job:
     cronjob(action='create', name='GitHub Trending 日报',
             script='github-trending-scraper.py', no_agent=True,
             schedule='0 9 * * *', deliver='weixin')
  3. 修改 deliver 为目标平台 (weixin, telegram, origin 等)

注意: 本脚本使用 urllib（无外部依赖），兼容 Hermes venv。
可根据需要修改 LIMIT 控制抓取数量、修改输出格式。
"""

import json
import urllib.request
import re
import html
from datetime import datetime, timezone, timedelta

# ===== 可配置参数 =====
LIMIT = 5                        # 抓取前 N 个项目
LANGUAGE = ""                     # 语言过滤: "python", "go", "" 表示全部
TIME_RANGE = "daily"              # daily | weekly | monthly
CACHE_ENABLED = True              # 缓存当日数据，避免重复抓取
# =====================

CST = timezone(timedelta(hours=8))
CACHE_PATH = __file__.replace(".py", "-cache.json")


def fetch_trending():
    """抓取 GitHub Trending 页面并解析项目列表"""
    url = f"https://github.com/trending/{LANGUAGE}?since={TIME_RANGE}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; HermesBot/1.0)",
        "Accept": "text/html",
    })

    with urllib.request.urlopen(req, timeout=15) as resp:
        html_content = resp.read().decode("utf-8", errors="replace")

    # 解析每个项目卡片
    articles = re.split(r'<article\s+class="Box-row[^"]*"[^>]*>', html_content)[1:]
    repos = []

    for article in articles[:LIMIT]:
        repo_match = re.search(r'href="/([^/"]+/[^/"]+)"', article)
        if not repo_match:
            continue

        full_name = repo_match.group(1)

        desc_match = re.search(
            r'<p\s+class="col-9[^"]*color-fg-muted[^"]*"[^>]*>\s*(.*?)\s*</p>',
            article, re.DOTALL
        )
        description = html.unescape(re.sub(r'<[^>]+>', '', desc_match.group(1))).strip() if desc_match else "暂无描述"

        lang_match = re.search(
            r'<span[^>]*itemprop="programmingLanguage"[^>]*>([^<]+)</span>', article
        )
        language = lang_match.group(1).strip() if lang_match else "N/A"

        stars_today_match = re.search(
            r'class="octicon[^"]*star[^"]*"[^>]*>.*?</svg>\s*([\d,]+)\s*(?:today)?',
            article, re.DOTALL
        )
        stars_today = stars_today_match.group(1).replace(",", "") if stars_today_match else "0"

        stars_match = re.search(
            r'class="octicon[^"]*star[^"]*"[^>]*>.*?</svg>\s*([\d,]+)\s*',
            article, re.DOTALL
        )
        stars = stars_match.group(1).replace(",", "") if stars_match else "0"

        forks_match = re.search(
            r'class="octicon[^"]*repo-forked[^"]*"[^>]*>.*?</svg>\s*([\d,]+)',
            article, re.DOTALL
        )
        forks = forks_match.group(1).replace(",", "") if forks_match else "0"

        repos.append({
            "name": full_name,
            "url": f"https://github.com/{full_name}",
            "description": description,
            "language": language,
            "stars": stars,
            "stars_today": stars_today,
            "forks": forks,
        })

    return repos


def format_summary(repos):
    """将项目列表格式化为中文日报文本"""
    today = datetime.now(CST).strftime("%Y-%m-%d")
    lines = [
        f"「GitHub {TIME_RANGE.title()} Trending 日报」{today}",
        "━━━━━━━━━━━━━━━━━━━━━",
    ]

    for i, repo in enumerate(repos, 1):
        lines.extend([
            "",
            f"【{i}】{repo['name']}",
            f"  📝 {repo['description']}",
            f"  🔤 {repo['language']}  ⭐ {repo['stars']} (+{repo['stars_today']})  🍴 {repo['forks']}",
            f"  🔗 {repo['url']}",
        ])

    lines.extend([
        "",
        "━━━━━━━━━━━━━━━━━━━━━",
        "数据来源: github.com/trending",
    ])
    return "\n".join(lines)


def main():
    # 检查缓存
    if CACHE_ENABLED:
        try:
            with open(CACHE_PATH) as f:
                cache = json.load(f)
            today = datetime.now(CST).strftime("%Y-%m-%d")
            if cache.get("date") == today and cache.get("repos"):
                print(format_summary(cache["repos"]))
                return
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    # 抓取
    repos = fetch_trending()

    # 缓存
    if CACHE_ENABLED:
        today = datetime.now(CST).strftime("%Y-%m-%d")
        try:
            with open(CACHE_PATH, "w") as f:
                json.dump({"date": today, "repos": repos}, f)
        except Exception:
            pass

    print(format_summary(repos))


if __name__ == "__main__":
    main()
