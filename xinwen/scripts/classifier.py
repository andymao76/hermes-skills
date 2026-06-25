#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻情报中心 - 智能分级引擎
自动给每条新闻打标签：🔴关键 / 🟡关注 / ⚪一般 / 🔇噪音
分级维度：多源覆盖度、热度趋势、用户画像匹配度、时效性
"""

from profiler import match_score, is_noise


# 信源可信度权重
SOURCE_CREDIBILITY = {
    'Hacker News': 0.9,
    'TechCrunch': 0.85,
    'The Verge': 0.85,
    'Ars Technica': 0.85,
    'Product Hunt': 0.8,
    'GitHub Trending': 0.9,
    'HN Show': 0.85,
    'V2EX': 0.7,
    '36氪': 0.8,
    '微博热搜': 0.6,
    'IT之家': 0.75,
    '腾讯科技': 0.8,
    '知乎热榜': 0.7,
    'B站热门': 0.5,
    '东方财富': 0.85,
    '雪球': 0.7,
    '华尔街见闻': 0.85,
    '财联社': 0.85,
    'HuggingFace Papers': 0.9,
    'ArXiv AI': 0.9,
    'One Useful Thing': 0.85,
    'Interconnects': 0.85,
    'KDnuggets': 0.8,
    'Memia': 0.8,
    'AI to ROI': 0.8,
    'ChinAI': 0.8,
    'The Batch (Andrew Ng)': 0.9,
    'Import AI': 0.85,
}


def _source_weight(source):
    """获取信源可信度权重"""
    return SOURCE_CREDIBILITY.get(source, 0.6)


def compute_classify_score(item, profile):
    """
    计算综合分级分数
    
    评分维度（满分100）：
    - 多源覆盖度（0-30）：3+源报道得满分
    - 热度分数（0-25）：标准化热度值
    - 用户画像匹配度（0-25）：与用户关注领域的匹配度
    - 信源可信度（0-20）：来源的权威性
    
    参数:
        item: 新闻条目（已去重合并）
        profile: 用户画像
    
    返回:
        dict: 分级结果，包含score, level, dimensions
    """
    dimensions = {}
    
    # 1. 多源覆盖度（0-30）
    source_count = item.get('source_count', 1)
    multi_bonus = item.get('multi_source_bonus', 0)
    if source_count >= 5:
        coverage_score = 30
    elif source_count >= 3:
        coverage_score = 25
    elif source_count >= 2:
        coverage_score = 18
    else:
        coverage_score = 5
    dimensions['多源覆盖'] = coverage_score
    
    # 2. 热度分数（0-25）
    hot = item.get('hot', 0)
    # 热度标准化：根据不同信源的热度量级做对数缩放
    if hot > 0:
        import math
        hot_score = min(25, 5 + 5 * math.log10(max(hot, 1)))
    else:
        hot_score = 3
    dimensions['热度'] = round(hot_score, 1)
    
    # 3. 用户画像匹配度（0-25）
    profile_score = match_score(item.get('title', ''), profile)
    # 将0-10的匹配度映射到0-25
    profile_mapped = min(25, profile_score * 2.5)
    dimensions['画像匹配'] = round(profile_mapped, 1)
    
    # 4. 信源可信度（0-20）
    sources = item.get('sources', [item.get('source', '')])
    if sources:
        max_credibility = max(_source_weight(s) for s in sources if s)
        credibility_score = max_credibility * 20
    else:
        credibility_score = 10
    dimensions['信源可信'] = round(credibility_score, 1)
    
    # 总分
    total = sum(dimensions.values())
    
    return {
        'score': round(total, 1),
        'dimensions': dimensions,
    }


def classify_item(item, profile):
    """
    对单条新闻进行分级
    
    参数:
        item: 新闻条目
        profile: 用户画像
    
    返回:
        dict: 包含level和score的新闻条目
    """
    result = dict(item)
    
    # 先判断噪音
    if is_noise(item.get('title', ''), profile):
        result['level'] = '🔇噪音'
        result['level_code'] = 0
        result['score'] = 0
        result['dimensions'] = {}
        return result
    
    # 计算分级分数
    classify = compute_classify_score(item, profile)
    score = classify['score']
    
    result['score'] = score
    result['dimensions'] = classify['dimensions']
    
    # 分级判定
    if score >= 65:
        result['level'] = '🔴关键'
        result['level_code'] = 3
    elif score >= 40:
        result['level'] = '🟡关注'
        result['level_code'] = 2
    else:
        result['level'] = '⚪一般'
        result['level_code'] = 1
    
    # 额外规则：3+源同时报道直接升级为关键
    if item.get('source_count', 1) >= 3 and result['level_code'] < 3:
        result['level'] = '🔴关键'
        result['level_code'] = 3
        result['score'] = max(score, 65)
    
    return result


def classify_all(items, profile):
    """
    对所有新闻进行分级
    
    参数:
        items: 新闻条目列表（已去重）
        profile: 用户画像
    
    返回:
        tuple: (classified_items, stats)
            classified_items: 分级后的条目列表
            stats: 各级别统计
    """
    classified = []
    stats = {'🔴关键': 0, '🟡关注': 0, '⚪一般': 0, '🔇噪音': 0}
    
    for item in items:
        result = classify_item(item, profile)
        classified.append(result)
        level = result.get('level', '⚪一般')
        if level in stats:
            stats[level] += 1
    
    # 按分数降序排序
    classified.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    return classified, stats


if __name__ == '__main__':
    import json
    from profiler import load_profile
    
    profile = load_profile()
    
    # 测试数据
    test_items = [
        {'title': 'OpenAI发布GPT-5', 'source': 'Hacker News', 'hot': 500,
         'category': 'AI深度', 'source_count': 3, 'sources': ['Hacker News', '36氪', 'IT之家'],
         'multi_source_bonus': 15},
        {'title': 'A股三大指数集体上涨', 'source': '东方财富', 'hot': 50,
         'category': '金融财经', 'source_count': 2, 'sources': ['东方财富', '雪球'],
         'multi_source_bonus': 8},
        {'title': '某明星出轨', 'source': '微博热搜', 'hot': 800,
         'category': '国内资讯', 'source_count': 1, 'sources': ['微博热搜'],
         'multi_source_bonus': 0},
        {'title': '限时3折优惠抢购', 'source': '广告', 'hot': 10,
         'category': '其他', 'source_count': 1, 'sources': ['广告'],
         'multi_source_bonus': 0},
    ]
    
    classified, stats = classify_all(test_items, profile)
    print(f"分级统计: {stats}")
    for item in classified:
        dims = item.get('dimensions', {})
        dim_str = ' | '.join(f"{k}={v}" for k, v in dims.items()) if dims else '-'
        print(f"  {item['level']} [{item.get('score', 0):.1f}] {item['title']}")
        print(f"         维度: {dim_str}")
