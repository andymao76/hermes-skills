---
name: pharma-website-seo
description: "B2B 医药原料药(API)/化学中间体供应商网站的SEO与内容策略 — 从0到1建站、E-E-A-T合规、Google Ads、CAS号SEO、批量产品导入、域名迁移。覆盖制药/化学行业B2B网站的全链路运营。"
version: 1.1.0
author: andymao
license: MIT
tags: [SEO, E-E-A-T, Google Ads, Pharma, B2B, Chemical-Supplier]
---

# Pharma Website SEO — 医药API/化工供应商网站运营

B2B 医药原料药（API）、化学中间体、科研试剂供应商网站的 SEO 与内容策略。覆盖从 0 到 1 建站到持续运营的完整链路。

## Triggers

- 用户问及医药/化工类B2B网站的SEO、Google Ads、内容策略
- 用户提及E-E-A-T、YMYL、Search Quality Evaluator Guidelines
- 用户需要为化学产品（API/中间体/科研试剂）做产品页
- 用户需要批量导入大量化学化合物产品
- 用户提及CAS号搜索、COA/MSDS文档展示
- 用户有老域名需要迁移或复用
- 用户要求组织/分类项目资产（图片、文档等）到目录
- 用户需要编写产品页的「质量认证」或「规格参数」板块

## 参考文件速查

| 需要做什么 | 打开哪个参考文件 |
|-----------|----------------|
| 产品页「质量规格」板块写作 | `references/chemical-product-qc-standards.md`（简要版）或 `references/chemical-product-qc-standards-comprehensive.md`（综合版，含 ICH/FDA/NMPA/WHO 法规） |
| YMYL 安全词过滤 + 免责声明 | `references/ymyl-safety-filter.md` |
| 15 个旗舰产品关键词 + CAS 号 | `references/pharma-product-keywords.md` |
| 项目目录结构与资产分类规则 | `references/project-directory-structure.md` |
| 有效期/复验期/纯度/含量速查 | `references/chemical-product-qc-standards.md` 第3~6节 |

## Core Concepts

### 客户画像

| 角色 | 需求 | 搜索行为 | 内容类型 |
|------|------|---------|---------|
| 药厂采购经理 | 找API/中间体供应商 | CAS号 + supplier | 产品数据表 + COA |
| 实验室科研人员 | 买研究级化合物 | compound name + buy | NMR图谱 + 文献引用 |
| 贸易商 | 找上游货源比价 | bulk + CAS + manufacturer | MOQ + 报价 + DMF |

### 供应矩阵

| 层级 | 客户 | 利润 |
|------|------|------|
| 原料药 API | 制剂厂 | 最高 |
| 高级中间体 | API厂/贸易商 | 高 |
| 中间体 | 贸易商/工厂 | 中 |
| 科研试剂 | 实验室 | 低(引流) |

### 产品架构（3层策略）

| 层级 | 数量 | 处理方式 | SEO策略 |
|------|------|---------|---------|
| T1-旗舰品 | 15个 | 手动精细制作，E-E-A-T满分 | 独立URL + 原创内容 + 推理 |
| T2-重点品 | 50-100个 | CSV批量导入(WP All Import) | 模板化独立页 + 主动索引 |
| T3-长尾品 | 几千个 | 数据库动态列表+搜索 | 动态URL + 被索引不主动推 |

## E-E-A-T Compliance (YMYL Level)

医药/化学类属于 Google 最高 YMYL 级别。必须满足以下四个维度：

### Experience（经验）
- 每篇产品页有真实作者署名 + LinkedIn/ORCID链接
- 使用企业邮箱（非Gmail/Yahoo）
- 团队页展示核心成员背景、职业资格证书
- 客户/合作伙伴 Logo 墙

### Expertise（专业知识）
- 所有技术声明引用 PubMed / ClinicalTrials.gov / FDA/EMA
- 每条产品页 >= 3 个权威来源
- 中英双语版本（英文版搜索引擎信任度更高）
- 技术深度：靶点机制、临床数据、竞争格局

### Authoritativeness（权威性）
- 被行业媒体引用（FierceBiotech, Endpoints, BioSpace）
- 外链来自 .edu / .org / 行业网站
- ISO 9001 / GMP 认证展示（含证书编号+发证机构链接）
- 行业协会认证

### Trustworthiness（可信度）
- 公司地址+电话+邮箱（Google Maps嵌入加分）
- 隐私政策 + 免责声明（"For research use only. Not for human consumption."）
- 每篇内容标注更新日期
- HTTPS 证书

### YMYL 关键词安全过滤器

| 分类 | 安全词(可用) | 高危词(禁用) |
|------|-------------|-------------|
| 用途描述 | for research use, in vitro study | for treatment, for clinical use |
| 靶点描述 | targets XXX receptor | treats XXX disease |
| 数据描述 | shows activity in cellular assays | proven clinical efficacy |
| 产品定位 | chemical intermediate, building block | drug substance |

## Product Page Template

每个产品页必须包含以下结构：

```
H1: [产品名] - API/Intermediate - CAS: [XXX-XX-X]

[首段概述] 150-200字
[产品快照表] CAS号/分子式/纯度/包装/交期
[API规格表] 质量标准/杂质谱/晶型/DMF状态  — QC字段定义参考 `references/chemical-product-qc-standards.md`
[中间体信息] 关键中间体CAS/工艺阶段
[文档下载区] 2x3网格(数据表/SDS/COA/HNMR/LCMS/Protocol)
[参考文献] >=3条 PubMed/ClinicalTrials链接
[询价按钮] 自动填充产品名+CAS号
[作者署名] 真实姓名/资质/LinkedIn
[免责声明] For research use only
```

