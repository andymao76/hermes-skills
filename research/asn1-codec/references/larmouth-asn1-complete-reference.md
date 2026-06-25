# Larmouth ASN.1 Complete 教材参考

> Prof John Larmouth《ASN.1 Complete》
> 版本: 1999 年 5 月 31 日
> 免费 PDF: https://www.oss.com/asn1/resources/books-whitepapers-pubs/larmouth-asn1-book.pdf
> 本地: `~/knowledge/telecom/3gpp/references/larmouth-asn1-complete.PDF`（1.3MB）

## 与 Dubuisson 教材的差异

| 维度 | Dubuisson | Larmouth |
|:-----|:----------|:---------|
| 定位 | 参考手册 | 教程 + 指南 |
| 风格 | 正式严谨 | 口语化、案例驱动 |
| 编码规则 | BER/PER 详尽参考 | 演进叙事，更简洁 |
| 编译器使用 | 无 | **Ch6 完整覆盖** |
| 设计管理 | 无 | **Ch7 覆盖** |

## Section III: 编码规则独特视角

Larmouth 不是分别罗列 BER 和 PER，而是讲述 **为什么需要 PER**：

1. **BER 问题**：TLV 开销 ~50%
2. **第一步**：去掉 T 字段 → "如果知道类型，为什么还传 tag？"
3. **PER 核心**：[P][L][V] 格式，依赖子类型约束压缩
4. **PER 压缩示例**：
   - `INTEGER (0..7)` → 3 bits（BER: 3+ bytes）
   - `BOOLEAN` → 1 bit（BER: 3 bytes）

## 实用章节

| 章节 | 内容 | 适用场景 |
|:----|:-----|:---------|
| Ch1 | 协议规范基础 + 案例研究 | 理解设计选择 |
| Ch2 | ASN.1 入门 | 初学者 |
| Ch3 | 模块结构 + tagging 环境 | 规范编写 |
| Ch6 | **ASN.1 编译器使用** | 唯一覆盖此主题的教材 |
| Ch7 | 设计与管理决策 | 项目启动时参考 |
| Section III | BER→PER 演进 | 理解为何需要 PER |

## 知识库

总结笔记：`~/knowledge/telecom/3gpp/larmouth-asn1-complete-summary.md`
