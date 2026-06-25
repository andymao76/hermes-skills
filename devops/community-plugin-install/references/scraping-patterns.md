# 爬虫 & 批量下载场景参考

本 session 中发现的爬虫类 skill 搜索和安装模式。

## 爬虫类 skill 搜索关键词

| 搜索词 | 结果质量 | 说明 |
|---|---|---|
| `npx skills search scraper` | 高 | 最直接，apify/firecrawl 等 |
| `npx skills search crawl` | 高 | firecrawl-crawl 系列 |
| `npx skills search scraping` | 中 | 更多教学类 |
| `npx skills search spider` | 低 | 较少 |

## 网络环境处理

- 本机可直接访问国内站点（baidu.com, zhimg.com）
- 国外站点（google.com, github releases）需代理 127.0.0.1:7897
- Python requests 默认不走代理（不走系统 HTTPS_PROXY）
- Docker daemon 代理配置在 /etc/docker/daemon.json
- 测试国内可达性：curl -s --connect-timeout 5 https://www.baidu.com/

## 图片下载测试结果

- Python requests + Pillow = 稳定可用
- 下载脚本：~/.hermes/scripts/batch-download.py
- 输出目录：~/Pictures/downloads/

## 缺失但可用的工具

- yt-dlp: 已安装（系统 Python3）
- aiohttp: 已安装（异步批量下载）
