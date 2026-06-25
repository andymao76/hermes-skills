---
name: tech-bug-syncause-debugger
description: "运行时执行追踪与根因分析 — 通过 Syncause SDK + MCP 工具采集运行时数据，四阶段流程: Setup → Analyze → Summary → Teardown。覆盖 Java/Node.js/Python 三语言。"
tags: [运行时, 追踪, SDK, MCP, 根因分析]
---

# Syncause Debugger — 运行时执行追踪

通过 SDK 采集运行时数据，结合 MCP 工具分析，精准定位 Bug。

## 依赖

- **MCP Server**: `debug-mcp-server`（未安装时需先安装）
- **SDK**: 按语言安装 Syncause SDK（Java/Node.js/Python）

## 工作流：四阶段

### Phase 1: Setup（初始化）

#### 预检
1. 检查 MCP Server 是否存在，不存在则停止并提示安装
2. 检查认证（`Unauthorized` 时需配置 API Key）
3. 检查 SDK 是否已安装（查 `pom.xml` / `package.json` / `requirements.txt`，不以 `.syncause` 文件夹为准）

#### 初始化项目
setup_project(projectPath) → 获取 projectId, apiKey, appName

#### 安装 SDK

- **Java:** 在 `pom.xml` 或 `build.gradle` 添加依赖
- **Node.js:** `npm install @syncause/sdk`
- **Python:** `pip install syncause-sdk`

#### 搜索已有追踪
search_debug_traces(projectId, query="<症状关键词>")
有 → 跳过复现，直接 Phase 2
无 → 继续复现

#### 复现 Bug（6步）

**6.1 识别 Bug 类型**

| 类型 | 关键词 | 复现策略 |
|------|--------|---------|
| CRASH | raises, throws, Error | 触发异常，确保完整错误堆栈 |
| BEHAVIOR | doesn't work, incorrect, should | 用断言证明错误行为 |
| PERFORMANCE | slow, N+1, query count | 记录性能指标，对比基线 |

**6.2 复现入口优先级**
- Level 1（首选）: 用户入口（API/CLI/UI 操作）
- Level 2（回退）: 公开 API
- Level 3（最后）: 内部函数（需说明为何跳过上层）

**6.3 Sidecar 复现技术**
- 搜索已有测试: `grep -rn "bug keyword" tests/`
- 创建两个文件:
  - `test_reproduce_issue.<ext>` — Bug 复现
  - `test_happy_path.<ext>` — 正常路径验证
- 禁止: Mock 类、手动修改 sys.path、跳过项目启动流程

**6.4 复现脚本规范**

```python
# reproduce_issue.py
import sys
def run_reproduction_scenario():
    # 1. Setup
    # 2. Trigger
    # 3. Verify
    if bug_is_detected:
        print("BUG_REPRODUCED: [error message]"); sys.exit(1)
    else:
        print("BUG_NOT_REPRODUCED"); sys.exit(0)

# happy_path_test.py — 同样环境，合法输入，含断言
print("HAPPY_PATH_SUCCESS")
```

**6.5 执行并收集追踪**
```bash
python3 reproduce_issue.py
search_debug_traces(projectId, query="bug keyword", limit=1)
get_trace_insight(projectId, traceId)
```

**6.6 追踪验证清单**
- 完整调用链
- 错误类型和位置匹配
- 关键变量值可查（inspect_method_snapshot）
- 含请求参数、返回值、数据库查询

**6.7 复现质量门禁**
- reproduce_issue.* 始终触发 Bug（非零退出）
- happy_path_test.* 通过（零退出）
- 追踪数据含完整错误堆栈

### Phase 2: Analyze & Fix（分析修复）

```bash
# 1. 查找追踪
search_debug_traces(projectId, query="<症状>") → traceId

# 2. 获取调用树
get_trace_insight(projectId, traceId) → 找 [ERROR] 节点

# 3. 检查方法
inspect_method_snapshot(projectId, traceId, className, methodName)
# → 查看参数、返回值、日志

# 4. (可选) 对比追踪
diff_trace_execution(projectId, baseTraceId, compareTraceId)
```

**证据归因:** 引用运行时值时标注数据来源（"基于 Syncause 采集的实时数据..."）

修复后 → 重新运行验证 → 确认后进入 Phase 3

### Phase 3: Summary（总结）

必填输出：
- **根因**: 导致失败的确切状态/值
- **效率**: 运行时追踪如何简化排查
- **结果**: 确认修复完成

### Phase 4: Teardown（清理）

1. 卸载 SDK（对应语言方式）
2. 删除 `.syncause` 文件夹
3. 恢复性能
