#!/usr/bin/env python3
"""
Template: GitHub 热门新项目日报 — 通过 GitHub Search API 获取数据。

适用于 network-restricted 环境（Trending 页面超时时），或需要更稳定数据源时。
此脚本无外部依赖（只用 urllib 标准库），兼容 Hermes venv。
特点: 网络连通性预检 + 3次重试 + 缓存 + topics 展示。

用法:
  1. 保存到 ~/.hermes/scripts/ 目录
  2. 修改可配置参数（LIMIT, MIN_STARS, LOOKBACK_DAYS, CACHE_ENABLED）
  3. 创建 cron job:
     cronjob(action='create', name='GitHub 热门新项目日报',
             script='github-search-api-trending.py', no_agent=True,
             schedule='0 9 * * *', deliver='weixin/telegram/origin')
"""

import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta

# ===== 可配置参数 =====
LIMIT = 5                          # 展示前 N 个项目
MIN_STARS = 50                     # 最低 star 数过滤
LOOKBACK_DAYS = 2                  # 搜索最近 N 天内创建的项目
CACHE_ENABLED = True               # 缓存当日数据
# =====================

CST = timezone(timedelta(hours=8))
CACHE_PATH = __file__.replace(".py", "-cache.json")


def fetch_top_repos():
    """通过 GitHub Search API 获取近期创建的热门项目"""
    two_days_ago = (datetime.now(CST) - timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%d")
    query = f"created:>={two_days_ago} stars:>{MIN_STARS}"
    url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(query)}&sort=stars&order=desc&per_page={LIMIT * 2}"

    req = urllib.request.Request(url, headers={
        "User-Agent": "HermesBot/1.0",
        "Accept": "application/vnd.github+json",
    })

    # 网络连通性预检
    import socket, time
    try:
        socket.create_connection(("api.github.com", 443), timeout=5)
    except OSError as e:
        print(f"❌ 无法连接到 api.github.com: {e}")
        exit(1)

    # 3次重试应对瞬时网络故障
    data = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                break
        except Exception as e:
            if attempt < 2:
                time.sleep(3)
                continue
            print(f"❌ GitHub API 请求失败 (已重试3次): {e}")
            exit(1)

    repos = []
    for item in data.get("items", [])[:LIMIT]:
        repos.append({
            "name": item["full_name"],
            "url": item["html_url"],
            "description": item.get("description") or "暂无描述",
            "language": item.get("language") or "N/A",
            "stars": str(item["stargazers_count"]),
            "forks": str(item["forks_count"]),
            "topics": item.get("topics", []),
        })
    return repos


def format_summary(repos):
    """格式化为中文日报"""
    today = datetime.now(CST).strftime("%Y-%m-%d")
    lines = [
        f"📅 GitHub 热门新项目日报 — {today}",
        "━━━━━━━━━━━━━━━━━━━━━",
        "💡 数据来源: GitHub Search API (近{}天创建)".format(LOOKBACK_DAYS),
    ]

    for i, repo in enumerate(repos, 1):
        topic_tags = " ".join(f"#{t}" for t in repo["topics"][:3]) if repo["topics"] else ""
        lines.extend([
            "",
            f"【{i}】{repo['name']}",
            f"📝 {repo['description']}",
            f"🔤 {repo['language']}  ⭐ {repo['stars']}  🍴 {repo['forks']}",
        ])
        if topic_tags:
            lines.append(f"🏷️  {topic_tags}")
        lines.append(f"🔗 {repo['url']}")

    lines.extend([
        "",
        "━━━━━━━━━━━━━━━━━━━━━",
        f"📊 生成时间: {datetime.now(CST).strftime('%Y-%m-%d %H:%M')}",
    ])
    return "\n".join(lines)


def main():
    today = datetime.now(CST).strftime("%Y-%m-%d")

    # 检查缓存
    if CACHE_ENABLED:
        try:
            with open(CACHE_PATH) as f:
                cache = json.load(f)
            if cache.get("date") == today and cache.get("repos"):
                print(format_summary(cache["repos"]))
                return
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    # 抓取
    repos = fetch_top_repos()

    # 缓存
    if CACHE_ENABLED:
        try:
            with open(CACHE_PATH, "w") as f:
                json.dump({"date": today, "repos": repos}, f)
        except Exception:
            pass

    print(format_summary(repos))


if __name__ == "__main__":
    main()
