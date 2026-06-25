# Awesome-Dify-Workflow — 精选模板分析

Source: `~/projects/github-workspace/Awesome-Dify-Workflow/DSL/` (46 YAML files)

This document catalogs the 7 most valuable community DSL templates for reuse, reference, and learning.

---

## 1. Agent工具调用 — Multi-Tool Agent

| Field | Value |
|-------|-------|
| File | `Agent工具调用.yml` |
| Mode | `advanced-chat` |
| DSL | `0.1.5` |
| Nodes | 3 (Start → Agent → Answer) |
| Model | gpt-4o-mini (langgenius/openai) |
| Strategy | FunctionCalling Agent |
| Tools | Time (current_time), DuckDuckGo (ddgo_search), OpenWeather (weather) |

**Pattern:** A classic FunctionCalling Agent that decides which tool to use. The Agent node has the LLM decide between 3 built-in tools based on user intent.

**Key techniques:**
- Agent node with `agent_strategy_name: function_calling`
- Tools configured with both `llm` (auto-inferred by LLM) and `form` (manual) parameters
- Tool schemas fully specified: labels in 4 languages, parameter types, defaults
- DuckDuckGo tool set to 5 max results, `require_summary: 0` (LLM handles summarization)
- Weather tool with city auto-extraction + language/units selection
- Note: OpenWeather tool is `enabled: false` — user can enable as needed

**Best for:** Quick multi-tool chat assistants, prototyping tool-use agents.

---

## 2. 搜索大师 — Search Master (Multi-Phase Web Research)

| Field | Value |
|-------|-------|
| File | `搜索大师.yml` |
| Mode | `advanced-chat` |
| DSL | `0.1.0` |
| Nodes | ~10 (Start → LLM → Code → Iteration → Code → Iteration2 [HTTP→If/Else→Tool→Template] → Template → LLM → Answer) |
| Model | gpt-3.5-turbo-16k (LLM 1 + LLM 4) |

**Pattern:** A sophisticated multi-phase web research workflow. User asks question → LLM generates 3 follow-up questions → Iteration 1 searches each question via HTTP → Iteration 2 processes results with If/Else routing → Final LLM summarizes.

**Architecture:**
```
Start → LLM1(生成追问) → Code(拆分追问) → Iteration1(搜索各追问的URL)
     → Code2(提取URLs) → Iteration2(
         HTTP Request(获取URL内容) → If/Else(有结果? → Tool补搜)
       ) → Template(拼接结果) → LLM4(总结) → Answer
```

**Key techniques:**
- **Two-level iteration:** Outer iteration for question generation, inner for result processing
- **If/Else routing inside iteration:** If HTTP response is empty, route to DuckDuckGo tool to retry
- **URL extraction via Code node** using regex: `r'(https?://\\S+)'`
- **Template Transform** to concatenate accumulated results from iteration
- **LLM memory** carries follow-up questions + original query as context

**Best for:** Deep web research bots, question-expansion search, content aggregation.

---

## 3. Deep Researcher On Dify — Multi-Turn Research Cascade

| Field | Value |
|-------|-------|
| File | `Deep Researcher On Dify .yml` |
| Mode | `advanced-chat` |
| DSL | `0.1.5` |
| Conversation Vars | 15 (research_theme, q1-q4, query1-query4, Chat_Stage, Language, f1-f4) |
| Environment Vars | 2 (Generate, REASK) |
| Nodes | ~30+ (Start → If/Else → 5+ LLM branches → Parameter Extractors → Assigners → Iteration → Tools → Answer) |

**Pattern:** A comprehensive multi-turn research assistant. Starts by asking questions in 4 dimensions → collects user answers → researches each dimension → generates final report.

**Architecture:**
```
Start → If/Else(Chat_Stage routing)
  ├─ "Asking" → LLM(生成问题) → Parameter Extractor → Answer(展示问题)
  ├─ "Answering" → Assigner(存回答) → If/Else(所有问题答完?)
  │    ├─ No → next question → Answer
  │    └─ Yes → set Chat_Stage=Generate → LLM(研究主题扩展)
  └─ "Generate" → Parameter Extractor(提取搜索词) → Iteration(Tool搜索) → Assigner → Answer(报告)
```

**Key techniques:**
- **Conversation variables** for multi-turn state management (Chat_Stage state machine)
- **Parameter Extractor** nodes to extract structured data (research dimensions, questions)
- **Variable Assigner** nodes (type: `assigner`) to write conversation variables mid-flow
- **If/Else state machine** pattern using `Chat_Stage` conversation var
- **Opening statement** triggers language selection

**Best for:** Structured multi-turn research bots, survey/interview applications, deep-dive assistants.

---

## 4. 宝玉的英译中优化版 — 3-Step Translation Refinement

| Field | Value |
|-------|-------|
| File | `宝玉的英译中优化版.yml` |
| Mode | `workflow` |
| DSL | `0.1.0` |
| Nodes | 3 (Start → LLM → End) |
| Model | DeepSeek Chat (deepseek-chat) |
| Input | `content` (paragraph, max 50K chars) |

**Pattern:** Elegant single-LLM translation with a 3-step prompt: translate → reflect → refine. All in one LLM call with structured XML output.

**Key techniques:**
- **One-LLM, multi-step approach:** System prompt instructs the model to output 3 sections:
  - `<step1_initial_translation>` — raw translation
  - `<step2_reflection>` — self-critique with specific suggestions
  - `<step3_refined_translation>` — polished final version
- **Comprehensive system prompt** with:
  - URL/image/PDF handling instructions
  - 3-step translation strategy
  - Glossary of 12 AI/tech terms (AGI→通用人工智能, LLM→大语言模型, etc.)
  - Style guidance: 简体中文 colloquial, accuracy/fluency/style/terminology checks
