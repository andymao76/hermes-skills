#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻情报中心 - 情报简报生成
不按源分类，按价值分类输出Markdown简报
"""

import os
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))


def _now_display():
    """当前时间显示"""
    return datetime.now(CST).strftime('%Y年%m月%d日 %H:%M')


def _format_sources(sources):
    """格式化来源列表"""
    if isinstance(sources, list):
        return '、'.join(sources)
    return str(sources)


def _generate_impact_hint(item):
    """根据分类和内容生成影响判断"""
    title = item.get('title', '')
    category = item.get('category', '')
    level = item.get('level', '')
    
    hints = []
    
    # 基于分类的影响判断
    category_impacts = {
        'AI深度': '可能影响AI技术路线和相关投资方向',
        '全球科技': '可能影响科技行业格局和竞争态势',
        '金融财经': '可能影响市场情绪和投资决策',
        '开源社区': '可能影响开发者生态和技术选型',
        '国内资讯': '值得关注的社会和经济动向',
    }
    
    if category in category_impacts:
        hints.append(category_impacts[category])
    
    # 多源报道加成
    if item.get('source_count', 1) >= 3:
        hints.append('多源交叉验证，可信度高')
    
    return '；'.join(hints) if hints else '持续关注后续发展'


def _generate_action_hint(item):
    """根据分级生成行动建议"""
    level = item.get('level', '')
    category = item.get('category', '')
    source_count = item.get('source_count', 1)
    
    if '🔴' in level:
        if category == 'AI深度':
            return '建议深入了解技术细节，评估对自身业务的影响'
        elif category == '金融财经':
            return '建议关注市场开盘反应，审视相关持仓'
        elif category == '全球科技':
            return '建议追踪后续报道，关注行业反应和评论'
        else:
            return '建议深入了解详情，评估影响范围'
    elif '🟡' in level:
        return '建议保持关注，等待更多信息'
    else:
        return '可暂缓关注'


def _extract_themes(items):
    """从关键情报中提取核心主题"""
    themes = []
    seen_keywords = set()
    
    for item in items:
        if '🔴' not in item.get('level', ''):
            continue
        title = item.get('title', '')
        category = item.get('category', '')
        
        # 简单主题提取
        if category == 'AI深度' and 'AI' not in seen_keywords:
            themes.append('AI领域动态')
            seen_keywords.add('AI')
        elif category == '金融财经' and '金融' not in seen_keywords:
            themes.append('金融市场变化')
            seen_keywords.add('金融')
        elif category == '全球科技' and '科技' not in seen_keywords:
            themes.append('科技行业进展')
            seen_keywords.add('科技')
        elif category == '开源社区' and '开源' not in seen_keywords:
            themes.append('开源生态更新')
            seen_keywords.add('开源')
    
    return themes


def generate_briefing(classified_items, stats, mode='daily', output_dir=None):
    """
    生成情报简报（Markdown格式）
    
    参数:
        classified_items: 分级后的新闻条目列表
        stats: 各级别统计
        mode: 模式 (daily/quick/topic/trace)
        output_dir: 输出目录
    
    返回:
        str: Markdown简报内容
    """
    # 按级别分组
    critical = [i for i in classified_items if '🔴' in i.get('level', '')]
    attention = [i for i in classified_items if '🟡' in i.get('level', '')]
    normal = [i for i in classified_items if '⚪' in i.get('level', '')]
    noise = [i for i in classified_items if '🔇' in i.get('level', '')]
    
    lines = []
    
    # 标题
    mode_labels = {
        'daily': '每日情报',
        'quick': '快速扫描',
        'topic': '领域深挖',
        'trace': '追踪更新',
    }
    mode_label = mode_labels.get(mode, '情报')
    
    lines.append(f"# 📡 新闻情报中心 — {mode_label}")
    lines.append(f"")
    lines.append(f"> 生成时间：{_now_display()}")
    lines.append(f"> 数据概览：共 {len(classified_items)} 条情报 | "
                 f"🔴关键 {len(critical)} | 🟡关注 {len(attention)} | "
                 f"⚪一般 {len(normal)} | 🔇噪音 {len(noise)}（已折叠）")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    
    # 🔴 关键情报区
    if critical:
        lines.append(f"## 🔴 关键情报")
        lines.append(f"")
        for idx, item in enumerate(critical, 1):
            lines.append(f"### {idx}. {item.get('title', '')}")
            lines.append(f"")
            
            # 来源信息
            source_count = item.get('source_count', 1)
            sources = item.get('sources', [item.get('source', '')])
            if source_count > 1:
                lines.append(f"- 📰 **{source_count}个源报道**：{_format_sources(sources)}")
            else:
                lines.append(f"- 📰 来源：{item.get('source', '')}")
            
            # 分类
            lines.append(f"- 🏷️ 分类：{item.get('category', '')}")
            
            # 热度
            hot = item.get('hot', 0)
            if hot > 0:
                lines.append(f"- 🔥 热度：{hot}")
            
            # 影响判断
            impact = _generate_impact_hint(item)
            lines.append(f"- 💥 **影响**：{impact}")
            
            # 行动建议
            action = _generate_action_hint(item)
            lines.append(f"- 🎯 **建议**：{action}")
            
            # 链接
            url = item.get('url', '')
            if url:
                lines.append(f"- 🔗 [查看原文]({url})")
            
            lines.append(f"")
    
    # 🟡 值得关注区
    if attention:
        lines.append(f"## 🟡 值得关注")
        lines.append(f"")
        for idx, item in enumerate(attention, 1):
            source_count = item.get('source_count', 1)
            sources_str = _format_sources(item.get('sources', [item.get('source', '')]))
            hot = item.get('hot', 0)
            hot_str = f" | 🔥{hot}" if hot > 0 else ""
            multi_str = f" ({source_count}源)" if source_count > 1 else ""
            
            lines.append(f"{idx}. **{item.get('title', '')}**{multi_str}")
            lines.append(f"   _{sources_str} · {item.get('category', '')}{hot_str}_")
            lines.append(f"")
    
    # 今日总结
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## 📋 今日总结")
    lines.append(f"")
    
    themes = _extract_themes(classified_items)
    if themes:
        lines.append(f"**核心主题**：{'、'.join(themes)}")
    else:
        lines.append(f"**核心主题**：暂无突出主题")
    lines.append(f"")
    
    # 主题概述
    if critical:
        lines.append(f"**关键情报摘要**：")
        for item in critical[:5]:
            lines.append(f"- {item.get('title', '')}（{item.get('category', '')}）")
        lines.append(f"")
    
    # 追踪建议
    track_suggestions = []
    for item in critical[:3]:
        from tracker import extract_track_keywords
        kws = extract_track_keywords(item.get('title', ''))
        if kws:
            track_suggestions.append(' '.join(kws[:3]))
    
    if track_suggestions:
        lines.append(f"**🎯 建议追踪**：")
        for suggestion in track_suggestions:
            lines.append(f"- `{suggestion}` — 回复「追踪 {suggestion}」启动追踪")
        lines.append(f"")
    
    # 底部信息
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"_本简报由新闻情报中心自动生成 · 30+信源智能分析_")
    
    content = '\n'.join(lines)
    
    # 保存到文件
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        date_str = datetime.now(CST).strftime('%Y%m%d_%H%M')
        filename = f"briefing_{mode}_{date_str}.md"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[简报] 已保存到 {filepath}")
    
    return content


if __name__ == '__main__':
    # 测试简报生成
    test_items = [
        {'title': 'OpenAI发布GPT-5', 'source': 'Hacker News', 'hot': 500,
         'category': 'AI深度', 'level': '🔴关键', 'score': 85,
         'source_count': 3, 'sources': ['Hacker News', '36氪', 'IT之家'],
         'url': 'https://example.com'},
        {'title': 'A股三大指数集体上涨', 'source': '东方财富', 'hot': 200,
         'category': '金融财经', 'level': '🔴关键', 'score': 72,
         'source_count': 2, 'sources': ['东方财富', '雪球'],
         'url': 'https://example.com'},
        {'title': 'GitHub Copilot推出新功能', 'source': 'GitHub', 'hot': 80,
         'category': '开源社区', 'level': '🟡关注', 'score': 52,
         'source_count': 1, 'sources': ['GitHub'],
         'url': ''},
        {'title': '某综艺节目更新', 'source': '微博热搜', 'hot': 50,
         'category': '国内资讯', 'level': '⚪一般', 'score': 25,
         'source_count': 1, 'sources': ['微博热搜'],
         'url': ''},
        {'title': '限时抢购优惠', 'source': '广告', 'hot': 10,
         'category': '其他', 'level': '🔇噪音', 'score': 0,
         'source_count': 1, 'sources': ['广告']},
    ]
    stats = {'🔴关键': 2, '🟡关注': 1, '⚪一般': 1, '🔇噪音': 1}
    
    content = generate_briefing(test_items, stats, mode='quick')
    print(content)
