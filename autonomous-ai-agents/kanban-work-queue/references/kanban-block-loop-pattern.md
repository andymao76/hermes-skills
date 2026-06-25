# KANBAN Worker 阻塞循环问题

## 现象

Goal-mode 任务被 worker 阻塞（如"需要选择方案A/B/C"），人工 `unblock` 并附上明确指示（如"选方案C"），但新 worker（run #4）重新读取上下文后，依然 output 同样的方案选项请求确认，再次阻塞。

## 根因

1. **Goal-mode 每次重启都重新全量分析** — worker 不读取 unblock message 中的决策，而是重新扫描 task body / comments / block reason
2. **选项列表被解读为"待决策"而非"已决策"** — 当 block reason 中包含多个选项时，即使后续有 unblock comment，worker 仍然认为自己需要先确认
3. **Worker 无会话持久性** — 每个 run 都是全新会话，对之前的决策无记忆

## 复现步骤

1. 创建 goal-mode 任务
```bash
hermes kanban create "优化 Nginx 配置" --goal --body "检查配置并优化" --priority 1
```
2. Worker 发现异常条件（Nginx 未安装），阻塞并给出选项A/B/C
3. 人工 `comment` 指示方向 + `unblock`
4. Worker 重新启动 → 读 task body → 再次输出同样的选项 → 再次阻塞

## 解决方案

### 方案一：在 block reason 中植入决策触发器（推荐）

创建任务时，在 body/block reason 中预埋"决策点触发词"：

```
Block reason: 请确认选A（优化Caddy）还是选B（装Nginx）？
只要 unblock 时带有"选A"或"方案A"，worker 直接执行不重新分析。
```

### 方案二：修改 task body 后再 unblock

解阻塞前先 update task body 去掉选项，只保留确定的方案：

```bash
hermes kanban edit t_xxx --body "已决定：方案C — 安装 Nginx + 优化 Caddy，直接执行"
hermes kanban unblock t_xxx
```

> 注意：`hermes kanban edit` 需要确认语法，目前 CLI 可能不支持直接 edit body。替代方案：用 comment 明确指示 + 期望 worker 理解。

### 方案三：绕过 worker，人工执行

对于涉及 sudo 或复杂决策的任务，最可靠的方式是让 worker 输出执行计划后阻塞，人工根据计划手动执行步骤，再 complete 任务。

## 结论

KANBAN goal-mode 适合"自动推进但需要人类做关键决策"的场景，但 **block/unblock 循环超过 2 次后**，建议直接人工按计划执行，避免 worker 反复分析造成浪费。
