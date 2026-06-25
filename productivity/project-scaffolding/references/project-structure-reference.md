# 项目分类与目录结构参考

收集自 GitHub 和业界最佳实践（kriasoft/Folder-Structure-Conventions, Cookiecutter Data Science 等）。

## 8 类项目目录模板

| 分类 | 核心目录 | 适用场景 |
|------|---------|---------|
| 通用软件 | src/docs/test/tools | 软件开发、API 开发、库项目 |
| 数据科学/AI | data/notebooks/models/src | 数据分析、ML、LLM 应用 |
| LI/LIG 监听 | 对接/工勘/巡检/方案/抓包/解码 | ZTLIG(Sinovatio)、华为/ZTE 合法监听 |
| AI 推理/API | src/api/core/models/config/docker | 模型部署、推理服务 |
| AI Agent | agents/tools/prompts/memory/workflows | 智能体应用 |
| Web 应用 | frontend/backend/api/db/docker | 前后端分离应用 |
| 运维/SRE | scripts/config/alerts/backups/cron | 运维监控 |
| 大数据 | config/scripts/sql/jobs/alerts | Hadoop/HBase/Kafka/Flink |

完整模板详见 `~/projects/_references/project-structure-reference.md`
