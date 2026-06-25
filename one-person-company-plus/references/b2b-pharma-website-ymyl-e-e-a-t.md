# B2B 医药原料药/中间体网站: E-E-A-T + SEO + Google Ads 策略

基于 Google Search Quality Evaluator Guidelines (2025-09) 的医药类 YMYL 网站最佳实践。

---

## 1. 核心界定

| 维度 | 说明 |
|------|------|
| 网站类型 | B2B 原料药 (API) / 中间体 / 科研试剂供应商 |
| 目标客户 | 药厂采购经理、实验室科研人员、贸易商 |
| Google 分类 | **YMYL (Your Money or Your Life)** — 医疗/药品类 |
| 核心评估标准 | E-E-A-T (Experience / Expertise / Authoritativeness / Trustworthiness) |

---

## 2. 客户画像与内容映射

| 角色 | 搜索行为 | 站内路径 | 转化行动 |
|------|---------|---------|---------|
| 药厂采购经理 | 搜 CAS 号 + "supplier"/"API" | 首页CAS搜索 → 产品页规格表 → COA下载 → 询价 | 提交询价单 |
| 实验室科研人员 | 搜 compound name + "buy"/"research grade" | 产品页 → 文献引用 → NMR图谱 → 小包装下单 | 购买/询价 |
| 贸易商 | 搜 "bulk" + CAS + "manufacturer China" | 关于我们 → MOQ → 出口文件 → 批量询价 | 大单询价 |

---

## 3. 产品页标准结构（B2B 医药供应商版）

```
H1: [产品名] — API / Intermediate — CAS: [XXX-XX-X]

【首段概述】150-200字
→ 包含: 产品名 + CAS号 + 靶点/机制 + 研发阶段 + 可供应规格

【产品快照表】（最上方，显眼位置）
CAS号 | 分子式 | 分子量 | 纯度 | 供应级别 | 包装 | 交货期

【API 规格表】（如可供应 API）
| 项目 | 标准 |
|------|------|
| 质量标准 | USP/EP/CP/In-house |
| 外观 | 白色至类白色粉末 |
| 单杂 | ≤0.1% |
| 总杂 | ≤0.5% |
| 残留溶剂 | ICH Q3C 合规 |
| 晶型 | [如有] |
| 粒径 | D90 [如有] |
| DMF 状态 | 已备案/计划中/无 |

【中间体信息】
关键中间体 CAS、合成路线简图、工艺阶段（实验室/中试/商业化）

【文件下载】
COA, MSDS, 结构确认图谱 (NMR/MS/HPLC), TDS

【参考文献】≥3 条 PubMed / ClinicalTrials 链接

【作者署名】真实姓名 + 学历/资历 + 更新日期

【询价按钮】
→ 表单自动填充产品名+CAS号
→ 数量下拉: 1g/5g/25g/100g/1kg/>1kg/定制
→ 用途: 科研/中试/商业化生产/贸易

【免责声明】内容仅供研究参考，不构成医疗建议
```

---

## 4. E-E-A-T 逐项检查清单

### Experience（经验）
- [ ] 每篇产品页有真实作者署名 + 简介（学历/从业经验）
- [ ] 团队页面展示核心成员背景（化药/生物技术相关）
- [ ] 案例研究: 过往合作项目（脱敏）
- [ ] 客户/合作伙伴 Logo 墙

### Expertise（专业知识）
- [ ] 所有技术声明引用 PubMed / ClinicalTrials.gov / FDA/EMA
- [ ] 每条产品页引用 ≥3 个权威来源
- [ ] 作者不得为 "admin"/"小编"，必须真实人名
- [ ] 技术深度达标（靶点机制、临床数据、竞争格局）
- [ ] 中英双语版本（英文页面更受国外客户信任）

### Authoritativeness（权威性）
- [ ] 被行业媒体引用（FierceBiotech, Endpoints, BioSpace 等）
- [ ] 外链来自 .edu / .org / 行业网站
- [ ] 行业协会认证展示
- [ ] ISO 9001 / GMP 认证展示

### Trustworthiness（可信度）
- [ ] 关于我们: 详细公司介绍 + 办公地址
- [ ] 联系页: 真实邮箱 + 电话 + 地址（Google Maps 嵌入加分）
- [ ] 隐私政策 + 数据保护声明
- [ ] 免责声明（研究参考用途）
- [ ] 每篇内容标注最后更新日期
- [ ] HTTPS 证书 + 安全站点标识

---

## 5. 12 年老域名迁移策略

**核心原则：不换域名**。新站直接用老域名上线。

```
旧域名（12年）              新站（同一域名）
├── 旧服务器/旧CMS     →    ├── 新服务器/新CMS
├── 12年外链积累        →    ├── 全部继承 ✅
└── Google 信任度       →    └── 0 沙盒期
```

操作步骤:
1. 备份旧站全部文件 + 数据库
2. 新服务器搭建新 CMS
3. 上线新站（同一域名）
4. 旧 URL → 301 重定向到新站对应页面
5. Google Search Console 提交新 Sitemap
6. 监控一周流量

---

## 6. Google Ads 策略（B2B 精准投放）

