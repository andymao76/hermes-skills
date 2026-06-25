# Pharma Website — 项目目录结构与资产分类

## 实际项目路径

```
~/work-projects/pharma-website/
```

> **注意：** 项目在 `work-projects/` 下，**不是** `projects/`。创建或查找项目文件时优先检查 `work-projects/`。

## 完整目录结构

```
pharma-website/
├── README.md                       # 项目概述
├── docs/
│   ├── SKILL.md                    # SEO策略主文档
│   ├── 化合物批量导入方案_V1.0.docx   # 批量导入方案
│   ├── 医药原料药网站上线完整SOP_V1.0.docx  # 上线SOP (V1.0)
│   ├── 医药原料药网站上线完整SOP_V1.2.docx  # 上线SOP (V1.2)
│   ├── searchqualityevaluatorguidelines_billingual.pdf  # Google评估指南
│   ├── references/
│   │   ├── pharma-product-keywords.md   # 产品关键词表
│   │   ├── ymyl-safety-filter.md        # YMYL安全词过滤
│   │   └── technical-seo/               # SEO技术参考资料截图
│   │       ├── 图片_20260617083731_35_1.jpg   # OKF标准推文截图
│   │       └── 不能传网上的资料.png             # 技术文档截图
│   └── screenshots/                     # 后台管理界面截图
│       ├── 图片_20260615173523_188_28.png   # 销售与运营数据统计
│       └── 图片_20260615173535_189_28.png   # 产品管理数据表格
├── personnel/
│   └── 图片_20260617111749_38_1.jpg        # 项目人员简历
├── references/
│   └── competitive/
│       └── 同行的页面效果.png                # 同行网站产品页截图
├── backup/
├── scripts/
└── src/
```

## 资产分类规则

项目中收集的图片/截图按以下规则分类存放：

| 分类 | 目录 | 内容 |
|------|------|------|
| 技术参考资料 | `docs/references/technical-seo/` | SEO技术文章截图、标准文档截图、工具界面截图 |
| 后台截图 | `docs/screenshots/` | 网站后台管理界面、数据统计、产品管理表格 |
| 竞品参考 | `references/competitive/` | 同业/竞争对手网站页面截图、产品页效果 |
| 人员资料 | `personnel/` | 团队成员的简历、证件照、资质文件 |
| 项目素材 | `src/` | 源代码、模板文件 |
| 脚本工具 | `scripts/` | 自动化脚本、批量处理工具 |
| 备份 | `backup/` | 旧版本备份 |
