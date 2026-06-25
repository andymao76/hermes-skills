#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻情报中心 - 话题追踪联动
用户对某条情报说"追踪" → 输出topic_tracking命令模板
自动生成追踪关键词和初始快照
"""

import json
import re
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))


def extract_track_keywords(title, source='', category=''):
    """
    从标题中提取追踪关键词
    
    参数:
        title: 新闻标题
        source: 来源
        category: 分类
    
    返回:
        list[str]: 追踪关键词列表
    """
    if not title:
        return []
    
    keywords = []
    
    # 提取英文专有名词（大写开头或全大写，2+字符）
    en_names = re.findall(r'\b[A-Z][A-Za-z0-9]+\b', title)
    # 过滤常见非专有名词
    common_words = {'The', 'A', 'An', 'In', 'On', 'At', 'To', 'For',
                    'Of', 'With', 'By', 'From', 'Is', 'Are', 'Was',
                    'And', 'Or', 'But', 'Not', 'New', 'How', 'Why',
                    'What', 'This', 'That', 'Its', 'Has', 'Can'}
    en_names = [n for n in en_names if n not in common_words and len(n) >= 2]
    keywords.extend(en_names)
    
    # 提取数字+单位模式（如 GPT-5, iPhone 16）
    version_patterns = re.findall(r'[A-Za-z]+[-\s]?\d+', title)
    keywords.extend(version_patterns)
    
    # 提取中文关键词（2-4字）
    cn_words = re.findall(r'[\u4e00-\u9fff]{2,4}', title)
    # 过滤停用词
    cn_stop = {'发布', '宣布', '推出', '最新', '重要', '首次', '正式',
               '已经', '可能', '将会', '如何', '为什么', '什么'}
    cn_words = [w for w in cn_words if w not in cn_stop]
    keywords.extend(cn_words[:5])
    
    # 去重
    seen = set()
    unique_keywords = []
    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower not in seen:
            seen.add(kw_lower)
            unique_keywords.append(kw)
    
    return unique_keywords[:8]


def generate_snapshot(item):
    """
    生成初始快照（用于追踪对比）
    
    参数:
        item: 新闻条目
    
    返回:
        dict: 快照数据
    """
    return {
        'title': item.get('title', ''),
        'source': item.get('source', ''),
        'hot': item.get('hot', 0),
        'sources': item.get('sources', []),
        'level': item.get('level', ''),
        'snapshot_time': datetime.now(CST).strftime('%Y-%m-%d %H:%M'),
    }


def generate_track_command(item):
    """
    生成话题追踪命令模板
    
    参数:
        item: 新闻条目
    
    返回:
        dict: 追踪命令信息
    """
    title = item.get('title', '')
    keywords = extract_track_keywords(title)
    
    if not keywords:
        keywords = [title[:20]]
    
    # 生成追踪主题名
    topic_name = ' '.join(keywords[:3])
    
    # 生成初始快照
    snapshot = generate_snapshot(item)
    
    # 构建追踪命令
    command = {
        'action': 'track',
        'topic': topic_name,
        'keywords': keywords,
        'initial_snapshot': snapshot,
        'command_template': (
            f'帮我追踪/关注 "{topic_name}"\n'
            f'追踪关键词：{", ".join(keywords)}\n'
            f'初始快照：{json.dumps(snapshot, ensure_ascii=False)}'
        ),
    }
    
    return command


def format_track_output(item):
    """
    格式化追踪输出（Markdown）
    
    参数:
        item: 新闻条目
    
    返回:
        str: Markdown格式的追踪信息
    """
    track = generate_track_command(item)
    
    lines = [
        f"## 🎯 话题追踪建议",
        f"",
        f"**{item.get('title', '')}**",
        f"",
        f"- 追踪主题：{track['topic']}",
        f"- 追踪关键词：{'、'.join(track['keywords'])}",
        f"- 触发来源：{item.get('source', '')}（{item.get('level', '')}）",
        f"",
        f"### 追踪命令",
        f"```",
        f"{track['command_template']}",
        f"```",
        f"",
        f"> 💡 复制上述命令发送给主助手，即可启动话题追踪",
        f"> 系统将定期推送相关更新",
    ]
    
    return '\n'.join(lines)


if __name__ == '__main__':
    # 测试
    test_items = [
        {'title': 'OpenAI发布GPT-5，性能提升3倍', 'source': 'Hacker News',
         'hot': 500, 'level': '🔴关键', 'sources': ['HN', '36氪', 'IT之家']},
        {'title': '特斯拉FSD V13开始推送', 'source': 'IT之家',
         'hot': 300, 'level': '🟡关注', 'sources': ['IT之家']},
    ]
    
    for item in test_items:
        track = generate_track_command(item)
        print(json.dumps(track, ensure_ascii=False, indent=2))
        print()
        print(format_track_output(item))
        print("---")
