# Skill 生命周期管理：从创建到验证到归档

## 完整生命周期

```
需求识别 → 创建 SKILL.md → 测试验证 → 投入使用 → 维护更新 → curator 归档
```

## 如何验证 Skill 是否正确（三阶模型）

### 一阶：功能验证（创建时做一次）

| 方法 | 工具 | 说明 |
|------|------|------|
| 手动测试 | 直接加载 skill 并执行典型任务 | 确认基本功能正常 |
| 测试用例 | `evals/evals.json` 写 2-3 个真实场景 | 覆盖主要使用路径 |
| A/B 对比 | skill-creator 的 with-skill vs baseline 并行跑 | 量化确认 skill 确实提升效果 |
| 断言评分 | 定义可验证指标（文件存在、格式正确、内容匹配） | `generate_review.py` 展示结果 |

### 二阶：持续验证（日常使用中）

| 信号 | 动作 |
|------|------|
| 用户纠正工作流/步骤 | 立即 patch 对应 skill，添加缺失步骤或 pitfall |
| 用户纠正输出风格/格式 | 更新 skill 的输出规范说明 |
| 遇到新错误或变通方案 | 添加为 pitfall 或扩展参考文件 |
| skill 加载后发现过时/错误 | 立即 patch |

### 三阶：生命周期管理（自动化）

| 机制 | 频率 | 说明 |
|------|------|------|
| `hermes curator` | 每 7 天 | 自动归档过期 skill、合并重复、标记低使用率 |
| 安全审计 | 每 2 天 | security-audit.py 扫描 skill 是否含敏感信息 |
| skill-creator 迭代 | 按需 | 旧 skill → 评估 → 改进 → 新 iteration |

## 维护规则

1. **类级命名**：`hdfs-expert`、`flink-sre-expert`，不写 `fix-X-today`
2. **SKILL.md 含完整 frontmatter**：name/description/category/priority/tags
3. **每条规则说明"为什么"**：不要只写 MUST/Never，解释背后的推理
4. **用户偏好嵌入 SKILL.md 正文**：用户纠正的输出格式/工作流，立即 patch 到 skill，不只在 memory
5. **reference 文件**：超过 500 行的内容拆到 `references/`，SKILL.md 留指针
