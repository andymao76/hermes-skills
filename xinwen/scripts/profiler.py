#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻情报中心 - 用户画像自适应
首次使用读取USER.md和MEMORY.md，提取关注领域关键词
"""

import os
import re
from collections import Counter


# 默认画像关键词
DEFAULT_PROFILE = {
    'core_keywords': ['AI', '人工智能', '大模型', '科技', '金融'],
    'secondary_keywords': ['开源', '创业', '投资', 'LLM', 'GPT',
                           '芯片', '自动驾驶', '机器人', '融资'],
    'blacklist_keywords': ['广告', '推广', '优惠券', '折扣', '拼团',
                           '砍价', '签到', '抽奖'],
}


def _read_file_safe(path):
    """安全读取文件，不存在返回空字符串"""
    if not os.path.exists(path):
        return ''
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return ''


def _extract_keywords(text):
    """从文本中提取关键词（简单分词+频率统计）"""
    if not text:
        return []
    
    # 去除Markdown标记
    text = re.sub(r'[#*`>\-\[\]\(\)]+', ' ', text)
    
    # 提取中英文关键词
    # 英文单词（2+字符）
    en_words = re.findall(r'\b[A-Za-z][A-Za-z0-9]+\b', text)
    # 中文短语（2-6字）
    cn_phrases = re.findall(r'[\u4e00-\u9fff]{2,6}', text)
    
    # 过滤停用词
    stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you',
                  'all', 'can', 'had', 'her', 'was', 'one', 'our',
                  'out', 'has', 'have', 'been', 'from', 'this',
                  'that', 'with', 'they', 'will', 'each', 'make',
                  'like', 'been', 'long', 'very', 'after', 'just',
                  '的', '了', '在', '是', '我', '有', '和', '就',
                  '不', '人', '都', '一', '一个', '上', '也', '很',
                  '到', '说', '要', '去', '你', '会', '着', '没有',
                  '看', '好', '自己', '这', '他', '她', '它', '们',
                  '那', '些', '什么', '怎么', '如果', '因为', '所以',
                  '但是', '可以', '已经', '或者', '而且', '然后',
                  '使用', '需要', '进行', '通过', '关于', '以下'}
    
    en_words = [w.lower() for w in en_words
                if w.lower() not in stop_words and len(w) >= 3]
    cn_phrases = [p for p in cn_phrases
                  if not any(sw in p for sw in ['的话', '时候', '情况'])]
    
    # 统计频率
    all_words = en_words + cn_phrases
    counter = Counter(all_words)
    
    # 返回高频词（至少出现2次，或总数少于20则全部返回）
    if len(counter) < 20:
        return list(counter.keys())
    
    return [word for word, count in counter.most_common(30) if count >= 2]


def load_profile(base_dir='.'):
    """
    加载用户画像
    
    参数:
        base_dir: 工作目录，用于查找USER.md和MEMORY.md
    
    返回:
        dict: 用户画像，包含core_keywords, secondary_keywords, blacklist_keywords
    """
    profile = {
        'core_keywords': list(DEFAULT_PROFILE['core_keywords']),
        'secondary_keywords': list(DEFAULT_PROFILE['secondary_keywords']),
        'blacklist_keywords': list(DEFAULT_PROFILE['blacklist_keywords']),
    }
    
    # 尝试读取用户文件
    user_md = _read_file_safe(os.path.join(base_dir, 'USER.md'))
    memory_md = _read_file_safe(os.path.join(base_dir, 'MEMORY.md'))
    
    combined = user_md + '\n' + memory_md
    if not combined.strip():
        print("[画像] 未找到用户画像文件，使用默认画像")
        return profile
    
    # 提取关键词
    keywords = _extract_keywords(combined)
    if keywords:
        # 前10个作为核心关键词
        profile['core_keywords'] = keywords[:10]
        # 后20个作为次要关键词
        profile['secondary_keywords'] = keywords[10:30]
        print(f"[画像] 从用户文件提取 {len(keywords)} 个关键词")
    else:
        print("[画像] 未提取到有效关键词，使用默认画像")
    
    return profile


def match_score(title, profile):
    """
    计算标题与用户画像的匹配度
    
    参数:
        title: 新闻标题
        profile: 用户画像
    
    返回:
        float: 匹配度分数 0-10
    """
    if not title:
        return 0.0
    
    score = 0.0
    title_lower = title.lower()
    
    # 核心关键词匹配（每个3分，上限6分）
    for kw in profile.get('core_keywords', []):
        if kw.lower() in title_lower:
            score += 3.0
    score = min(score, 6.0)
    
    # 次要关键词匹配（每个1分，上限3分）
    for kw in profile.get('secondary_keywords', []):
        if kw.lower() in title_lower:
            score += 1.0
    score = min(score, 9.0)
    
    # 黑名单扣分
    for kw in profile.get('blacklist_keywords', []):
        if kw in title:
            score -= 5.0
    
    return max(score, 0.0)


def is_noise(title, profile):
    """
    判断标题是否为噪音
    
    参数:
        title: 新闻标题
        profile: 用户画像
    
    返回:
        bool: 是否为噪音
    """
    if not title:
        return True
    
    # 黑名单关键词
    for kw in profile.get('blacklist_keywords', []):
        if kw in title:
            return True
    
    # 纯广告模式
    ad_patterns = [
        r'限时.{0,4}折', r'免费领取', r'点击领取', r'^【.*福利.*】',
        r'^\d+元$', r'^包邮$', r'优惠券$',
    ]
    for pattern in ad_patterns:
        if re.search(pattern, title):
            return True
    
    return False


if __name__ == '__main__':
    profile = load_profile()
    print(json.dumps(profile, ensure_ascii=False, indent=2))
    
    # 测试匹配
    test_titles = [
        'OpenAI发布GPT-5',
        '拼多多限时3折优惠',
        'A股三大指数集体上涨',
        'GitHub Copilot新增功能',
    ]
    for t in test_titles:
        score = match_score(t, profile)
        noise = is_noise(t, profile)
        print(f"  {t} -> 匹配度={score:.1f}, 噪音={noise}")
