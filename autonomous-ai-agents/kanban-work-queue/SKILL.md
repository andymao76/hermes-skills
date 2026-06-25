---
name: kanban-work-queue
description: Hermes KANBAN 多 agent 协作面板 — 配置、CLI 命令、任务生命周期、调度器、工具集门控
version: 1.1.0
created_by: agent
platforms: [linux, macos]
---


# Hermes KANBAN 多 Agent 协作面板

Hermes KANBAN 是一个基于 SQLite 的持久化任务面板（`~/.hermes/kanban.db`），用于**跨会话、跨 profile 的多 agent 协作**。调度器内嵌在 gateway 中，自动扫描 ready 任务并派发给指定 profile 的 worker 进程执行。

KANBAN 的核心设计是：**CLI 给人类用，工具集给 agent 用**。普通会话看不到 kanban 工具集，只有被调度器派发的 worker 进程才有。

---

## 任务生命周期

```
triage → todo → scheduled → ready → running → done
                                  ↓
                               blocked
```

| 状态 | 含义 |
|------|------|
| triage | 草稿，需要 specifier 完善描述后 promote 到 todo |
| todo | 已定稿，等待排期 |
| scheduled | 已排期 |
| ready | 就绪，调度器/人工可领取执行 |
| running | 正在执行 |
| blocked | 阻塞（等人工、等外部依赖） |
| done | 完成 |

---

## CLI 命令速查

### 基本操作

| 操作 | 命令 |
|------|------|
| 列出所有任务 | `hermes kanban list` |
| 查看任务详情 | `hermes kanban show t_xxxxxxxx` |
| 创建任务 | `hermes kanban create "任务标题" --priority N --body "描述"` |
| 认领任务 | `hermes kanban assign t_xxxxxxxx default` |
| 添加评论 | `hermes kanban comment t_xxxxxxxx "评论内容"` |
| 完成任务 | `hermes kanban complete t_xxxxxxxx` |
| 阻塞任务 | `hermes kanban block t_xxxxxxxx --reason "原因"` |
| 解除阻塞 | `hermes kanban unblock t_xxxxxxxx` |

### 高级操作

| 操作 | 命令 |
|------|------|
| 关联任务 | `hermes kanban link t_aaa t_bbb` |
| 取消关联 | `hermes kanban unlink t_aaa t_bbb` |
| 归档任务 | `hermes kanban archive t_xxxxxxxx` |
| 查看统计 | `hermes kanban stats` |
| 查看日志 | `hermes kanban log` |
| 查看运行记录 | `hermes kanban runs` |
| 切换面板 | `hermes kanban boards` |
| 查看多个面板 | `hermes kanban boards` |

### 创建高级任务

**创建带 goal 循环的任务（AI 自动迭代直到完成）：**
```bash
hermes kanban create "优化 Nginx 配置" --goal --body "检查当前配置，给出优化建议并应用"
```
- `--goal`：让 worker 反复迭代直到任务完成
- `--goal-max-turns 20`：可调整迭代上限（默认 20）

**创建关联子任务：**
```bash
hermes kanban create "修复登录 Bug" --parent t_xxx
```

**创建带 skill 的任务（worker 自动加载指定技能）：**
```bash
hermes kanban create "审查 PR #42" --skill github-code-review
```
- `--skill` 可重复，如 `--skill translation --skill github-code-review`
- 会追加到内置的 kanban-worker skill 之后

**创建工作区模式任务（自动创建 git worktree）：**
```bash
hermes kanban create "重构用户模块" --workspace worktree --branch wt/user-refactor
```

**设置运行时上限：**
```bash
hermes kanban create "大数据分析" --max-runtime 30m
```
- 支持格式：`90s`, `30m`, `2h`, `1d`
- 超出上限后调度器 SIGTERM → SIGKILL worker，任务重新排队

**创建草稿（等待完善）：**
```bash
hermes kanban create "待定需求" --triage
```
- 需要后续用 `hermes kanban specify t_xxx --body "..."` 完善后 promote

---

