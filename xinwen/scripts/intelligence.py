#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻情报中心 - 主引擎
编排完整流程：抓取 → 分级 → 去重 → 排序 → 简报输出
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone, timedelta

# 添加脚本目录到路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from fetch_sources import fetch_all
from deduplicator import deduplicate
from classifier import classify_all
from profiler import load_profile
from briefing import generate_briefing

CST = timezone(timedelta(hours=8))


def run_intelligence(mode='daily', topic=None, keyword=None,
                     base_dir='.', output_dir=None, json_output=False):
    """
    运行情报分析完整流程
    
    参数:
        mode: 模式 (daily/quick/topic/trace)
        topic: 领域过滤（仅topic模式）
        keyword: 追踪关键词（仅trace模式）
        base_dir: 工作目录（查找用户画像）
        output_dir: 简报输出目录
        json_output: 是否输出JSON（调试用）
    
    返回:
        dict or str: 分析结果
    """
    print(f"📡 新闻情报中心启动 — 模式：{mode}")
    print(f"{'='*50}")
    
    # 1. 加载用户画像
    print(f"\n[1/4] 加载用户画像...")
    profile = load_profile(base_dir)
    
    # 2. 数据抓取
    print(f"\n[2/4] 数据抓取中...")
    topic_filter = None
    if mode == 'topic' and topic:
        topic_filter = topic
    elif mode == 'trace':
        # trace模式：根据关键词推测关注领域
        topic_filter = None  # 全量抓取，后续过滤
    
    raw_items = fetch_all(topic_filter=topic_filter)
    
    # trace模式：按关键词过滤
    if mode == 'trace' and keyword:
        kw_lower = keyword.lower()
        raw_items = [i for i in raw_items
                     if kw_lower in i.get('title', '').lower()]
        print(f"  [关键词过滤] '{keyword}' → {len(raw_items)} 条匹配")
    
    if not raw_items:
        print("⚠ 未抓取到任何数据")
        return {'error': '未抓取到数据', 'items': []}
    
    # 3. 去重合并
    print(f"\n[3/4] 语义去重...")
    deduped = deduplicate(raw_items)
    print(f"  去重前: {len(raw_items)} 条 → 去重后: {len(deduped)} 条")
    
    # 4. 智能分级
    print(f"\n[4/4] 智能分级...")
    classified, stats = classify_all(deduped, profile)
    print(f"  分级统计: {stats}")
    
    # quick模式：只保留🔴和🟡，限制5条
    if mode == 'quick':
        classified = [i for i in classified
                      if '🔴' in i.get('level', '') or '🟡' in i.get('level', '')]
        classified = classified[:5]
        stats = {'🔴关键': sum(1 for i in classified if '🔴' in i.get('level', '')),
                 '🟡关注': sum(1 for i in classified if '🟡' in i.get('level', '')),
                 '⚪一般': 0, '🔇噪音': 0}
        print(f"  [快速模式] 精选 {len(classified)} 条")
    
    # JSON输出
    if json_output:
        result = {
            'mode': mode,
            'timestamp': datetime.now(CST).strftime('%Y-%m-%d %H:%M:%S'),
            'stats': stats,
            'items': classified,
        }
        return result
    
    # 生成简报
    report_dir = output_dir or os.path.join(
        os.path.dirname(SCRIPT_DIR), 'reports')
    content = generate_briefing(classified, stats, mode=mode,
                                output_dir=report_dir)
    
    print(f"\n{'='*50}")
    print(f"✅ 情报分析完成")
    print(f"   模式: {mode}")
    print(f"   结果: {stats}")
    
    return {
        'mode': mode,
        'stats': stats,
        'items': classified,
        'briefing': content,
    }


def main():
    parser = argparse.ArgumentParser(
        description='新闻情报中心 - 智能新闻分析工具')
    parser.add_argument('--mode', type=str, default='daily',
                        choices=['daily', 'quick', 'topic', 'trace'],
                        help='运行模式：daily(完整)/quick(快速)/topic(领域)/trace(追踪)')
    parser.add_argument('--topic', type=str, default=None,
                        help='领域深挖话题（仅topic模式）：全球科技/开源社区/国内资讯/金融财经/AI深度')
    parser.add_argument('--keyword', type=str, default=None,
                        help='追踪关键词（仅trace模式）')
    parser.add_argument('--base-dir', type=str, default='.',
                        help='工作目录（查找用户画像文件）')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='简报输出目录')
    parser.add_argument('--json', action='store_true',
                        help='输出JSON格式（调试用）')
    
    args = parser.parse_args()
    
    result = run_intelligence(
        mode=args.mode,
        topic=args.topic,
        keyword=args.keyword,
        base_dir=args.base_dir,
        output_dir=args.output_dir,
        json_output=args.json,
    )
    
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif isinstance(result, dict) and 'briefing' in result:
        print(result['briefing'])


if __name__ == '__main__':
    main()
