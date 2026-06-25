# 小红书热门笔记数据字段格式参考

## 接口返回 JSON 结构

```json
{
  "articles": [
    {
      "title": "笔记标题",
      "author": "作者名",
      "authorUrl": "作者主页链接",
      "url": "笔记链接",
      "publishTime": "2026-05-15",
      "interactionCount": 10000,
      "relevanceScore": 9.8,
      "heatScore": 3.0,
      "timelinessScore": 2.0,
      "totalScore": 14.8
    }
  ],
  "latestHotArticles": [
    {
      "title": "热门笔记",
      "author": "作者",
      "authorUrl": "https://www.xiaohongshu.com/user/profile/xxx",
      "url": "笔记链接",
      "publishTime": "2026-05-14",
      "interactionCount": 85000
    }
  ],
  "hotTopics": [],
  "relatedSearches": ["拓展词1", "拓展词2"],
  "total": 100
}
```

## 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| title | string | 笔记标题 |
| author | string | 作者昵称 |
| authorUrl | string | 作者主页链接 |
| url | string | 笔记链接 |
| publishTime | string | 发布时间 (YYYY-MM-DD) |
| interactionCount | int | 互动数（点赞+收藏+评论） |
| relevanceScore | float | 相关性评分 (0-10) |
| heatScore | float | 热度评分 (0-3) |
| timelinessScore | float | 时效评分 (0-2) |
| totalScore | float | 总分 (0-15) |

## 排序规则

- **有关键词时**：按 totalScore 降序（relevanceScore + heatScore + timelinessScore）
- **全站热门/无关键词时**：按 interactionCount 降序
- **推荐热门笔记**：始终按 interactionCount 降序