## Dashboard 自动启动

Dashboard 可配置为 systemd 用户服务，随系统开机自启。详情见 `references/dashboard-systemd-service.md`。

```bash
systemctl --user status hermes-dashboard
```

---

## 安装与初始化（Setup）

### 首次初始化

```bash
# 初始化 KANBAN 数据库（自动创建 ~/.hermes/kanban.db）
hermes kanban init
```

`kanban init` 会尝试将 bundled skills（如 `kanban-worker`）同步到当前 profile。

### 修复"Unknown skill(s): kanban-worker"错误

如果 dispatcher 派发 worker 时失败，日志显示 `Error: Unknown skill(s): kanban-worker`，说明该技能未同步到 profile。手动复制：

```bash
# 检查技能是否存在
hermes skills list | grep kanban-worker

# 如缺少则手动复制
cp -r ~/.hermes/hermes-agent/skills/devops/kanban-worker ~/.hermes/skills/devops/
```

然后重新调度任务。

### 面板健康检查

```bash
hermes kanban diag      # 快速诊断面板健康度
hermes kanban boards    # 查看所有面板
```

---

## ⚠️ 常见陷阱（Pitfalls）

### 1. `--priority` 是整数，不是字符串

```bash
# ❌ 错误
hermes kanban create "任务" --priority high

# ✅ 正确
hermes kanban create "任务" --priority 1
```
优先级数字越小越优先，纯用于排序，无标签语义。

### 2. `comment` 用位置参数，不是 `--body`

```bash
# ❌ 错误
hermes kanban comment t_xxx --body "评论"

# ✅ 正确
hermes kanban comment t_xxx "评论"
```

### 3. `assign` 用位置参数，不是 `--assignee`

```bash
# ❌ 错误
hermes kanban assign t_xxx --assignee default

# ✅ 正确
hermes kanban assign t_xxx default
```
要取消认领：`hermes kanban assign t_xxx none`

### 4. KANBAN 工具集默认不可见

执行 `hermes tools list` 看不到 `kanban` 工具集——这是设计如此。工具集仅在以下两种情况加载：
- 环境变量 `HERMES_KANBAN_TASK` 被设置（调度器派发的 worker）
- `toolsets` 配置中显式包含 `kanban`（orchestrator profile）

正常 `hermes chat` 会话无 kanban 工具，但 CLI 命令 `hermes kanban` 始终可用。

### 5. 调度器在 gateway 中而非 CLI 中运行

KANBAN 调度器默认内嵌在 gateway 进程，每 60 秒扫描一次。gateway 不运行时，不会自动派发任务。配置：
```yaml
kanban:
  dispatch_in_gateway: true
  dispatch_interval_seconds: 60
```

### 6. 任务重试与熔断

- 默认失败重试 2 次（通过 `kanban.failure_limit` 配置）
- 连续失败超过限制后任务自动进入 blocked 状态
- 可通过 `--max-retries N` 按任务覆写
- **调度器自动重试**：如果 worker 进程 crash（如缺少依赖），dispatcher 会自动 claim 并重试（run #2 crash → run #3 auto-spawned）
- 重试后 worker 应通过 `kanban_show` 检查前序 run 的 `outcome` / `summary` / `error` 避免重复失败路径

### 7. Worker 是无头进程，不能问问题

Worker 在后台运行，**没有真人实时对话**。以下操作会导致任务卡住：

```python
# ❌ 错误 — worker 里没有听众，会 timeout
clarify(question="请确认是否执行？")

# ✅ 正确 — 用 block 让人工介入
kanban_comment(body="执行计划已准备，需要确认：...")
kanban_block(reason="请确认是否执行方案C？")
```

阻断后人工 `unblock` 会触发新的 worker 运行，通过评论线程获取答复。

### 8. Goal-mode worker 解阻塞后可能重新询问而非直接执行

**现象：** 任务 blocked 后，人工 `unblock` 并附上明确指示（如"选方案C"），但新 worker 重新读取上下文后依然 output 同样的方案选项请求确认，而非直接执行。

