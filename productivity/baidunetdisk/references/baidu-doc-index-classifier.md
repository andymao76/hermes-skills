# 百度网盘文档索引分类 → 知识库生成器

## 输入
- `~/knowledge/baidu-netdisk-index.md` — xpan API 扫描生成的原始索引
- 格式：Markdown，每段 `### /目录名` 下接表格 `| 文件名 | 类型 | 大小 |`

## 分类映射规则

双层分类策略：先按**目录路径**关键词判断，未命中的再按**文件名**关键词判断。

### 第一层：目录路径匹配（优先）

```python
DIR_CATEGORIES = {
    '核心网': '核心网', 'EPC': '核心网', 'HLR': '核心网', 'DHLR': '核心网',
    'MSC': '核心网', 'MGW': '核心网', 'GGSN': '核心网', 'SGSN': '核心网',
    'IMS': 'IMS-VoLTE', 'VOLTE': 'IMS-VoLTE', 'SIP': 'IMS-VoLTE',
    'NFV': 'NFV-SDN-Cloud', 'SDN': 'NFV-SDN-Cloud',
    'LI': '合法监听', 'LAWFUL': '合法监听', '监听': '合法监听',
    '5G': '5G-NB-IoT', 'NB': '5G-NB-IoT',
    '大数据': '大数据-AI',
    '网管': '网管-运维',
    '3GPP': '3GPP标准',
    'ASN': 'ASN1-编解码',
    ...（完整见 SKILL.md）
}
```

### 第二层：文件名匹配（路径未命中时 fallback）

```python
FILE_KEYWORDS = {
    'IMS': 'IMS-VoLTE', 'VoLTE': 'IMS-VoLTE',
    '核心网': '核心网', 'EPC': '核心网',
    '5G': '5G-NB-IoT', 'VoNR': '5G-NB-IoT',
    'ASN': 'ASN1-编解码',
    'MySQL': '数据库', 'SQL': '数据库',
    ...（完整见 SKILL.md）
}
```

### Fallback 策略
- 根目录 `/` 和 `/来自：` `/PHOTO` `/Music` 等 → `个人文件`
- 其他均归为 `其他资料`

## 重复检测

### 规则
- 同名（忽略大小写）+ 同大小（字节数完全一致）= 重复
- 纯 `2 * 语言版本的 .html` 文件，仅保留中文(`cn`)版本
- Python 2.7 相关文件关键词: `python2, python2.7, py2, py27`

### 去重策略
1. **SAGE 文档 HTML 文件** — 多语言版本的 `.html` 文件重复，直接移除重复标记
2. **真实重复** — 同名同大小文件跨目录存在，保留主目录条目，其他位置用 `↳ 同文件见:` 替换

## 输出结构

```
~/knowledge/baidu-netdisk/
├── _index.md          # 总索引
├── _classification.md # 按领域导航
├── 核心网.md          # 每个分类独立文件
├── ims-volte.md
├── nfv-sdn-cloud.md
├── ...（通常 15-20 个分类文件）
```

每个分类文件包含：
1. 文档数 + 总大小统计
2. 文件类型分布
3. 按原网盘目录分组罗列的文档清单
4. 跨分类重复标记

## 注意事项

- 禁用 HTTP_PROXY 环境变量（同 xpan API）
- `no_proxy` 环境变量不影响 urllib 行为，必须 `os.environ.pop()`
- 出现 JSON 解析错误时用 `strict=False`
- recursion depth 超过 200 会炸栈，用 BFS 替代递归
- `collections.defaultdict` 从 `from collections import defaultdict` 导入