- **End node** outputs the LLM's text field
- **Temperature: 1.1** for creative translation variety

**Best for:** High-quality English-to-Chinese translation, especially AI/tech content.

---

## 5. translation_workflow — Agentic Translation with Country Adaptation

| Field | Value |
|-------|-------|
| File | `translation_workflow.yml` |
| Mode | `workflow` |
| DSL | `0.1.0` |
| Nodes | 6 (Start → LLM → If/Else → [LLM 2 branches] → Variable Aggregator → LLM → End) |
| Model | DeepSeek Chat |
| Inputs | `source_text`, `source_lang`, `target_lang`, `country` (optional) |

**Pattern:** 吴恩达's Agentic Translation pattern — translate once, then refine based on whether the target country is specified.

**Architecture:**
```
Start(4 inputs) → LLM1(initial translation) → If/Else(country is null?)
  ├─ true:  → LLM2(standard polish)
  └─ false: → LLM3(country-adapted polish)
       → Variable Aggregator → LLM4(final output) → End
```

**Key techniques:**
- **4-parameter input** design: source_text, source_lang, target_lang, country (optional)
- **If/Else branching** on country emptiness — clean conditional refinement
- **Variable Aggregator** to merge branches before final LLM
- **Chained refinement** — LLM 2/3 does polish, LLM 4 does final assembly
- DeepSeek Chat model for cost-effective translation

**Best for:** Production translation pipelines requiring locale/regional adaptation.

---

## 6. MCP — MCP (Model Context Protocol) Agent Integration

| Field | Value |
|-------|-------|
| File | `MCP.yml` |
| Mode | `advanced-chat` |
| DSL | `0.1.5` |
| Nodes | 3 (Start → Agent → Answer) |
| Model | gpt-4o-mini (langgenius/openai) |
| Strategy | MCP FunctionCalling (`hjlarry/agent/mcp_agent`) |
| Plugin | `hjlarry/agent:0.0.1` |

**Pattern:** Demonstrates Dify's MCP (Model Context Protocol) integration. The agent uses an external MCP server as a tool provider.

**Key techniques:**
- **Agent node** uses `agent_strategy_provider_name: hjlarry/agent/mcp_agent` (not the built-in agent)
- **MCP Server URL** configured via `mcp_server` parameter pointing to `https://router.mcp.so/sse/...`
- **Regular built-in tool** (time) alongside MCP-provided capabilities
- **Plugin dependency** declared in `dependencies` block
- Same Time tool schemas as Agent工具调用 — shows reusable pattern

**Best for:** MCP-powered assistants that need access to external MCP servers.

---

## 7. 全书翻译 — Full-Book Translation with Chunked Iteration

| Field | Value |
|-------|-------|
| File | `全书翻译.yml` |
| Mode | `workflow` |
| DSL | `0.1.2` |
| Nodes | 7 (Start → Code → Iteration [3 LLMs inside: 识别专有名词→翻译→润色] → Template Transform → End) |
| Model | gpt-4o (Iteration inside) |

**Pattern:** Handles long documents by chunking with overlap, translating each chunk through 3 sequential LLM stages, then concatenating results.

**Architecture:**
```
Start(input_text) → Code(chunk by token_limit=1000, overlap=100)
  → Iteration(per chunk):
       LLM1(识别专有名词 → 术语表)
       LLM2(翻译 → 保留术语)
       LLM3(润色 → 最终文本)
  → Template Transform(concatenate all chunks) → End
```

**Key techniques:**
- **Code node** for text chunking: `token_limit=1000`, `overlap=100`, 6 chars/token estimate
- **Iteration** with 3 LLMs in series: Term Recognition → Translation → Polish
- **Multi-LLM pipeline inside iteration**: each chunk goes through all 3 stages
- **Vision enabled** for image content within documents
- **Template Transform** concatenates iteration output into single final text
- **End node** outputs final translated text

**Best for:** Full-book/batch translation, long-document processing with guaranteed coverage.

---

## Summary Table

| # | Template | Mode | Nodes | Model | Key Feature | Best For |
|---|----------|------|-------|-------|-------------|----------|
| 1 | Agent工具调用 | chat | 3 | gpt-4o-mini | Multi-tool FC Agent | Tool-using chat assistants |
| 2 | 搜索大师 | chat | ~10 | gpt-3.5-turbo | 2-level iteration + If/Else | Deep web research |
| 3 | Deep Researcher | chat | 30+ | varies | Conv vars state machine | Multi-turn research Q&A |
| 4 | 宝玉翻译优化版 | workflow | 3 | DeepSeek | 3-step single-LLM prompt | High-quality EN→CN |
| 5 | translation_workflow | workflow | 6 | DeepSeek | Country-adaptive branching | Agentic translation pipes |
| 6 | MCP | chat | 3 | gpt-4o-mini | MCP FunctionCalling strategy | MCP server integration |
| 7 | 全书翻译 | workflow | 7 | gpt-4o | Chunked iteration + 3-stage LLM | Long docs / full books |

## Honorable Mentions

| File | Why It's Interesting |
|------|---------------------|
| `DuckDuckGo翻译+LLM二次翻译.yml` | Tool-based translation (DuckDuckGo) → LLM refinement — token-efficient hybrid approach |
| `Dify 运营一条龙.yml` | Serial Template→HTTP→Code pipeline for automated content operations (104KB, 2781 lines) |
| `Document_chat_template.yml` | Full document chatbot with file upload → document extractor → question classifier → knowledge retrieval → LLM chain |
| `runLLMCode.yml` | LLM generates Python → Code node executes → output — code generation sandbox pattern |
| `Demo-tod_agent.yml` | To-do list agent using OpenAI plugin — shows plugin dependency declaration pattern |