### 关键词类型
| 类型 | 示例 | 匹配方式 |
|------|------|---------|
| CAS号精准 | `[221202-67-9 API]` | 精确 |
| 产品名+supplier | `"Orforglipron supplier"` | 短语 |
| 产品名+bulk | `"Orforglipron bulk"` | 短语 |
| 靶点+intermediate | `"GLP-1 intermediate"` | 短语 |
| API manufacturer | `"GLP-1 API manufacturer"` | 短语 |
| 科研级 | `"KRAS G12D inhibitor buy"` | 广泛 |

### 预算建议
- 测试期: $50-100/天
- 稳定期: $500-1000/月（按转化效果调整）
- 配合 LinkedIn + 行业目录免费渠道

### 广告文案模板
```
标题1: [产品名] API | CAS [XXX-XX-X] | 高纯度 99%+
标题2: [靶点] API 中国供应商 | ISO 9001 | 全球发货
描述: 供应 API 与关键中间体。GMP 合规，COA/MSDS 齐全。公斤级到吨级。立即询价 →
```

---

## 7. 关键词矩阵（15个热门靶点产品）

| 产品 | CAS号 | URL slug | 核心长尾词 |
|------|-------|---------|-----------|
| Orforglipron | 221202-67-9 | orforglipron-cas-221202-67-9-api | oral GLP-1 API supplier, GLP-1 intermediate China |
| Taletrectinib | — | taletrectinib-ros1-api | ROS1 inhibitor API, DS-6051b intermediate |
| MRTX1133 | — | mrtx1133-kras-g12d | KRAS G12D inhibitor research grade |
| Olomorasib | — | olomorasib-kras-g12c | KRAS G12C inhibitor, LY3537982 |
| Camizestrant | — | camizestrant-er-degrader-api | ER degrader API, AZD9833 bulk |
| Zongertinib | — | zongertinib-her2-mutant-api | HER2 TKI API, BI-1810631 |
| Daraxonrasib | — | daraxonrasib-kras-g12c | RMC-6291 intermediate supplier |
| RMC-9805 | — | rmc-9805-kras-g12d | KRAS G12D inhibitor, Revolution Medicines |
| NVL-655 | — | nvl-655-alk | next-gen ALK inhibitor intermediate |
| BLU-945 | — | blu-945-kras-g12c | BLU-945 EGFR combination intermediate |
| AMG 193 | — | amg-193-prmt5 | PRMT5 inhibitor intermediate |
| IDE397 | — | ide397-mat2a | MAT2A inhibitor, IDEAYA intermediate |
| TNG462 | — | tng462-prmt5 | MTA-cooperative PRMT5 intermediate |
| TYRA-300 | — | tyra-300-fgfr3 | FGFR3 inhibitor intermediate |
| BDTX-1535 | — | bdtx-1535-egfr | EGFR/HER2 brain metastases intermediate |

注: CAS 号需根据实际产品确认，部分早期项目可能未公开。

---

## 8. 技术 SEO 清单（CMS 自建站）

- [ ] HTTPS (Let's Encrypt 免费)
- [ ] 移动端适配 (Responsive)
- [ ] 页面速度 < 3秒 (Core Web Vitals)
- [ ] WebP 图片格式
- [ ] CDN (Cloudflare 免费版)
- [ ] XML Sitemap → Google Search Console
- [ ] robots.txt 正确配置
- [ ] Canonical URL 防重复
- [ ] 404 自定义页面

### URL 结构
```
/product/orforglipron-cas-221202-67-9-api
/product/taletrectinib-cas-xxxxx-xx-x-intermediate
```
禁止无意义URL (`/p=123`, `/product/pid123`)

### Schema.org 结构化数据
- Product（产品名称、CAS号、纯度、包装）
- ChemicalSubstance（CAS号、分子式、IUPAC名）
- BreadcrumbList（面包屑）
- Organization（公司信息）
- Article（行业文章）
- FaqPage（常见问题）

---

## 9. 内容日历（首月）

| 周次 | 产品页 | 文章 |
|------|--------|------|
| 第1周 | 前5个热品页上线 | 首页+关于我们+联系 |
| 第2周 | 剩余10个产品页 | GLP-1市场分析文章 |
| 第3周 | 英文版产品页 | KRAS G12C vs G12D对比 |
| 第4周 | CAS号数据库页面 | 肺癌靶向药研发综述 |

---

## 10. 日常运营频率

| 频率 | 动作 |
|------|------|
| 每天 | 询价3小时内响应、GSC报警检查、GA4实时数据 |
| 每周 | 1篇行业文章（中英）+ 1个新产品页、Google Ads优化、关键词排名检查 |
| 每月 | SEO表现复盘、产品数据更新、外链建设、竞品分析 |
| 每季 | 全站内容审计、E-E-A-T更新、技术SEO审计、Google Ads QBR |

---

## 参考来源

- Google Search Quality Evaluator Guidelines (2025-09-11) — E-E-A-T 对标标准
- Google Ads 保健和药物政策 (support.google.com/adspolicy/answer/176031)
- 2025 广告安全报告 (blog.google)
