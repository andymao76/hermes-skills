# 项目目录布局快照

记录时间：2026-06-17

## 顶层目录约定

| 目录 | 用途 |
|------|------|
| `~/work-projects/` | 工作项目 |
| `~/personal-projects/` | 生活/个人项目 |
| `~/work-projects/_archive/` | 未分类归档（71项文件+目录） |

## 工作项目 (work-projects/)

| 项目目录 | 说明 | 结构特征 |
|---------|------|---------|
| A1/ | 苏丹谛听项目 (LI多层整合) | cfg/ztlig/owls/bigdata/integration |
| Indonesia-SIOCC/ | 印尼项目 (AI数据分析) | data/notebooks/scripts/models/docs/output |
| pharma-website/ | 医药原料药网站SEO | assets/backup/docs/references/scripts/src |
| ETSI-ASN1-Assistant/ | 电信标准ASN.1助手 | src/docs/tests |
| github-workspace/ | GitHub开发工作区 | src |
| _references/ | 工作参考文档 | 各类模板和最佳实践 |
| _archive/ | 未分类归档 | 71项（电信Skill文档/周报/架构图/脚本/临时目录） |

### 工作项目中的散落文件

- download_standards.py / download_standards_offline.py
- download_standards_bundle.tar.gz / _selfextract.sh
- README_DOWNLOAD_STANDARDS.md
- hermes_check.sh
- system_info.py
- myprogram.code-workspace
- Indonesia-SIOCC.zip

## 个人项目 (personal-projects/)

| 项目目录 | 说明 | 内容特点 |
|---------|------|---------|
| hermes-agent/ | Hermes Agent搭建 | 架构图PDF/SVG/HTML、配置备份、community-skills包 |
| second-brain/ | 第二大脑搭建 | smartbrain 设计稿 (PDF/PNG/HTML) |
| diudiu/ | 丢丢病情跟踪 | 健康报告HTML、贵宾犬心脏病指南、Python图片搜索脚本 |
| BACKUP/ | 个人备份 | 空 |

## 注意

- archive 中的内容可后续按需分类到具体项目或 knowledge/ 知识库
- LI/电信相关文档（HERMES_SKILL_*、Telecom_Expert_Pack 等）在 archive 中，应移到 knowledge/telecom/ 对应子目录
