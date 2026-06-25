# 信源配置

## 全球科技

| 信源 | 抓取方式 | URL/API |
|------|----------|---------|
| Hacker News | Algolia API | http://hn.algolia.com/api/v1/search_by_date |
| Product Hunt | 网页爬取 | https://www.producthunt.com/ |
| TechCrunch | RSS | https://techcrunch.com/feed/ |
| The Verge | RSS (Atom) | https://www.theverge.com/rss/index.xml |
| Ars Technica | RSS | https://feeds.arstechnica.com/arstechnica/index |

## 开源社区

| 信源 | 抓取方式 | URL/API |
|------|----------|---------|
| GitHub Trending | 公开API | https://api.github.com/search/repositories |
| GitHub Trending(备用) | 网页爬取 | https://github.com/trending |
| HN Show HN | Algolia API | http://hn.algolia.com/api/v1/search_by_date?query=Show+HN |
| V2EX | 官方API | https://www.v2ex.com/api/topics/hot.json |

## 国内资讯

| 信源 | 抓取方式 | URL/API |
|------|----------|---------|
| 36氪 | API | https://36kr.com/hot-list/catalog |
| 微博热搜 | Ajax API | https://weibo.com/ajax/side/hotSearch |
| IT之家 | 网页爬取 | https://www.ithome.com/ |
| 腾讯科技 | 网页爬取 | https://new.qq.com/tag/415 |
| 知乎热榜 | API | https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total |
| B站热门 | API | https://api.bilibili.com/x/web-interface/ranking/v2 |

## 金融财经

| 信源 | 抓取方式 | URL/API |
|------|----------|---------|
| 东方财富 | 公开API | https://np-listapi.eastmoney.com/comm/web/getNewsByColumns |
| 雪球热帖 | API | https://xueqiu.com/query/v1/square/hot_post_list.json |
| 华尔街见闻 | API（可能被CF保护） | https://wallstreetcn.com/api/finfo/v2/live-list |
| 财联社 | 网页爬取 | https://www.cls.cn/depth/1000 |

## AI深度

| 信源 | 抓取方式 | URL/API |
|------|----------|---------|
| HuggingFace Papers | RSS | https://huggingface.co/papers/rss |
| ArXiv AI分类 | API | http://export.arxiv.org/api/query |
| One Useful Thing | RSS | https://www.oneusefulthing.org/feed |
| Interconnects | RSS | https://www.interconnects.ai/feed |
| KDnuggets | RSS | https://www.kdnuggets.com/feed |
| Memia | RSS | https://memia.substack.com/feed |
| AI to ROI | RSS | https://aitoroi.substack.com/feed |
| ChinAI | RSS | https://chinai.substack.com/feed |
| The Batch (Andrew Ng) | RSS | https://www.deeplearning.ai/the-batch/feed/ |
| Import AI | RSS | https://importai.substack.com/feed |

## 不纳入的信源

| 信源 | 原因 |
|------|------|
| 华尔街见闻(网页版) | Cloudflare保护，爬取成功率极低 |

## 抓取规范

- 所有请求添加User-Agent伪装
- 超时设置：15秒
- 异常兜底：单个信源失败不影响整体
- 并发线程：8个
- 每个信源最多抓取25条
