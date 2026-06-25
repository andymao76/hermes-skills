---
name: dify-dsl
description: "Create Dify DSL (.dify.yml) workflow definition files — 15 node types, 4 templates, layout calculation, 8 schema traps. Merged from workflow-skill (LingyiChen-AI) v1.3.0."
version: 1.4.0
tags: [dify, dsl, workflow, workflow-engine, ai-applications, no-code, tavily, coze, comfyui]
---

# Dify DSL — Workflow Definition Files

Create Dify DSL (Domain Specific Language) workflow files in YAML format that can be imported into Dify Studio. Use this when the user asks for a Dify workflow, chatflow, or DSL file.

**Source:** Merged from [LingyiChen-AI/workflow-skill](https://github.com/LingyiChen-AI/workflow-skill) — tracked against dify-api **1.13.3**, DSL **0.6.0**.

## Reference Files (Imported from workflow-skill)

This skill now includes complete node schemas, templates, and format references:

| Resource | Path | Content |
|----------|------|---------|
| DSL Format | `references/dsl-format.md` | Complete DSL structure with all fields |
| Edge & Layout | `references/edge-and-layout.md` | Edge rules, handle naming, layout calculation |
| Node Schemas (15) | `references/nodes/*.md` | Per-node full field specification |
| Templates (6) | `templates/*.yml` | Chatbot / RAG / Agent / Translation / Deep Research / Task Iteration |
| Examples (2) | `examples/*.yml` | Simple chatbot / RAG with rerank |
| Community Patterns | `references/community-workflow-patterns.md` | UUID IDs, conversation_vars, 0.1.5 format, cascade patterns |
| Awesome-Dify-Workflow Picks | `references/awesome-dify-workflow-picks.md` | 7精选模板分析: Agent工具调用/搜索大师/Deep Researcher/翻译等 |

Also see `~/projects/github-workspace/` for cloned community workflow repos (Awesome-Dify-Workflow 46 YAMLs, Open-Deep-Research).

### Dify Platform Administration (absorbed from dify-admin)

For self-hosted Dify (Docker Compose) operations — container management, password reset, API authentication, app testing, model provider config, and SSE event stream diagnostics — see `references/ssh-tunnel-expose-local-dify.md` for the SSH tunnel exposure guide. Key admin commands:

```bash
cd ~/dify/docker
docker compose ps                    # container status
docker compose logs --tail=50 api    # API logs
docker exec docker-db_postgres-1 psql -U postgres -d dify -c "SELECT email, name, status FROM accounts;"  # list accounts
```

Password reset uses PBKDF2-HMAC-SHA256 (not bcrypt). Login API: POST `/console/api/login` with base64-encoded password. API calls need both cookie-based auth AND `X-CSRF-TOKEN` header from the `csrf_token` cookie.

Workflow/chat testing endpoints:
- advanced-chat: `POST /console/api/apps/{id}/advanced-chat/workflows/draft/run`
- workflow: `POST /console/api/apps/{id}/workflows/draft/run`

Response is SSE event stream — use `curl -s -N` for streaming. Diagnose failures by finding first `node_finished` with `status: "failed"`.

## Awesome-Dify-Workflow 精选模板

The `references/awesome-dify-workflow-picks.md` file catalogs 7 top templates from the Awesome-Dify-Workflow repo:

| # | Template | Type | Nodes | Best For |
|---|----------|------|-------|----------|
| 1 | Agent工具调用 | FC Agent | 3 | Multi-tool chat assistants |
| 2 | 搜索大师 | Deep Research | ~10 | Multi-phase web research |
| 3 | Deep Researcher | Multi-turn Research | 30+ | Structured research Q&A |
| 4 | 宝玉的英译中优化版 | Translation | 3 | High-quality EN→CN with 3-step refinement |
| 5 | translation_workflow | Translation | 6 | Country-adaptive translation |
| 6 | MCP | MCP Agent | 3 | MCP FunctionCalling integration |
| 7 | 全书翻译 | Book Translation | 7 | Long-document chunked translation |

See the full reference file for complete analysis including architecture diagrams, key techniques, and code snippets.

## Smart Interaction Logic

Before generating, assess if the user's description is sufficient:

**Proceed directly** if the description includes clear input/output expectations and processing logic.

**Ask clarifying questions** (max 3 rounds) if unclear:
1. "What inputs/outputs?"
2. "What processing steps? (LLM call, knowledge retrieval, API call, conditional logic)"
3. "Any specific models, tools, or knowledge bases?"

## Node Router Table (15 Types)

| Node | Type Key | Purpose | Schema File |
|------|----------|---------|-------------|
| Start | `start` | Entry point; defines input variables | `references/nodes/start.md` |
| End | `end` | Terminal node for Workflow; declares outputs | `references/nodes/end.md` |
| Answer | `answer` | Streams response in Chatflow mode | `references/nodes/answer.md` |
| LLM | `llm` | Invokes a large language model | `references/nodes/llm.md` |
| Knowledge Retrieval | `knowledge-retrieval` | Searches knowledge bases | `references/nodes/knowledge-retrieval.md` |
| Code | `code` | Executes Python3/JS/JSON code | `references/nodes/code.md` |
| HTTP Request | `http-request` | Makes HTTP API calls | `references/nodes/http-request.md` |
| If/Else | `if-else` | Conditional branching (IF/ELIF/ELSE) | `references/nodes/if-else.md` |
| Variable Aggregator | `variable-aggregator` | Merges variables from multiple branches | `references/nodes/variable-aggregator.md` |
| Iteration | `iteration` | Loops over array, runs sub-graph per element | `references/nodes/iteration.md` |
| Document Extractor | `document-extractor` | Extracts text from uploaded files | `references/nodes/document-extractor.md` |
| Template Transform | `template-transform` | Renders Jinja2 templates | `references/nodes/template-transform.md` |
| Question Classifier | `question-classifier` | Routes by classifying input via LLM | `references/nodes/question-classifier.md` |
| Parameter Extractor | `parameter-extractor` | Extracts structured params via LLM | `references/nodes/parameter-extractor.md` |
| Tool | `tool` | Invokes external tools (built-in/API/MCP) | `references/nodes/tool.md` |

## Generation Flow

1. **Parse requirement** — Identify the app mode (`workflow` or `advanced-chat`), needed nodes, data flow.
   - `workflow` mode (Start→End) for batch processing
   - `advanced-chat` mode (Start→Answer) for conversational chatbots

2. **Select nodes** from the router table above. Load the corresponding schema file for each selected node.

3. **Check template match** — If the requirement closely matches a known pattern, start from a template:

   | Template | Path | Matches When |
   |----------|------|-------------|
   | Chatbot | `templates/chatbot.yml` | Simple conversational bot: Start → LLM → Answer |
   | RAG | `templates/rag.yml` | Knowledge-base Q&A: Start → Knowledge Retrieval → LLM → Answer |
   | Agent | `templates/agent.yml` | Tool-using agent with question classification or parameter extraction |
   | Translation | `templates/translation.yml` | Text transformation/translation |
   | Deep Research | `templates/deep-research.yml` | Multi-level topic decomposition + iterative retrieval + structured report |
   | Task Iteration | `templates/task-iteration.yml` | Complex task → decompose → iterate each step → summarize |

4. **Assemble from schemas** — If no template matches, build nodes individually. For each node:
   - Generate a unique ID (13-digit timestamp string, e.g. `"1711536487001"`)
   - Fill required fields per the node schema
   - Use `{{#nodeId.variableName#}}` syntax for variable references
   - Use `{{#sys.query#}}` for system query variable in chatflow mode

5. **Generate edges** — Connect nodes following `references/edge-and-layout.md`:
   - Edge ID: `{sourceId}-{sourceHandle}-{targetId}-{targetHandle}`
   - Standard sourceHandle: `"source"` for most nodes
   - If/Else branches: `"true"` (first case), case_id (elif), `"false"` (else)
   - Question Classifier branches: topic `id` as sourceHandle
   - targetHandle always `"target"`
   - All edges use `type: "custom"` and `zIndex: 0` (or `1002` inside iterations)

6. **Calculate layout positions** — Place nodes on a left-to-right grid:
   - Start node at `{x: 80, y: 282}`
   - Horizontal spacing: 300px per step
   - Vertical spacing for parallel branches: 200px apart
   - Node width: 244px, height varies

7. **Output file** — Render as YAML. Validate structure completeness.

## DSL Structure

```yaml
version: "0.6.0"       # Must match CURRENT_APP_DSL_VERSION
kind: app
app:
  name: "Workflow Name"
  mode: "advanced-chat"   # or "workflow"
  description: "..."
  icon: "\U0001F916"
  icon_background: "#FFEAD5"
  icon_type: emoji
  use_icon_as_answer_icon: false
dependencies: []
workflow:
  environment_variables: []
  conversation_variables: []
  features:
    file_upload:
      enabled: false
    opening_statement: ""         # chatflow only
    retriever_resource:
      enabled: false
    sensitive_word_avoidance:
      enabled: false
    speech_to_text:
      enabled: false
    suggested_questions: []       # chatflow only
    suggested_questions_after_answer:
      enabled: false
    text_to_speech:
      enabled: false
  graph:
    nodes: []
    edges: []
    viewport:
      x: 0
      y: 0
      zoom: 0.7
```

## Version Discovery

**CRITICAL**: Always check the actual `CURRENT_APP_DSL_VERSION` from the source code. In Dify 1.13.3+ this is `"0.6.0"` defined in:
```
dify/api/constants/dsl_version.py
```
If you have local access to the Dify source (`~/dify/api/`), read it directly. If not, search GitHub.

**DSL version differences:**
| Version | Dify Version | Community Usage | Key Signs |
|---------|-------------|-----------------|-----------|
| **0.1.5** | < 1.13 | Awesome-Dify-Workflow (10.5k ⭐) | UUID node IDs, simpler features |
| **0.6.0** | 1.13.3+ | workflow-skill target | Timestamp IDs, richer features, graphon |

Dify imports both versions. When targeting an older instance, generate 0.1.5 format with UUIDs.

## Workflow vs Chatflow

| Aspect | Workflow | Chatflow (advanced-chat) |
|--------|----------|-------------------------|
| `mode` | `workflow` | `advanced-chat` |
| Terminal | End node | Answer node |
| Memory | No memory | Has conversation memory |
| `sys.query` | Not available | Available |
| Start node | Has `variables` (form-like) | Has `sys.query` built-in |

## Conversation Variables (Multi-Turn State)

Use `conversation_variables` for multi-turn data collection across user messages, especially in chatflow mode. Community workflows like Deep Research use this pattern extensively:

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
```

**Pattern**: LLM generates questions → stored in conversation_vars → user answers → stored → all vars used as context for final output.

**When to use**: questionnaires, multi-step research briefs, state that must persist across user turns, intermediate results shared by multiple downstream branches.

See `references/community-workflow-patterns.md` for the full Deep Research cascade pattern.

## Node ID Convention

Three formats, choose based on context:

- **UUID** (community standard for exported workflows): `"46b6620c-ea24-40e6-8389-49ea02b5cdef"`. Used by Awesome-Dify-Workflow (10k+ stars) and most community-exported YAMLs. Prefer this when modifying an existing exported workflow.
- **Numeric IDs** (recommended for fresh generation targeting Dify 0.6.0+): 13-digit timestamp, e.g. `"1711536487001"`. Increment by a few thousand between nodes.
- **String IDs**: `start-node`, `llm-node`, `answer-node` — works but less consistent with Dify exports.
- **Edge IDs**: `{sourceId}-{sourceHandle}-{targetId}-{targetHandle}`
- When uncertain which format to use, ask what Dify version the user is on and whether they're importing into an existing instance.

## Common Schema Pitfalls (Must Avoid)

These are the 8 most common mistakes that break Dify 0.6.0 DSL import:

1. **Variable shape differs per node type.**
   - `code`, `llm`, `template-transform`, `parameter-extractor` use **objects** with `value_selector:`
   - `variable-aggregator` uses **bare nested lists** (no value_selector wrapper)
   - `document-extractor` uses a singular `variable_selector` (flat array), not a list

2. **`memory` belongs only to chatflow LLM nodes.** In `workflow` mode, `sys.query` does not exist; LLM nodes must omit the `memory` block. Same for LLM nodes inside iterations in a workflow app.

3. **Iteration containers need dimensions in both places.** Set `width` and `height` both inside `data` and at the outer node level.

4. **Iteration child nodes** must declare `parentId: <iteration_id>`, `data.isInIteration: true`, `data.iteration_id: <iteration_id>`, and `zIndex: 1002`. Their `position` is relative to the iteration container.

5. **`iterator_input_type` must match the real element type.** For files: `"array[file]"`. For numbers: `"array[number]"`. Mismatch breaks runtime variable resolution.

6. **Plugin dependencies.** If you reference a model provider or tool provider not bundled with Dify, declare it in top-level `dependencies` so import flags missing plugins. Empty `dependencies: []` is fine when plugins are known installed.

7. **End node `outputs`** is a list of `{variable, value_selector, value_type}` items; **Code node `outputs`** is a dict keyed by variable name with `{type, children}` values. Do not mix.

8. **Edge `data` block** should include `sourceType`, `targetType`, `isInIteration`, `isInLoop`. Edges inside iteration also need `iteration_id` and `zIndex: 1002`.

## Plugin Dependencies

| Plugin | Provider String | Location |
|--------|----------------|----------|
| Tavily | `tavily/tavily` | Dify Plugin Marketplace |
| OpenAI | `langgenius/openai` | Dify Plugin Marketplace |
| DeepSeek | `langgenius/deepseek` | Pre-installed with Dify |
| JSON Process | `langgenius/json_process` | Dify Plugin Marketplace |
| Wikipedia | `langgenius/wikipedia` | Dify Plugin Marketplace |

Plugins MUST be installed **before** importing the DSL.

## Output Rules

- **Location**: final `.dify.yml` goes to **current working directory**; temp files to `/tmp/dify-workflow/`
- **Filename**: `<kebab-case-name>.dify.yml`
- **Format**: YAML only (`.dify.yml` or `.yml`). JSON is NOT accepted by Dify import.
- **All string node IDs** must be quoted in YAML to prevent type coercion.

## Provider Setup (User Must Do)

1. Tavily plugin: Dify → Plugins → Marketplace → Install "Tavily" → enter API Key
2. DeepSeek: Dify → Settings → Model Providers → DeepSeek → enter API Key
3. Any other models/providers referenced in LLM nodes

## Reference Workflows

- `references/tavily-deepseek-search-workflow.dsl` — Start → Tavily → LLM → Answer
- `examples/simple-chatbot.yml` — Minimal Start → LLM → Answer
- `examples/rag-with-rerank.yml` — Knowledge retrieval with reranking
