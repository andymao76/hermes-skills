# 化学药品标签与质控标准参考手册 — 综合版

> B2B API/化学中间体网站「质量标准」和「证书认证」板块的内容编写综合参考。
> 整理自 ICH Q7/Q11/Q3A/Q3C/Q6A、FDA Q7A Guidance、NMPA GMP (2010)、WHO TRS 957 等公开资料。

---

## 一、CAS 号（Chemical Abstracts Service）标准

**定义**：美国化学文摘社为每种化学物质分配的唯一数字标识符，避免多种名称导致的混淆。

**编号结构**：
```
格式: PPPPPP.PP.X
- 第一部分: 2~6 位数字
- 第二部分: 2 位数字
- 第三部分: 1 位校验码
示例: CAS 23579-79-5
```

数字越多，通常表示物质结构越复杂。

**网站应用**：
- URL 路径包含 CAS 号：`/product/orforglipron-cas-221202-67-9-api`
- 首页显眼位置放 CAS 号搜索框
- 产品页 Header 突出 CAS 号
- Structured Data: Product + ChemicalSubstance Schema

---

## 二、批号（Batch No.）

**通用约定**：批号 = 生产完毕日 YYYYMMDD

示例：生产 2023.08.21 → 批号 20230821

以**生产完毕日**（全部工序完成当天）为准，非开始日。

---

## 三、有效期（Expiry Date）与复验期（Re-test Date）

### 核心定义对比

| 概念 | 英文 | 定义 | 法律效力 |
|------|------|------|---------|
| **有效期** | Expiry Date | 在规定的贮存条件下，质量符合标准的最终期限 | **硬截止** — 超过后即使检验合格也不能使用 |
| **复验期** | Re-test Date | 贮存一定时间后需重新检验以确认质量合格的日期 | **弹性间隔** — 复验合格后可继续使用并顺延 |

### 法规依据

- **ICH Q7A 核心推荐**："原料药通常用复验期，而不用有效期。"
- **中国 GMP (2010版) 第165条**：物料质量标准必须包含"有效期或复验期"
- **中国境内原料药**：只能标有效期（按药品管理）；出口可依 ICH/FDA 标复验期

### 有效期计算

| 形态 | 有效期 | 示例（生产日 2020.01.10） |
|------|-------|------------------------|
| 固体/粉末 | +2年 -1天 | 到期 2022.01.09 |
| 液体/油状 | +1年 -1天 | 到期 2021.01.09 |
| 结晶类 | 根据熔点评估 | 熔点高→稳定→有效期长 |

### 进厂物料操作规则

| 标识情况 | 操作 |
|---------|------|
| 只有有效期 | 直接使用至有效期，一般无需复验 |
| 只有复验期 | 到期必须复验合格才能继续使用；起算点为进厂检验日期 |
| 两者同时（复验期 ≤ 有效期） | 超复验期但在有效期内，需复验合格 |
| 无明确有效期 | 企业基于风险评估自主制定复验期 |

---

## 四、纯度（Purity）与含量（Assay）

| 术语 | 定义 |
|------|------|
| **纯度（Purity）** | 混合物中所含目标组分的百分数，通常包含全部结构清晰的成分 |
| **含量（Assay）** | 特指目标活性成分的含量，如药物含量 |

- 两者反映的内容**本质上一致**，都是指混合物中目标组分的百分比
- **纯度越高，含量越高**（正相关）
- 产品页中建议同时列出 purity 和 assay 值，并附 COA/HPLC 图谱

---

## 五、GMP 核心要求 — ICH 指南体系

### 关键指南

| 指南 | 适用范围 | 核心内容 |
|------|---------|---------|
| **ICH Q7** | API 生产 GMP | 质量体系、人员、厂房、设备、文件、物料管理、生产控制、实验室控制、验证、变更控制 |
| **ICH Q11** | 原料药开发与生产 | 工艺理解、杂质控制策略、过程重现性 |
| **ICH Q3A** | 杂质控制 | 原料药中有机杂质限度 |
| **ICH Q3C** | 残留溶剂 | 残留溶剂限量标准 |
| **ICH Q6A** | 质量标准 | 检验项目和可接受标准 |
| **ICH Q2** | 分析方法验证 | 准确度、精密度、专属性和线性 |

### API 质量标准应包含的项目

1. **外观（Appearance）** — 粉末、固体、液体、晶状、油状
2. **鉴别（Identity）** — NMR、IR、MS
3. **纯度（Purity）** — HPLC/GC 法
4. **含量（Assay）**
5. **残留溶剂（Residual Solvents）**
6. **重金属/元素杂质（Heavy Metals）**
7. **熔点/水分（Melting Point / Water Content）**
8. **粒度分布（Particle Size）** — 必要时
9. **晶型（Polymorphism）** — 必要时

### 供应商应提供的文档

- **COA（Certificate of Analysis）** — 完整分析结果
- **方法验证报告** — 符合 ICH Q2
- **杂质路径分析**
- **变更控制透明度**
- **稳定性数据**
- **DMF/CEP** — 法规申报支持

### GMP 标签要求（ICH Q7 第9章）

- 中间体/API 标签应标明：名称、识别码、产品批号
- API 标签应标明：名称、地址、**有效期**（出口中间体可标**复验期**）
- 存在贮存条件的，标签上应注明
- 包装标签的发放、使用、销毁均需有记录

---

## 六、WHO 药品质量控制实验室规范

### QC 实验室质量体系要素

- 组织结构与职责界定
- 文档管理体系（SOP、质量标准、检验记录）
- 人员资质与培训
- 内部/外部审计
- 纠正与预防措施（CAPA）
- 投诉处理
- 超标结果（OOS）处理流程
- 标准品/对照品管理
- 能力验证与协作试验

### 原始数据管理要点（中国 GMP 指南）

- 记录不得涂改，修改需划线 + 签名 + 日期
- 电子数据需权限控制、审计追踪
- 数据备份需验证可恢复性
- 检验记录保存：有效期后 1 年

---

## 七、YMYL 合规 — 免责声明

药品/化学类网站属于 Google 最高 YMYL 级别，产品页底部必须包含：

```html
<div class="disclaimer">
<p><strong>For Research Use Only.</strong>
Not for human or veterinary diagnostic or therapeutic use.
This product is not a drug, medicine, or medical device.</p>
</div>
```

中文版：
```html
<div class="disclaimer">
<p><strong>仅供研究使用。</strong>
不用于人类或动物的诊断或治疗用途。
本产品不是药物、药品或医疗器械。</p>
</div>
```

---

## 八、参考来源

| 来源 | 内容 |
|------|------|
| ICH Q7 / Q7A | GMP for Active Pharmaceutical Ingredients |
| ICH Q11 | Development and Manufacture of Drug Substances |
| ICH Q6A | Specifications: Test Procedures and Acceptance Criteria |
| FDA Guidance (21 CFR Part 210/211) | GMP for APIs |
| NMPA 药品生产质量管理规范 (2010年修订) | 中国 GMP |
| WHO TRS 957 Annex 1 | Good Practices for Pharmaceutical QC Laboratories |
| 中国药典 2020版 9001 | 原料药物与制剂稳定性试验指导原则 |
| BOC Sciences | GMP for APIs: A Practical Guide |
| Tianming Pharmaceutical | Pharmaceutical Intermediate Quality Standards Guide |
| 摩熵医药 | 全面解读有效期和复验期的差别和使用 |
