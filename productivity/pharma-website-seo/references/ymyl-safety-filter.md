# YMYL 关键词安全过滤器

用于医药/化学类 B2B 网站内容审核。所有产品页发布前必须经过此过滤。

## 使用方式

1. 在 CMS 中设置关键词替换规则
2. 每次发布前用 grep/Python 扫描全文
3. 高危词不可出现，出现则必须替换或用免责声明隔离

## 完整对照表

| 分类 | 安全(可用) | 高危(禁用) | 替换建议 |
|------|-----------|-----------|---------|
| 用途描述 | for research use, in vitro study, laboratory use | for treatment, for clinical use, for human use | 加粗免责声明前置 |
| 靶点描述 | targets XXX receptor, inhibits XXX enzyme | treats XXX disease, cures XXX, therapeutic | 改为"modulates"/"targets" |
| 数据描述 | shows activity in cellular assays, demonstrates binding affinity | proven clinical efficacy, shown to treat | 附原文链接+"for reference" |
| 文献引用 | related research publication, as described in | clinical recommendation, treatment protocol | 仅引用不关联 |
| 产品定位 | chemical intermediate, building block, research compound | drug substance, active pharmaceutical for therapy | 统一用"suitable for research" |
| 质量描述 | HPLC purity >=98%, meets research grade standards | pharmaceutical grade, GMP for clinical use | GMP证书单独展示 |

## 常用免责声明模板

```html
<!-- 产品页底部必加 -->
<div class="disclaimer">
<p><strong>For Research Use Only.</strong> 
Not for human or veterinary diagnostic or therapeutic use. 
This product is not a drug, medicine, or medical device.</p>
</div>
```

## 中文版免责声明

```html
<div class="disclaimer">
<p><strong>仅供研究使用。</strong> 
不用于人类或动物的诊断或治疗用途。 
本产品不是药物、药品或医疗器械。</p>
</div>
```

## 自动检测脚本思路

```bash
# 扫描所有产品页中的高危词
grep -rn -i 'treat\|cure\|therapy\|clinical grade\|therapeutic\|疗效\|治疗\|临床' content/products/
```
