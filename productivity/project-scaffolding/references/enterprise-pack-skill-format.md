# Enterprise Skill Pack — 3-File Skill Format Reference

## skill.yaml — Metadata + Workflow

Each skill in the pack has a `skill.yaml` with these standard fields:

```yaml
name: skill-name
description: "Brief description — triggers Hermes auto-loading"
version: "1.0.0"
author: "andymao"
triggers:
  - "keyword1"
  - "keyword2"
configuration:
  field: value
workflow:
  - step: "Step name"
    action: "What the agent should do"
    output: "Expected result"
crossReferences:
  - related-skill-name
```

Key rules:
- `name` must be lowercase with hyphens (FTS5 convention)
- `description` is what Hermes uses for automatic skill loading — make it searchable
- `triggers` are keywords the user might say
- `workflow` steps should be numbered and actionable

## prompt.md — Operational Guidance

The prompt file is what the model reads when loading the skill. It should contain:

1. **前置条件** — Prerequisites (tools, credentials, state)
2. **流程** — Step-by-step instructions with exact commands
3. **Pitfalls** — Common issues to avoid
4. **验证** — How to verify success

Keep it concise — this goes into the model's context every time.

## examples.md — Usage Scenarios

Concrete examples showing what the skill produces:

```
## 场景 1: xxx
输入: "xxx"
输出:
  - 结果A
  - 结果B

## 场景 2: yyy
输入: "yyy"
输出:
  - ...
```

Examples help the model understand the expected output format.

## Stub Skills

A stub skill is just `skill.yaml` with minimal fields — no `prompt.md` or `examples.md`. Use stubs when:

- The skill is planned but not yet fleshed out
- The user explicitly says "leave as placeholder"
- You're scaffolding the pack structure first

The stub should still have a meaningful `description` so Hermes can trigger-load it later.