**原因：** goal-mode worker 每次启动都重新分析任务上下文，如果 `block reason` 和 comments 中的信息较为丰富（列出多个选项），worker 可能把这些选项解读为"待决策"而非"已决策"，从而再次阻塞。

**解决：**
```bash
# ❌ 不明确 — 解阻塞信息模糊，worker 会再分析
hermes kanban unblock t_xxx

# ✅ 在 unblock 时直接指定方案
hermes kanban unblock t_xxx "选方案C：Nginx + Caddy并存，立即执行"

# ✅ 更可靠 — 先在评论中明确指示，再 unblock
hermes kanban comment t_xxx "已决定选方案C，请直接执行：安装 Nginx + 优化 Caddy"
hermes kanban unblock t_xxx
```

**推荐做法：** 在 `kanban block reason` 中直接写明"如果选择X方案，unblock时直接告知即可"，或者在 body 中预埋执行计划，减少 worker 二次分析时的歧义。

### 9. sudo 命令在 worker 中不可执行

```bash
# ❌ worker 执行这个会失败（no password was provided）
sudo apt install -y nginx

# ✅ 方案A：worker 应检测到需要 sudo，记录步骤到评论，block 让人工执行
kanban_comment(body="请执行以下命令：\nsudo apt install -y nginx")
kanban_block(reason="需要人工执行 3 条 sudo 命令，见评论")

# ✅ 方案B：直接在 task body 中写明步骤，人工看到 block 后手动执行再 complete
```

**最佳做法**：创建任务时如果预判涉及系统级操作，在 body 中写明需要人工配合的步骤。

---

## 调度器行为

内嵌在 gateway 中的 dispatcher 每 `dispatch_interval_seconds`（默认 60s）执行：

1. 扫描 ready 状态且 assignee 非空的任务
2. 检查 assignee 当前 running 任务数是否超过 `max_in_progress_per_profile`
3. 原子性地 claim 任务（标记为 running）
4. 启动 worker 子进程（设置 `HERMES_KANBAN_TASK` 环境变量）
5. 监听 worker 的心跳和完成信号
6. 超时未完成 → SIGTERM → SIGKILL，任务重新排队
7. 回收超时的 running 任务（`dispatch_stale_timeout_seconds`，默认 4h）

### 自动分解（auto_decompose）

```yaml
kanban:
  auto_decompose: true        # 自动将复杂任务拆解为子任务
  auto_decompose_per_tick: 3  # 每 tick 最多分解 3 个
```
创建任务时系统会自动生成子任务分解建议，适用于大任务拆解。

---

## 完整工作流示例（真实案例）

以下展示一次完整的 KANBAN 任务从创建到阻塞的生命周期，基于真实会话记录。

### 1. 创建任务（goal 模式）
```bash
hermes kanban create "优化 Nginx 配置" --goal --body "检查当前配置，给出优化建议并应用" --priority 1
# → Created t_f49c5f2b (ready, assignee=-)
```

### 2. 认领并手动派发
```bash
# 认领任务
hermes kanban assign t_f49c5f2b default

# 预览派发（dry-run）
hermes kanban dispatch --dry-run
# → Spawned: 1  (t_f49c5f2b -> default)

# 执行派发
hermes kanban dispatch
# → Spawned: 1  (t_f49c5f2b -> default @ workspace)
```

### 3. 自动重试（worker crash 场景）
如果首次派发时 worker 进程 crash（如缺少 `kanban-worker` 技能），dispatcher 会自动 claim 并重试。任务日志显示：
```
# run #2 crashed  →  dispatcher 自动 claim →  run #3 spawned
```

### 4. 查看 Worker 执行状态
```bash
# 查看任务状态（running/blocked/done）
hermes kanban list

# 查看运行记录详情
hermes kanban show t_f49c5f2b
```
Worker 日志位置：`~/.hermes/kanban/logs/t_xxxxxxxx.log`

