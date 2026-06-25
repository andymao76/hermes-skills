# Community Workflow Patterns

Discovered by analyzing 49 community DSL workflows from the top 10k-star Dify workflow repos (cloned locally).

## Local Reference Repos

| Repo | Path | DSL Count | Key Insight |
|------|------|-----------|-------------|
| Awesome-Dify-Workflow | `~/projects/github-workspace/Awesome-Dify-Workflow/DSL/` | 46 YAMLs | Most popular community patterns, across 9 categories. See `references/awesome-dify-workflow-picks.md` for 7精选模板分析 |
| Open-Deep-Research-workflow-on-Dify | `~/projects/github-workspace/Open-Deep-Research-workflow-on-Dify/` | 1 YAML (100KB) | Deep Research cascade architecture |

---

## 1. UUID Node IDs (Community Standard)

Community-exported Dify workflows do NOT use 13-digit timestamps. They use UUID v4:

```yaml
nodes:
  - id: "46b6620c-ea24-40e6-8389-49ea02b5cdef"
    type: custom
    data:
      type: start
      title: Start
```

Edge IDs also use UUIDs:

```yaml
edges:
  - id: "46b6620c-ea24-40e6-8389-49ea02b5cdef-source-96b85891-ba39-40e4-9a16-fe2fb2b8ba18-target"
    source: "46b6620c-ea24-40e6-8389-49ea02b5cdef"
    target: "96b85891-ba39-40e4-9a16-fe2fb2b8ba18"
```

**When to use UUID vs Timestamp:**
- **UUID** — when matching the community export format, or when the user provides an exported workflow they want modified
- **Timestamp** — when generating from scratch for Dify 0.6.0+ import (the workflow-skill convention)

## 2. Conversation Variables for Multi-Turn State

The Deep Research workflow uses conversation variables extensively to track multi-turn user input across a structured research session:

```yaml
conversation_variables:
  - name: research_theme
    value_type: string
    value: ""
  - name: q1
    description: "第一个问题"
    value_type: string
    value: ""
  - name: query1
    description: "用户的第一个回答"
    value_type: string
    value: ""
  - name: q2
    value_type: string
    value: ""
  # ... up to 7+ variables
```

**Pattern: Question → Gather → Store → Report**
1. LLM node generates questions, stores in conversation_var `q1`
2. User answers, stored in conversation_var `query1`
3. Research phase reads all `query1..queryN` + `research_theme` as context
4. Report generation collates everything

**When to use conversation_variables:**
- Multi-turn data collection (questionnaires, interviews, research briefs)
- State that must persist across user messages in chatflow mode
- Intermediate results that multiple downstream branches need

## 3. DSL Format Version Differences

| Version | Usage | Key Differences |
|---------|-------|-----------------|
| **0.1.5** | Community-exported (Awesome-Dify-Workflow, older Dify) | UUID node IDs, simpler features section, no graphon |
| **0.6.0** | Current Dify 1.13.3+ (workflow-skill target) | Timestamp IDs, richer features, graphon-compatible |

**Backward compatibility:** Dify imports both versions. When generating for a user on an older Dify (< 1.13), prefer 0.1.5 format with UUIDs. When uncertain, ask which Dify version they're on.

## 4. 2>1 Model Cascade (Deep Research Pattern)

The cascade pattern from Open-Deep-Research-workflow-on-Dify:

```
Stage 1: Powerful model (Gemini 2.0 Flash)
  ├─ Topic decomposition into 4 research dimensions
  ├─ Generate targeted questions for each dimension
  └─ Extract subtopics

Stage 2: Multiple lighter model calls (DeepSeek R1 distill)
  ├─ Per-subtopic: retrieve + generate paragraph
  ├─ Uses conversation_variables for accumulated context
  └─ Each call is independent (parallelizable)

Stage 3: Structured report assembly
  └─ Collate all generated paragraphs into Markdown
```

**Key insight:** The "2>1" means: use 1 powerful model to plan/decompose → use many lighter model calls to execute. This is more cost-effective than using the powerful model for everything.

## 5. Community Pattern Categories (with Local Paths)

The Awesome-Dify-Workflow repo has 9 categories of ready-to-study patterns:

| Category | Example File | Pattern |
|----------|-------------|---------|
| Task Decomposition | `llm2o1.cn.yml` | Split → Iterate → Summarize |
| JSON Pipe | `json-repair.yml` | LLM output → JSON validator → JSON repair → Output |
| Translation Pipeline | `translation_workflow.yml` | 4-param input → LLM translate → Agentic refinement |
| Code Generation | `Python Coding Prompt.yml` | Chat → Code Generation with system prompt |
| Tool Agent | `Agent工具调用.yml` | FC-based tool calling with Dify 1.0 Agent |
| MCP Integration | `MCP-amap.yml` | MCP Agent strategy + external API |
| Memory Chat | `记忆测试.yml` | Short-term memory + CoT chain |
| Data Viz | `chart_demo.yml` | Data → ECharts rendering via answer |
| Course Generation | `dify_course_demo.yml` | Auto-generate full course materials |

All files are available at `~/projects/github-workspace/Awesome-Dify-Workflow/DSL/` for direct study.

## 6. Sandbox Notes

Several community workflows require a custom sandbox (`dify-sandbox-py`) for:
- matplotlib/pandas/numpy execution (official sandbox blocks these)
- File read/parse via Code node
- The stock sandbox error `operation not permitted` means switch to [dify-sandbox-py](https://github.com/svcvit/dify-sandbox-py)

Update `sandbox/dependencies/python-requirements.txt` and restart to add packages.
