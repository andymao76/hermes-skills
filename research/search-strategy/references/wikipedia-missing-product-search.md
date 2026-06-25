# Wikipedia 不收录产品时的公共网络搜索策略

## 适用场景

当维基百科不收录某个特定产品/设备的独立词条时，需要通过多种关键词变体和不同来源类型来定位有效文档。

## 关键词变体策略

一个产品可能有多个官方名称和历史变体。分别搜索每个变体：

```
原始名称: Alcatel S1240
变体搜索:
  - "Alcatel S1240"        # 产品型号
  - "System 12"            # 系统代号
  - "System 1240"          # 早期代号
  - "Alcatel 1000 S12"     # 后续命名
  - "A1000 S12"            # 缩写形式
```

## 来源类型优先级（从高到低）

| 优先级 | 来源类型 | 特点 | 示例 |
|--------|---------|------|------|
| 1 | 运营商/厂商官方 PDF | 权威、有完整架构描述 | Telefonica、Nokia 文档库 |
| 2 | 技术社区论坛 | 包含实际命令和操作经验 | Alcatel Unleashed、Stack Overflow |
| 3 | 学术/技术文档分享 | 功能描述、架构概述 | Scribd、PDFCOFFEE、archive.org |
| 4 | 开放源码复古电信项目 | 硬件逆向、操作记录 | Osmocom Retronetworking |
| 5 | 中文技术社区 | 中文操作经验和命令参考 | 知乎专栏、百度文库、CSDN |
| 6 | 设备制造商用户手册 | 终端用户文档 | 厂商官网 |
| 7 | 通用商业手册网站 | 低信息密度、混杂 | manymanuals、manualslib |

## 多轮搜索模式

对旧电信设备（1980s-1990s），单轮搜索通常不够。串联如下：

**第1轮** — 产品名称 + "operation and maintenance" + "manual" + "PDF"
**第2轮** — 深入提取第1轮中发现的有价值来源（论坛帖、PDF）
**第3轮** — 基于第1/2轮发现的新关键词继续搜索（如具体命令名、子系统名）
**第4轮** — 中文关键词搜索（适用于中国曾大量部署的设备）

## 命令示例

```bash
# 第一阶段：宽泛搜索
web_search:
  - query: '"S1240" "Alcatel" "operation and maintenance" manual PDF'
  - query: '"System 12" digital exchange O&M documentation'

# 第二阶段：提取论坛/社区内容后，搜索具体命令
web_search:
  - query: '"S1240" "Alcatel" "maintenance" command manual MML'

# 第三阶段：中文环境搜索
web_search:
  - query: '上海贝尔 S1240 操作维护 手册 MML 命令 中文'
```

## 注意

- Telefonica 等运营商发布的 PDF 通常是 **PUBLIC** 级别的公开文档
- Scribd 上的文档可能需要登录，但内容可以通过 web_extract 提取摘要
- Osmocom 的 retronetworking wiki 加载可能较慢（HTTPS + 地理距离），优先使用 curl 或调整 timeout
- Alcatel 被 Nokia 收购后，旧设备文档不再公开发布，技术社区论坛（如 Alcatel Unleashed）是最后的高质量来源
