# Session知识沉淀模板

每次完成重要任务后，按此清单执行经验沉淀。

## 1. 成果确认
- [ ] 本次任务是否完成？
- [ ] 有无未解决的技术阻塞？

## 2. 知识库更新
- [ ] `project_status.yaml` 相关项目状态更新
- [ ] `decision_log.md` 如有架构/技术决策须追加
- [ ] `worklog/daily/YYYY-MM-DD.md` 写入今日工作记录

## 3. 技能提炼
- [ ] 是否发现可复用的技术模式/流程？ → 写入 `knowledge/skills/`
- [ ] 是否有排错过程值得保存？ → 写入 `knowledge/skills/troubleshooting/`
- [ ] 是否该创建/更新 Hermes Skill？ → `skill_manage`

## 4. 记忆更新
- [ ] 用户偏好/环境事实是否有变化？ → `memory`
- [ ] 发现的新API key位置/格式？ → `memory`

## 5. 后续行动
- [ ] 是否有 cron 任务需要创建/调整？
- [ ] 是否需要下一次跟进？

## 快速检查命令
```bash
# 查看当前项目状态
cat ~/knowledge/_system/project_status.yaml

# 刷新语义索引
cd ~/knowledge && python3 .obsidian/scripts/kb-search.py refresh

# 查看今日工作日志
cat ~/knowledge/worklog/daily/$(date +%Y-%m-%d).md
```