### 5. 阻塞场景：worker 发现意外条件
当 worker 发现系统实际使用 Caddy 而非 Nginx，优雅阻塞：
1. 将详细分析写入工作区文件
2. 在评论中记录发现
3. 调用 `kanban_block` 给出选项

```
# 阻塞后的面板状态
⊘ t_f49c5f2b  blocked  default  优化 Nginx 配置

# block reason 包含问题描述和选项
Nginx 未安装，系统运行的是 Caddy。需要确认操作方向：
  A) 优化现有 Caddy 配置（推荐）
  B) 安装 Nginx 替代 Caddy
  C) 安装 Nginx 并存
```

### 6. 处理阻塞任务（人工介入）
```bash
# 查看完整详情和评论
hermes kanban show t_f49c5f2b

# 在评论中指示方向
hermes kanban comment t_f49c5f2b "选方案A，优化 Caddy 配置"

# 解除阻塞 → 触发新的 worker 执行
hermes kanban unblock t_f49c5f2b
```

### 7. 完成任务
```bash
hermes kanban complete t_f49c5f2b
hermes kanban stats      # 查看统计
hermes kanban archive t_f49c5f2b  # 归档完成的任务
```

---

## 相关路径

| 资源 | 路径 |
|------|------|
| KANBAN 数据库 | `~/.hermes/kanban.db` |
| Worker 日志 | `~/.hermes/logs/kanban-worker-*.log` |
| 调度器配置 | `config.yaml` → `kanban.*` |
| 工具集定义 | `toolsets.py` → `"kanban"` |

Worker 日志自动轮转，按 `worker_log_rotate_bytes`（默认 2MB）和 `worker_log_backup_count`（默认 1 个备份）管理。

---

## KANBAN 工具集参考

对于被派发的 worker，可用的工具包括：

| 工具 | 用途 |
|------|------|
| `kanban_show` | 查看当前任务详情 |
| `kanban_list` | 查看面板任务列表 |
| `kanban_complete` | 标记任务完成 |
| `kanban_block` | 标记任务阻塞 |
| `kanban_unblock` | 解除阻塞 |
| `kanban_heartbeat` | 发送心跳（长任务） |
| `kanban_comment` | 添加评论 |
| `kanban_create` | 创建子任务 |
| `kanban_link` | 关联其他任务 |

---

## 完整配置参考

```yaml
kanban:
  dispatch_in_gateway: true            # 在 gateway 中内嵌调度器
  dispatch_interval_seconds: 60        # 调度扫描间隔
  failure_limit: 2                     # 连续失败熔断阈值
  worker_log_rotate_bytes: 2097152     # worker 日志轮转大小(2MB)
  worker_log_backup_count: 1           # 日志备份数
  orchestrator_profile: ''             # 默认编排器 profile
  default_assignee: ''                 # 默认认领人
  max_in_progress_per_profile: null    # 每个 profile 最大并行数
  auto_decompose: true                 # 自动分解任务
  auto_decompose_per_tick: 3           # 每 tick 分解数
  dispatch_stale_timeout_seconds: 14400 # 超时回收(4h)
```

---

## 最佳实践

1. **先创建，后 assign** — 创建时不指定 assignee，review 后再分配
2. **用 `--goal` 处理复杂任务** — 比一次性 prompt 效果好，worker 会迭代完善
3. **评论记录决策** — 用 `comment` 记录为什么这么做，方便后续回溯
4. **关联子任务** — 大任务用 `--parent` 关联，面板自动分组
5. **检查后端状态** — `hermes kanban diag` 快速诊断面板健康度

---

## Worker Deep Dive (absorbed from kanban-worker)

The following section covers worker-specific behavior, handoff shapes, retry diagnostics, and edge cases for agents running as dispatched workers.

### Workspace Handling

| Kind | What it is | How to work |
|---|---|---|
| `scratch` | Fresh tmp dir, yours alone | Read/write freely; GC'd when task archived |
| `dir:<path>` | Shared persistent directory | Other runs read what you write. Treat like long-lived state. Path is guaranteed absolute. |
| `worktree` | Git worktree | If `.git` doesn't exist, run `git worktree add <path> ${HERMES_KANBAN_BRANCH:-wt/$HERMES_KANBAN_TASK}` from the main repo first. Commit work here. |

