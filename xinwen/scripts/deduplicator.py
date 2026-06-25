#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻情报中心 - 语义去重与合并
同一事件多源报道 → 合并为一条情报
基于TF-IDF + 余弦相似度实现，不依赖额外库
"""

import math
import re
from collections import Counter


# 中英文停用词
STOP_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
    'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were',
    'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
    'will', 'would', 'could', 'should', 'may', 'might', 'can',
    'this', 'that', 'these', 'those', 'it', 'its', 'he', 'she',
    'they', 'we', 'you', 'i', 'me', 'my', 'your', 'his', 'her',
    'our', 'their', 'not', 'no', 'nor', 'so', 'if', 'as', 'than',
    '的', '了', '在', '是', '我', '有', '和', '就', '不', '人',
    '都', '一', '上', '也', '很', '到', '说', '要', '去', '你',
    '会', '着', '没有', '看', '好', '这', '他', '她', '它', '们',
    '那', '些', '什么', '怎么', '与', '及', '等', '为', '中',
    '对', '被', '让', '把', '从', '而', '又', '将', '已', '之',
}


def _tokenize(text):
    """简单分词：英文按空格，中文按2-4字滑窗 + 实体词提取"""
    if not text:
        return []
    
    text = text.lower()
    # 提取英文单词
    en_tokens = re.findall(r'[a-z][a-z0-9]+', text)
    # 提取中文n-gram (2-4字)
    cn_text = re.sub(r'[^\u4e00-\u9fff]', '', text)
    cn_tokens = []
    for n in [2, 3, 4]:
        for i in range(len(cn_text) - n + 1):
            cn_tokens.append(cn_text[i:i+n])
    
    # 额外：提取中文实体词（数字+单位、品牌名等）
    # 匹配如 "GPT-5"、"iPhone 16" 等混合模式
    mixed_tokens = re.findall(r'[A-Za-z]+[-]?\d+', text)
    # 匹配数字
    num_tokens = re.findall(r'\d+', text)
    
    tokens = en_tokens + cn_tokens + mixed_tokens + num_tokens
    # 过滤停用词
    tokens = [t for t in tokens if t not in STOP_WORDS and len(t) >= 2]
    return tokens


def _tfidf_vector(text, idf_dict):
    """计算文本的TF-IDF向量（稀疏表示为字典）"""
    tokens = _tokenize(text)
    if not tokens:
        return {}
    
    # 计算TF
    tf = Counter(tokens)
    total = len(tokens)
    
    # 计算TF-IDF
    vector = {}
    for word, count in tf.items():
        tf_val = count / total
        idf_val = idf_dict.get(word, 1.0)
        vector[word] = tf_val * idf_val
    
    return vector


def _cosine_similarity(vec1, vec2):
    """计算两个稀疏向量的余弦相似度"""
    if not vec1 or not vec2:
        return 0.0
    
    # 找到共同词
    common_words = set(vec1.keys()) & set(vec2.keys())
    
    dot_product = sum(vec1[w] * vec2[w] for w in common_words)
    
    norm1 = math.sqrt(sum(v * v for v in vec1.values()))
    norm2 = math.sqrt(sum(v * v for v in vec2.values()))
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def _keyword_overlap_score(title1, title2):
    """
    关键词共现评分（中文标题辅助判断）
    提取关键实体词，计算共现比例
    
    参数:
        title1: 标题1
        title2: 标题2
    
    返回:
        float: 共现评分 0-1
    """
    if not title1 or not title2:
        return 0.0
    
    def _extract_key_tokens(text):
        """提取关键实体词"""
        tokens = set()
        text_lower = text.lower()
        # 英文实体（大写开头或含数字的，如GPT-5, OpenAI）
        for m in re.finditer(r'[A-Za-z][A-Za-z0-9\-]*', text):
            word = m.group().lower()
            if len(word) >= 3:
                tokens.add(word)
        # 数字
        for m in re.finditer(r'\d+', text):
            tokens.add(m.group())
        # 中文关键词（2字以上）
        cn = re.sub(r'[^\u4e00-\u9fff]', ' ', text)
        for m in re.finditer(r'[\u4e00-\u9fff]{2,4}', cn):
            tokens.add(m.group())
        # 过滤停用词
        tokens = {t for t in tokens if t not in STOP_WORDS}
        return tokens
    
    tokens1 = _extract_key_tokens(title1)
    tokens2 = _extract_key_tokens(title2)
    
    if not tokens1 or not tokens2:
        return 0.0
    
    # Jaccard相似度
    intersection = tokens1 & tokens2
    union = tokens1 | tokens2
    
    if not union:
        return 0.0
    
    jaccard = len(intersection) / len(union)
    
    # 如果共现关键词占比高，加权
    overlap_ratio_1 = len(intersection) / len(tokens1) if tokens1 else 0
    overlap_ratio_2 = len(intersection) / len(tokens2) if tokens2 else 0
    
    # 取两种度量的较大值
    return max(jaccard, (overlap_ratio_1 + overlap_ratio_2) / 2)


def compute_idf(items):
    """
    计算IDF（逆文档频率）
    
    参数:
        items: 新闻条目列表
    
    返回:
        dict: 词 -> IDF值
    """
    doc_count = len(items)
    if doc_count == 0:
        return {}
    
    # 统计每个词出现在多少个文档中
    doc_freq = Counter()
    for item in items:
        tokens = set(_tokenize(item.get('title', '')))
        for token in tokens:
            doc_freq[token] += 1
    
    # 计算IDF
    idf_dict = {}
    for word, df in doc_freq.items():
        idf_dict[word] = math.log(doc_count / (df + 1)) + 1  # 平滑
    
    return idf_dict


def deduplicate(items, threshold=0.45):
    """
    语义去重与合并
    
    参数:
        items: 新闻条目列表
        threshold: 相似度阈值，0.45以上视为同一事件
    
    返回:
        list[dict]: 去重后的新闻条目列表
    """
    if not items:
        return []
    
    # 计算IDF
    idf_dict = compute_idf(items)
    
    # 计算每条新闻的TF-IDF向量
    vectors = []
    for item in items:
        vec = _tfidf_vector(item.get('title', ''), idf_dict)
        vectors.append(vec)
    
    # 并查集式合并
    n = len(items)
    parent = list(range(n))
    
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    
    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            # 按热度合并到更大的组
            if items[px].get('hot', 0) >= items[py].get('hot', 0):
                parent[py] = px
            else:
                parent[px] = py
    
    # 两两比较相似度
    for i in range(n):
        for j in range(i + 1, n):
            sim = _cosine_similarity(vectors[i], vectors[j])
            # 额外：关键词共现检测（中文标题辅助判断）
            kw_sim = _keyword_overlap_score(
                items[i].get('title', ''), items[j].get('title', ''))
            combined_sim = max(sim, kw_sim)
            if combined_sim >= threshold:
                union(i, j)
    
    # 按组合并
    groups = {}
    for i in range(n):
        root = find(i)
        if root not in groups:
            groups[root] = []
        groups[root].append(i)
    
    # 合并结果
    result = []
    for root, indices in groups.items():
        # 选热度最高的作为主条目
        best_idx = max(indices, key=lambda i: items[i].get('hot', 0))
        main_item = dict(items[best_idx])
        
        # 收集所有来源
        sources = []
        urls = []
        for idx in indices:
            src = items[idx].get('source', '')
            url = items[idx].get('url', '')
            if src and src not in sources:
                sources.append(src)
            if url and url not in urls:
                urls.append(url)
        
        main_item['merged'] = len(indices) > 1
        main_item['source_count'] = len(indices)
        main_item['sources'] = sources
        main_item['all_urls'] = urls
        
        # 多源加分
        if len(indices) >= 3:
            main_item['multi_source_bonus'] = 15
        elif len(indices) >= 2:
            main_item['multi_source_bonus'] = 8
        else:
            main_item['multi_source_bonus'] = 0
        
        result.append(main_item)
    
    return result


if __name__ == '__main__':
    import json
    
    # 测试数据
    test_items = [
        {'title': 'OpenAI发布GPT-5模型', 'source': '36氪', 'hot': 100, 'category': 'AI深度'},
        {'title': 'GPT-5正式发布，性能大幅提升', 'source': 'IT之家', 'hot': 80, 'category': 'AI深度'},
        {'title': 'OpenAI GPT-5亮相', 'source': 'Hacker News', 'hot': 200, 'category': '全球科技'},
        {'title': 'A股三大指数集体上涨', 'source': '东方财富', 'hot': 50, 'category': '金融财经'},
        {'title': 'A股市场今日全线飘红', 'source': '雪球', 'hot': 40, 'category': '金融财经'},
        {'title': 'GitHub Copilot推出新功能', 'source': 'GitHub', 'hot': 60, 'category': '开源社区'},
    ]
    
    result = deduplicate(test_items)
    print(f"去重前: {len(test_items)} 条, 去重后: {len(result)} 条")
    for item in result:
        merged = '✓' if item.get('merged') else ' '
        print(f"  [{merged}] {item['title']} "
              f"(源数={item['source_count']}, 加分={item['multi_source_bonus']})")
