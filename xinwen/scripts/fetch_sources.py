#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻情报中心 - 数据抓取层
30+信源并发抓取，5大分类覆盖
"""

import json
import re
import time
import hashlib
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import OrderedDict

import requests
from bs4 import BeautifulSoup

# 统一时区
CST = timezone(timedelta(hours=8))

# 通用请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;'
              'q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# 请求超时
TIMEOUT = 15


def _now_str():
    """返回当前时间字符串"""
    return datetime.now(CST).strftime('%Y-%m-%d %H:%M')


def _make_item(title, source, category, url='', hot=0, extra=None):
    """构造标准化新闻条目"""
    item = {
        'id': hashlib.md5(f"{source}:{title}".encode('utf-8')).hexdigest()[:12],
        'title': title.strip(),
        'source': source,
        'category': category,
        'url': url,
        'hot': hot,
        'timestamp': _now_str(),
        'extra': extra or {},
    }
    return item


# ========== 全球科技 ==========

def fetch_hacker_news():
    """Hacker News - Algolia API（免费无需Key）"""
    items = []
    try:
        url = 'http://hn.algolia.com/api/v1/search_by_date'
        params = {
            'tags': 'story',
            'hitsPerPage': 30,
            'numericFilter': 'points>50',
        }
        resp = requests.get(url, params=params, timeout=TIMEOUT)
        data = resp.json()
        for hit in data.get('hits', []):
            title = hit.get('title', '')
            if not title:
                continue
            points = hit.get('points', 0) or 0
            obj_id = hit.get('objectID', '')
            items.append(_make_item(
                title=title,
                source='Hacker News',
                category='全球科技',
                url=f'https://news.ycombinator.com/item?id={obj_id}',
                hot=points,
                extra={'comment_count': hit.get('num_comments', 0) or 0},
            ))
    except Exception as e:
        print(f"[抓取异常] Hacker News: {e}")
    return items


def fetch_product_hunt():
    """Product Hunt - 爬取首页热门"""
    items = []
    try:
        url = 'https://www.producthunt.com/'
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # 尝试从页面提取产品名称
        for tag in soup.select('[data-test="post-name"]'):
            title = tag.get_text(strip=True)
            if title:
                items.append(_make_item(
                    title=title,
                    source='Product Hunt',
                    category='全球科技',
                    hot=50,
                ))
        # 备用：从JSON-LD提取
        if not items:
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    ld = json.loads(script.string)
                    if isinstance(ld, list):
                        for entry in ld:
                            name = entry.get('name', '')
                            if name:
                                items.append(_make_item(
                                    title=name,
                                    source='Product Hunt',
                                    category='全球科技',
                                    url=entry.get('url', ''),
                                    hot=40,
                                ))
                except Exception:
                    pass
    except Exception as e:
        print(f"[抓取异常] Product Hunt: {e}")
    return items


def fetch_techcrunch():
    """TechCrunch - RSS"""
    items = []
    try:
        url = 'https://techcrunch.com/feed/'
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        soup = BeautifulSoup(resp.text, 'xml')
        for item_tag in soup.find_all('item')[:20]:
            title_tag = item_tag.find('title')
            link_tag = item_tag.find('link')
            if title_tag:
                items.append(_make_item(
                    title=title_tag.get_text(strip=True),
                    source='TechCrunch',
                    category='全球科技',
                    url=link_tag.get_text(strip=True) if link_tag else '',
                    hot=30,
                ))
    except Exception as e:
        print(f"[抓取异常] TechCrunch: {e}")
    return items


def fetch_the_verge():
    """The Verge - RSS"""
    items = []
    try:
        url = 'https://www.theverge.com/rss/index.xml'
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        soup = BeautifulSoup(resp.text, 'xml')
        for item_tag in soup.find_all('entry')[:15]:
            title_tag = item_tag.find('title')
            link_tag = item_tag.find('link')
            if title_tag:
                href = link_tag.get('href', '') if link_tag else ''
                items.append(_make_item(
                    title=title_tag.get_text(strip=True),
                    source='The Verge',
                    category='全球科技',
                    url=href,
                    hot=25,
                ))
    except Exception as e:
        print(f"[抓取异常] The Verge: {e}")
    return items


def fetch_ars_technica():
    """Ars Technica - RSS"""
    items = []
    try:
        url = 'https://feeds.arstechnica.com/arstechnica/index'
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        soup = BeautifulSoup(resp.text, 'xml')
        for item_tag in soup.find_all('item')[:15]:
            title_tag = item_tag.find('title')
            link_tag = item_tag.find('link')
            if title_tag:
                items.append(_make_item(
                    title=title_tag.get_text(strip=True),
                    source='Ars Technica',
                    category='全球科技',
                    url=link_tag.get_text(strip=True) if link_tag else '',
                    hot=20,
                ))
    except Exception as e:
        print(f"[抓取异常] Ars Technica: {e}")
    return items


# ========== 开源社区 ==========

def fetch_github_trending():
    """GitHub Trending - 公开API"""
    items = []
    try:
        # 使用搜索API获取近期热门仓库
        url = 'https://api.github.com/search/repositories'
        since = (datetime.now(CST) - timedelta(days=3)).strftime('%Y-%m-%d')
        params = {
            'q': f'created:>{since}',
            'sort': 'stars',
            'order': 'desc',
            'per_page': 25,
        }
        resp = requests.get(url, params=params, timeout=TIMEOUT,
                            headers={'Accept': 'application/vnd.github.v3+json'})
        data = resp.json()
        for repo in data.get('items', []):
            name = repo.get('full_name', '')
            desc = repo.get('description', '') or ''
            title = f"{name}: {desc}" if desc else name
            items.append(_make_item(
                title=title[:120],
                source='GitHub Trending',
                category='开源社区',
                url=repo.get('html_url', ''),
                hot=repo.get('stargazers_count', 0),
                extra={
                    'stars': repo.get('stargazers_count', 0),
                    'language': repo.get('language', ''),
                },
            ))
    except Exception as e:
        print(f"[抓取异常] GitHub Trending: {e}")
    return items


def fetch_v2ex():
    """V2EX - API"""
    items = []
    try:
        url = 'https://www.v2ex.com/api/topics/hot.json'
        resp = requests.get(url, timeout=TIMEOUT)
        data = resp.json()
        for topic in data[:20]:
            title = topic.get('title', '')
            if not title:
                continue
            items.append(_make_item(
                title=title,
                source='V2EX',
                category='开源社区',
                url=topic.get('url', ''),
                hot=topic.get('replies', 0),
                extra={'node': topic.get('node', {}).get('name', '')},
            ))
    except Exception as e:
        print(f"[抓取异常] V2EX: {e}")
    return items


def fetch_github_trending_scrape():
    """GitHub Trending - 网页爬取（备用）"""
    items = []
    try:
        url = 'https://github.com/trending'
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        soup = BeautifulSoup(resp.text, 'html.parser')
        for article in soup.select('article.Box-row')[:25]:
            h2 = article.select_one('h2 a')
            if not h2:
                continue
            name = '/'.join(part.strip() for part in h2.get_text().split('/'))
            desc_tag = article.select_one('p')
            desc = desc_tag.get_text(strip=True) if desc_tag else ''
            title = f"{name}: {desc}" if desc else name
            star_tag = article.select_one('a.Link--muted.d-inline-block.mr-3')
            stars = 0
            if star_tag:
                star_text = star_tag.get_text(strip=True).replace(',', '')
                try:
                    stars = int(star_text)
                except ValueError:
                    pass
            items.append(_make_item(
                title=title[:120],
                source='GitHub Trending',
                category='开源社区',
                url=f'https://github.com/{name}',
                hot=stars,
                extra={'stars': stars},
            ))
    except Exception as e:
        print(f"[抓取异常] GitHub Trending(爬取): {e}")
    return items


def fetch_hacker_news_show():
    """Hacker News Show HN"""
    items = []
    try:
        url = 'http://hn.algolia.com/api/v1/search_by_date'
        params = {
            'tags': 'story',
            'query': 'Show HN',
            'hitsPerPage': 15,
            'numericFilter': 'points>30',
        }
        resp = requests.get(url, params=params, timeout=TIMEOUT)
        data = resp.json()
        for hit in data.get('hits', []):
            title = hit.get('title', '')
            if not title or 'Show HN' not in title:
                continue
            points = hit.get('points', 0) or 0
            obj_id = hit.get('objectID', '')
            items.append(_make_item(
                title=title,
                source='HN Show',
                category='开源社区',
                url=f'https://news.ycombinator.com/item?id={obj_id}',
                hot=points,
            ))
    except Exception as e:
        print(f"[抓取异常] HN Show: {e}")
    return items


# ========== 国内资讯 ==========

def fetch_36kr():
    """36氪 - 热榜爬取"""
    items = []
    try:
        url = 'https://36kr.com/hot-list/catalog'
        headers = {**HEADERS, 'Referer': 'https://36kr.com/hot-list/catalog'}
        resp = requests.get(url, headers=headers, timeout=TIMEOUT)
        # 36氪可能返回HTML而非JSON，需兼容处理
        content_type = resp.headers.get('Content-Type', '')
        if 'json' in content_type or resp.text.strip().startswith('{'):
            data = resp.json()
        else:
            # 从HTML页面中提取数据
            data = {}
        # 解析热榜数据
        catalog_list = data.get('data', {}).get('catalog', [])
        if isinstance(catalog_list, list):
            for entry in catalog_list:
                if isinstance(entry, dict):
                    for item in entry.get('items', []):
                        title = item.get('title', '') or item.get('widget_title', '')
                        if not title:
                            continue
                        items.append(_make_item(
                            title=title.strip(),
                            source='36氪',
                            category='国内资讯',
                            url=f"https://36kr.com/p/{item.get('id', '')}",
                            hot=item.get('views_count', 0) or 0,
                            extra={'views': item.get('views_count', 0)},
                        ))
        # 备用：尝试直接爬取36氪首页
        if not items:
            url2 = 'https://36kr.com/'
            resp2 = requests.get(url2, headers=headers, timeout=TIMEOUT)
            soup = BeautifulSoup(resp2.text, 'html.parser')
            for a_tag in soup.select('a.article-item-title')[:20]:
                title = a_tag.get_text(strip=True)
                href = a_tag.get('href', '')
                if title:
                    items.append(_make_item(
                        title=title,
                        source='36氪',
                        category='国内资讯',
                        url=href if href.startswith('http') else f'https://36kr.com{href}',
                        hot=15,
                    ))
            # 再试其他选择器
            if not items:
                for a_tag in soup.select('.hot-list-item a')[:15]:
                    title = a_tag.get_text(strip=True)
                    if title and len(title) > 5:
                        items.append(_make_item(
                            title=title,
                            source='36氪',
                            category='国内资讯',
                            hot=15,
                        ))
    except Exception as e:
        print(f"[抓取异常] 36氪: {e}")
    return items


def fetch_weibo_hot():
    """微博热搜"""
    items = []
    try:
        url = 'https://weibo.com/ajax/side/hotSearch'
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        data = resp.json()
        realtime = data.get('data', {}).get('realtime', [])
        for entry in realtime[:25]:
            title = entry.get('note', '') or entry.get('word', '')
            if not title:
                continue
            hot_num = entry.get('num', 0) or 0
            items.append(_make_item(
                title=title.strip(),
                source='微博热搜',
                category='国内资讯',
                url=f"https://s.weibo.com/weibo?q=%23{title.strip()}%23",
                hot=hot_num,
                extra={'label': entry.get('label_name', '')},
            ))
    except Exception as e:
        print(f"[抓取异常] 微博热搜: {e}")
    return items


def fetch_ithome():
    """IT之家 - 热榜爬取"""
    items = []
    try:
        url = 'https://www.ithome.com/'
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # 尝试从首页新闻列表提取
        for block in soup.select('.lst > li')[:25]:
            a_tag = block.select_one('a')
            title_tag = block.select_one('.title') or block.select_one('a')
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            href = a_tag.get('href', '') if a_tag else ''
            if title:
                items.append(_make_item(
                    title=title,
                    source='IT之家',
                    category='国内资讯',
                    url=href,
                    hot=20,
                ))
        # 备用选择器
        if not items:
            for a_tag in soup.select('a.title')[:20]:
                title = a_tag.get_text(strip=True)
                href = a_tag.get('href', '')
                if title:
                    items.append(_make_item(
                        title=title,
                        source='IT之家',
                        category='国内资讯',
                        url=href,
                        hot=20,
                    ))
    except Exception as e:
        print(f"[抓取异常] IT之家: {e}")
    return items


def fetch_tencent_tech():
    """腾讯科技 - 新闻页面爬取"""
    items = []
    try:
        url = 'https://news.qq.com/rain/a/20240101V01YJG'
        # 尝试腾讯新闻科技频道
        url2 = 'https://new.qq.com/tag/415'
        resp = requests.get(url2, headers=HEADERS, timeout=TIMEOUT)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # 从页面提取新闻标题
        for a_tag in soup.select('.result-list .detail a')[:20]:
            title = a_tag.get_text(strip=True)
            href = a_tag.get('href', '')
            if title:
                items.append(_make_item(
                    title=title,
                    source='腾讯科技',
                    category='国内资讯',
                    url=href,
                    hot=15,
                ))
        # 备用选择器
        if not items:
            for a_tag in soup.select('a[data-chlist]')[:15]:
                title = a_tag.get_text(strip=True)
                if title and len(title) > 5:
                    items.append(_make_item(
                        title=title,
                        source='腾讯科技',
                        category='国内资讯',
                        hot=15,
                    ))
    except Exception as e:
        print(f"[抓取异常] 腾讯科技: {e}")
    return items


def fetch_zhihu_hot():
    """知乎热榜"""
    items = []
    try:
        url = 'https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total'
        params = {'limit': 25, 'desktop': 'true'}
        headers = {**HEADERS, 'Referer': 'https://www.zhihu.com/hot'}
        resp = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
        data = resp.json()
        for entry in data.get('data', []):
            target = entry.get('target', {})
            title = target.get('title', '')
            if not title:
                continue
            hot_num = entry.get('detail_text', '')
            try:
                hot_val = int(re.sub(r'\D', '', hot_num))
            except (ValueError, TypeError):
                hot_val = 0
            items.append(_make_item(
                title=title.strip(),
                source='知乎热榜',
                category='国内资讯',
                url=f"https://www.zhihu.com/question/{target.get('id', '')}",
                hot=hot_val,
            ))
    except Exception as e:
        print(f"[抓取异常] 知乎热榜: {e}")
    return items


def fetch_bilibili_hot():
    """B站热门"""
    items = []
    try:
        url = 'https://api.bilibili.com/x/web-interface/ranking/v2'
        params = {'rid': 0, 'type': 'all'}
        resp = requests.get(url, headers=HEADERS, params=params, timeout=TIMEOUT)
        data = resp.json()
        for video in data.get('data', {}).get('list', [])[:20]:
            title = video.get('title', '')
            if not title:
                continue
            # 去除HTML标签
            title = re.sub(r'<[^>]+>', '', title)
            items.append(_make_item(
                title=title.strip(),
                source='B站热门',
                category='国内资讯',
                url=video.get('short_link_v2', '') or f"https://www.bilibili.com/video/{video.get('bvid', '')}",
                hot=video.get('stat', {}).get('view', 0),
                extra={'owner': video.get('owner', {}).get('name', '')},
            ))
    except Exception as e:
        print(f"[抓取异常] B站热门: {e}")
    return items


# ========== 金融财经 ==========

def fetch_eastmoney():
    """东方财富 - 公开API"""
    items = []
    try:
        url = 'https://np-listapi.eastmoney.com/comm/web/getNewsByColumns'
        params = {
            'client': 'web',
            'biz': 'web_news_col',
            'column': '350',
            'order': '1',
            'needInteractData': '0',
            'page_index': '1',
            'page_size': '20',
        }
        resp = requests.get(url, params=params, timeout=TIMEOUT,
                            headers=HEADERS)
        data = resp.json()
        news_list = []
        # 尝试多种数据路径
        for path in ['data.newsList', 'data.list', 'data']:
            obj = data
            for key in path.split('.'):
                if isinstance(obj, dict):
                    obj = obj.get(key)
                    if obj is None:
                        obj = {}
                        break
                else:
                    obj = {}
                    break
            if isinstance(obj, list) and obj:
                news_list = obj
                break
        for entry in news_list:
            if not isinstance(entry, dict):
                continue
            title = entry.get('title', '')
            if not title:
                continue
            items.append(_make_item(
                title=title.strip(),
                source='东方财富',
                category='金融财经',
                url=entry.get('url', '') or entry.get('newsUrl', ''),
                hot=entry.get('readCount', 0) or entry.get('commentCount', 0) or 0,
            ))
        # 备用：尝试东方财富7x24快讯
        if not items:
            url2 = 'https://np-listapi.eastmoney.com/comm/web/getFastNewsList'
            params2 = {
                'client': 'web',
                'biz': 'web_fast',
                'fastColumn': '102',
                'sortEnd': '',
                'pageSize': '20',
            }
            resp2 = requests.get(url2, params=params2, timeout=TIMEOUT,
                                 headers=HEADERS)
            data2 = resp2.json()
            data2_obj = data2.get('data') or {}
            for entry in data2_obj.get('fastNewsList', []):
                if not isinstance(entry, dict):
                    continue
                title = entry.get('title', '') or entry.get('content', '')
                if not title:
                    continue
                title = re.sub(r'<[^>]+>', '', title).strip()
                if title:
                    items.append(_make_item(
                        title=title[:80],
                        source='东方财富',
                        category='金融财经',
                        hot=15,
                    ))
    except Exception as e:
        print(f"[抓取异常] 东方财富: {e}")
    return items


def fetch_xueqiu():
    """雪球热帖"""
    items = []
    try:
        url = 'https://xueqiu.com/query/v1/square/hot_post_list.json'
        params = {
            'size': 20,
            'sort': 'hot',
        }
        headers = {**HEADERS, 'Referer': 'https://xueqiu.com/'}
        # 先获取cookie
        session = requests.Session()
        session.get('https://xueqiu.com/', headers=headers, timeout=TIMEOUT)
        resp = session.get(url, params=params, headers=headers, timeout=TIMEOUT)
        data = resp.json()
        for post in data.get('list', [])[:20]:
            title = post.get('title', '') or post.get('text', '')[:60]
            if not title:
                continue
            title = re.sub(r'<[^>]+>', '', title).strip()
            items.append(_make_item(
                title=title[:80],
                source='雪球',
                category='金融财经',
                url=f"https://xueqiu.com/{post.get('user', {}).get('id_str', '')}/{post.get('id', '')}",
                hot=post.get('reply_count', 0) or post.get('retweet_count', 0) or 0,
            ))
    except Exception as e:
        print(f"[抓取异常] 雪球: {e}")
    return items


def fetch_wallstreet_cn():
    """华尔街见闻 - 快讯（尝试，可能被CF保护）"""
    items = []
    try:
        url = 'https://wallstreetcn.com/api/finfo/v2/live-list'
        params = {'channel': 'global-channel', 'cursor': '', 'limit': 20}
        resp = requests.get(url, headers=HEADERS, params=params, timeout=TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get('data', {}).get('items', []):
                title = item.get('title', '') or item.get('content_text', '')
                if not title:
                    continue
                title = re.sub(r'<[^>]+>', '', title).strip()
                if title:
                    items.append(_make_item(
                        title=title[:80],
                        source='华尔街见闻',
                        category='金融财经',
                        url=item.get('uri', ''),
                        hot=item.get('vote_count', 0) or 0,
                    ))
    except Exception as e:
        print(f"[抓取异常] 华尔街见闻: {e}")
    return items


def fetch_cls_telegraph():
    """财联社电报"""
    items = []
    try:
        url = 'https://www.cls.cn/api/sw'
        params = {
            'app': 'CailianpressWeb',
            'os': 'web',
            'sv': '7.7.5',
        }
        resp = requests.get(url, headers=HEADERS, params=params, timeout=TIMEOUT)
        # 尝试滚动新闻接口
        url2 = 'https://www.cls.cn/depth/1000'
        resp2 = requests.get(url2, headers=HEADERS, timeout=TIMEOUT)
        soup = BeautifulSoup(resp2.text, 'html.parser')
        for a_tag in soup.select('.depth-item a')[:15]:
            title = a_tag.get_text(strip=True)
            if title and len(title) > 5:
                items.append(_make_item(
                    title=title,
                    source='财联社',
                    category='金融财经',
                    url=a_tag.get('href', ''),
                    hot=15,
                ))
    except Exception as e:
        print(f"[抓取异常] 财联社: {e}")
    return items


# ========== AI深度 ==========

def fetch_huggingface_papers():
    """HuggingFace Papers - RSS"""
    items = []
    try:
        url = 'https://huggingface.co/papers/rss'
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        soup = BeautifulSoup(resp.text, 'xml')
        for item_tag in soup.find_all('item')[:20]:
            title_tag = item_tag.find('title')
            link_tag = item_tag.find('link')
            if title_tag:
                title = title_tag.get_text(strip=True)
                link = link_tag.get_text(strip=True) if link_tag else ''
                # 提取arxiv id
                arxiv_id = ''
                if 'arxiv' in link.lower():
                    match = re.search(r'(\d{4}\.\d{4,5})', link)
                    if match:
                        arxiv_id = match.group(1)
                items.append(_make_item(
                    title=title,
                    source='HuggingFace Papers',
                    category='AI深度',
                    url=link,
                    hot=30,
                    extra={'arxiv_id': arxiv_id},
                ))
    except Exception as e:
        print(f"[抓取异常] HuggingFace Papers: {e}")
    return items


def fetch_arxiv_ai():
    """ArXiv AI分类 - RSS"""
    items = []
    try:
        url = 'http://export.arxiv.org/api/query'
        params = {
            'search_query': 'cat:cs.AI OR cat:cs.CL OR cat:cs.LG',
            'start': 0,
            'max_results': 20,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending',
        }
        resp = requests.get(url, params=params, timeout=TIMEOUT)
        soup = BeautifulSoup(resp.text, 'xml')
        for entry in soup.find_all('entry')[:20]:
            title_tag = entry.find('title')
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True).replace('\n', ' ')
            link_tag = entry.find('id')
            link = link_tag.get_text(strip=True) if link_tag else ''
            # 提取摘要前60字
            summary_tag = entry.find('summary')
            summary = ''
            if summary_tag:
                summary = summary_tag.get_text(strip=True)[:60]
            items.append(_make_item(
                title=title[:100],
                source='ArXiv AI',
                category='AI深度',
                url=link,
                hot=20,
                extra={'summary': summary},
            ))
    except Exception as e:
        print(f"[抓取异常] ArXiv AI: {e}")
    return items


# AI Newsletters RSS源
AI_NEWSLETTER_RSS = {
    'One Useful Thing': 'https://www.oneusefulthing.org/feed',
    'Interconnects': 'https://www.interconnects.ai/feed',
    'KDnuggets': 'https://www.kdnuggets.com/feed',
    'Memia': 'https://memia.substack.com/feed',
    'AI to ROI': 'https://aitoroi.substack.com/feed',
    'ChinAI': 'https://chinai.substack.com/feed',
    'The Batch (Andrew Ng)': 'https://www.deeplearning.ai/the-batch/feed/',
    'Import AI': 'https://importai.substack.com/feed',
}


def _fetch_rss_feed(source_name, rss_url, category='AI深度', hot_val=15):
    """通用RSS抓取函数"""
    items = []
    try:
        resp = requests.get(rss_url, headers=HEADERS, timeout=TIMEOUT)
        soup = BeautifulSoup(resp.text, 'xml')
        # RSS 2.0
        for item_tag in soup.find_all('item')[:5]:
            title_tag = item_tag.find('title')
            link_tag = item_tag.find('link')
            if title_tag:
                title = title_tag.get_text(strip=True)
                link = ''
                if link_tag:
                    link = link_tag.get_text(strip=True)
                items.append(_make_item(
                    title=title,
                    source=source_name,
                    category=category,
                    url=link,
                    hot=hot_val,
                ))
        # Atom
        if not items:
            for entry in soup.find_all('entry')[:5]:
                title_tag = entry.find('title')
                link_tag = entry.find('link')
                if title_tag:
                    title = title_tag.get_text(strip=True)
                    href = ''
                    if link_tag:
                        href = link_tag.get('href', '') or link_tag.get_text(strip=True)
                    items.append(_make_item(
                        title=title,
                        source=source_name,
                        category=category,
                        url=href,
                        hot=hot_val,
                    ))
    except Exception as e:
        print(f"[抓取异常] {source_name}: {e}")
    return items


def fetch_ai_newsletters():
    """并发抓取所有AI Newsletter RSS源"""
    all_items = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {}
        for name, url in AI_NEWSLETTER_RSS.items():
            f = executor.submit(_fetch_rss_feed, name, url)
            futures[f] = name
        for f in as_completed(futures):
            all_items.extend(f.result())
    return all_items


# ========== 汇总 ==========

# 所有抓取函数列表
ALL_FETCHERS = [
    # 全球科技
    fetch_hacker_news,
    fetch_product_hunt,
    fetch_techcrunch,
    fetch_the_verge,
    fetch_ars_technica,
    # 开源社区
    fetch_github_trending,
    fetch_github_trending_scrape,
    fetch_v2ex,
    fetch_hacker_news_show,
    # 国内资讯
    fetch_36kr,
    fetch_weibo_hot,
    fetch_ithome,
    fetch_tencent_tech,
    fetch_zhihu_hot,
    fetch_bilibili_hot,
    # 金融财经
    fetch_eastmoney,
    fetch_xueqiu,
    fetch_wallstreet_cn,
    fetch_cls_telegraph,
    # AI深度
    fetch_huggingface_papers,
    fetch_arxiv_ai,
    fetch_ai_newsletters,
]


def fetch_all(max_workers=8, topic_filter=None):
    """
    并发抓取所有信源
    
    参数:
        max_workers: 并发线程数
        topic_filter: 可选分类过滤 ('全球科技'/'开源社区'/'国内资讯'/'金融财经'/'AI深度')
    
    返回:
        list[dict]: 标准化新闻条目列表
    """
    fetchers = ALL_FETCHERS
    if topic_filter:
        # 根据分类筛选抓取函数
        category_map = {
            '全球科技': [fetch_hacker_news, fetch_product_hunt, fetch_techcrunch,
                       fetch_the_verge, fetch_ars_technica],
            '开源社区': [fetch_github_trending, fetch_github_trending_scrape,
                       fetch_v2ex, fetch_hacker_news_show],
            '国内资讯': [fetch_36kr, fetch_weibo_hot, fetch_ithome,
                       fetch_tencent_tech, fetch_zhihu_hot, fetch_bilibili_hot],
            '金融财经': [fetch_eastmoney, fetch_xueqiu, fetch_wallstreet_cn,
                       fetch_cls_telegraph],
            'AI深度': [fetch_huggingface_papers, fetch_arxiv_ai,
                      fetch_ai_newsletters],
        }
        fetchers = category_map.get(topic_filter, ALL_FETCHERS)

    all_items = []
    start = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fn): fn.__name__ for fn in fetchers}
        for future in as_completed(futures):
            fn_name = futures[future]
            try:
                items = future.result()
                all_items.extend(items)
                print(f"  ✓ {fn_name}: {len(items)} 条")
            except Exception as e:
                print(f"  ✗ {fn_name}: {e}")
    
    elapsed = time.time() - start
    print(f"\n抓取完成：共 {len(all_items)} 条，耗时 {elapsed:.1f}s")
    return all_items


# 支持命令行直接运行
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='新闻情报中心 - 数据抓取')
    parser.add_argument('--topic', type=str, default=None,
                        help='分类过滤：全球科技/开源社区/国内资讯/金融财经/AI深度')
    args = parser.parse_args()
    
    items = fetch_all(topic_filter=args.topic)
    print(json.dumps(items, ensure_ascii=False, indent=2))