### Tenant Isolation

If `$HERMES_TENANT` is set, prefix memory entries with the tenant so context doesn't leak: `business-a: Acme is our biggest customer`.

### Good `kanban_complete` Handoff Shapes

**Coding task:**
```python
kanban_complete(
    summary="shipped rate limiter — token bucket, keys on user_id with IP fallback, 14 tests pass",
    metadata={
        "changed_files": ["rate_limiter.py", "tests/test_rate_limiter.py"],
        "tests_run": 14, "tests_passed": 14,
        "decisions": ["user_id primary, IP fallback for unauthenticated requests"],
    },
)
```

**Coding task needing human review (review-required):** For most code-changing tasks, block instead of complete. Drop structured metadata into a comment first, then block with reason prefixed `review-required: `:
```python
kanban_comment(body="review-required handoff:\n" + json.dumps({...}, indent=2))
kanban_block(reason="review-required: rate limiter shipped, 14/14 tests pass — needs eyes before merging")
```

**Research task:**
```python
kanban_complete(
    summary="3 competing libraries reviewed; vLLM wins on throughput",
    metadata={"sources_read": 12, "recommendation": "vLLM", "benchmarks": {"vllm": 1.0, "sglang": 0.87}},
)
```

### Claiming Cards You Actually Created

If your run produced new kanban tasks via `kanban_create`, pass the ids in `created_cards` on `kanban_complete`. Only list ids captured from a successful `kanban_create` return value — never invent ids. If a create call failed, the card was NOT created.

```python
c1 = kanban_create(title="remediate SQL injection", assignee="security-worker")
kanban_complete(summary="Review done", created_cards=[c1["task_id"]])
```

### Block Reasons That Get Answered Fast

Bad: `"stuck"` — the human has no context.  
Good: one sentence naming the specific decision needed. Leave longer context as a comment:

```python
kanban_comment(body="Full context: I have user IPs from Cloudflare headers...")
kanban_block(reason="Rate limit key choice: IP (simple, NAT-unsafe) or user_id (requires auth)?")
```

### Heartbeats

Good: `"epoch 12/50, loss 0.31"`, `"scanned 1.2M/2.4M rows"`.  
Bad: `"still working"`, empty notes, sub-second intervals. Every few minutes max; skip for tasks under ~2 minutes.

### Retry Scenarios

If `kanban_show` returns prior runs:
- `outcome: "timed_out"` → chunk the work or shorten it
- `outcome: "crashed"` → OOM or segfault; reduce memory footprint
- `outcome: "spawn_failed"` → profile config issue; `kanban_block`, don't retry blindly
- `outcome: "reclaimed"` → operator archived the task; check status carefully
- `outcome: "blocked"` → read the unblock comment in the thread

### Notification Routing

Configure cross-profile notifications via `notification_sources` in `~/.hermes/config.yaml`:
- `notification_sources: ['*']` — accept from all profiles
- `notification_sources: ['default', 'zilor-ppt']` — restrict to specific profiles

### Worker Do NOT

- Call `delegate_task` as substitute for `kanban_create` — use `kanban_create` for cross-agent handoffs
- Call `clarify` — there is no live user; use `kanban_comment` + `kanban_block` instead
- Modify files outside `$HERMES_KANBAN_WORKSPACE` unless the task body says to
- Create follow-up tasks assigned to yourself — assign to the right specialist
- Complete a task you didn't actually finish — block it instead
- Rely on `hermes kanban <verb>` CLI from terminal tool — use the `kanban_*` tools; CLI may not be installed in containerized backends

### CLI Fallback (for scripting)

Every tool has a CLI equivalent: `kanban_show` ↔ `hermes kanban show <id> --json`, `kanban_complete` ↔ `hermes kanban complete <id> --summary "..." --metadata '{...}'`, etc. Use the tools from inside an agent; the CLI exists for the human at the terminal.