## 产品文档展示区设计

参考 MedChemExpress 风格的产品"纯度与文档"区域：

```
┌────────────────────────────────────────────┐
│  纯度: 99.98%          选择批次: [下拉]    │
├────────────┬────────────┬──────────────────┤
│ 📄 数据表   │ 📄 SDS     │ 📄 COA           │
│   (281 KB)  │  (420 KB)  │  (255 KB)        │
├────────────┼────────────┼──────────────────┤
│ 📄 HNMR    │ 📄 LCMS    │ 📄 操作说明      │
│   (308 KB)  │  (122 KB)  │  (2659 KB)       │
└────────────┴────────────┴──────────────────┘
```

设计要素：
- 纯度独占一行大字突出
- 批次选择下拉框（多批次COA追溯）
- 2x3网格布局，文件+Kb标注
- 每份文档标注文件大小（透明可信）
- PDF图标统一

## Google Ads Strategy

### 关键词矩阵

| 类型 | 例子 | 匹配 | 出价 |
|------|------|------|------|
| CAS精准 | [221202-67-9 API] | 精确 | 中高 |
| 产品+supplier | "Orforglipron supplier" | 短语 | 中 |
| 产品+bulk | "Orforglipron bulk" | 短语 | 中 |
| 靶点+intermediate | "GLP-1 intermediate" | 短语 | 中低 |
| API manufacturer | "GLP-1 API manufacturer" | 短语 | 中 |

### 落地页要求
- 广告写什么 → 落地页必须展示什么（GMP证书编号、COA下载、物流合作方）
- 违反此原则 Google 可能封禁医疗类广告账户

## CAS号 SEO (核心差异化策略)

采购经理的核心搜索路径：知道CAS号 → Google搜索 → 找到你 → 看规格 → 询价

- URL 路径包含 CAS 号: `/product/orforglipron-cas-221202-67-9-api`
- 首页显眼位置放 CAS 号搜索框
- 每个产品页 header 突出 CAS 号
- Structured Data: Product + ChemicalSubstance Schema

## 技术配置 Checklist

- HTTPS (Let's Encrypt)
- WordPress + Rank Math SEO
- XML Sitemap 提交 Google Search Console
- Structured Data: Product + ChemicalSubstance + BreadcrumbList + Organization
- 301 redirect if migrating from old site
- 域名历史检测: Wayback Machine + Ahrefs + GSC + mxToolbox

## 批量导入策略 (WordPress)

### WP All Import CSV导入

```csv
product_name,cas_number,category,supply_level,purity,packaging,status
Orforglipron API,221202-67-9,GLP-1,API,99%+,1kg/5kg/25kg,publish
```

### Custom Post Type 配置
- Slug: `product`
- URL: `/product/{product_name}-cas-{cas_number}`
- Custom Fields (ACF): cas_number, molecular_formula, purity, supply_level, packaging, coa_file, msds_file

## QC质量标准参考（产品页内容）

产品页「质量标准」板块所需字段定义、法规依据和示例见三个参考文件：

- `references/chemical-product-qc-standards.md` — 由 EOS MED CHEM 照片提取的简要版（CAS/批号/有效期/纯度）
- `references/chemical-product-qc-standards-detailed.md` — 综合 ICH/FDA/WHO/NMPA 研究整理的过渡版
- `references/chemical-product-qc-standards-comprehensive.md` — 完整综合版（含 GMP 框架、8 项参考标准、YMYL 免责声明、供应商文档列表）

三者互补使用：简要版适合快速查阅常见字段含义；详细版适合写产品页「质量认证」板块时引用；综合版适合对外展示的质量文档编写。

## 13个产品关键词表

See `references/pharma-product-keywords.md` for the full table.

## 项目目录与资产分类

实际项目路径: `~/work-projects/pharma-website/`（注意在 `work-projects/` 下，不是 `projects/`）。

项目资产分类规则见 `references/project-directory-structure.md`。

### 资产分类规则（速查）

项目中收集的图片/截图按以下规则分类存放：

| 分类 | 目录 | 内容示例 |
|------|------|---------|
| 技术参考资料 | `docs/references/technical-seo/` | SEO技术截图、标准文档、工具界面 |
| 后台截图 | `docs/screenshots/` | 数据统计、产品管理表格 |
| 竞品参考 | `references/competitive/` | 同行网站产品页截图 |
| 人员资料 | `personnel/` | 简历、资质文件 |

### 图片分析→分类放入流程

当需要分析并组织项目中的图片/截图时：

1. 用 Vision API 分析图片内容（类型、文字、布局）
2. 根据内容判定分类（技术参考/后台截图/竞品参考/人员档案）
3. 移动到对应的子目录
4. 清理临时/重复文件
5. 更新 SKILL.md 的参考文件速查表

## Risk Checklist (Pre-Launch)

1. **域名历史风险** — Web Archive + Ahrefs + GSC 检查老域名无处罚
2. **E-E-A-T可验证性** — 所有作者真实署名+LinkedIn+企业邮箱
3. **YMYL医疗宣称红线** — 禁用词过滤 + "For research use only" 前置免责声明
4. **Google Ads落地页匹配** — 广告承诺 vs 落地页展示必须100%一致

## 日常工作SOP

| 频率 | 动作 |
|------|------|
| 每天 | 3小时内响应询价 + GSC报警检查 |
| 每周 | 1篇行业文章 + 1个产品页 + Ads数据分析 |
| 每月 | SEO复盘 + 产品数据更新 + 外链建设 |
| 每季 | 全站健康检查 + E-E-A-T更新 + 技术SEO审计 |
