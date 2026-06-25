---
name: dify-workflow-dsl
description: "Generate importable Dify DSL (YAML) workflow files from natural language descriptions — correct schema structure, node types, edges, plugin references, and model configurations for Dify v1.x"
version: 1.0.0
author: assistant
license: MIT
tags: [Dify, DSL, Workflow, LLM, Chatflow, No-Code]
---

# Dify Workflow DSL Generation

Generate fully importable Dify DSL (`.yml`/`.yaml`) workflow files from natural language descriptions. Covers the correct YAML structure, node types, edge connections, plugin references, and model configurations needed for Dify v1.14+.

## Critical: DSL Format Requirements

**Dify DSL is ALWAYS YAML (`.yml`/`.yaml`), NEVER JSON.**

The `.dsl` extension is a convention but the file content must be YAML. Dify creates the file from its canvas export, so you must match its internal structure exactly.

## DSL File Structure

```yaml
app:
  description: "应用描述"
  icon: 🔍
  icon_background: '#D1E9FF'
  mode: advanced-chat          # advanced-chat (Chatflow) or workflow (Workflow)
  name: 应用名称
kind: app
version: 0.1.5                  # Schema version, not app version
workflow:
  conversation_variables: []     # Store per-conversation state
  environment_variables: []      # Global env vars
  features:
    file_upload:
      image:
        enabled: false
        number_limits: 3
        transfer_methods:
        - local_file
        - remote_url
    retriever_resource:
      enabled: true
    sensitive_word_avoidance:
      enabled: false
    speech_to_text:
      enabled: false
    suggested_questions: []
    suggested_questions_after_answer:
      enabled: false
    text_to_speech:
      enabled: false
    opening_statement: ''
  graph:
    edges:
    - id: edge-xxxxxxxxxxxxx    # unique edge ID
      source: 1749xxxxxxxxx     # source node ID
      target: 1749xxxxxxxxx     # target node ID
      sourceHandle: ...         # exact handle name from the node type
      targetHandle: ...         # exact handle name from the target
    nodes:
      # ... node definitions
  title: 应用名称
```

## Node Types and Handle Names

Each node type has specific handles. These MUST match exactly for Dify to parse the edges:

| Node Type | Source Handle | Target Handle | Notes |
|-----------|--------------|---------------|-------|
| **start** | `start-source` | — | Input variables listed under `variables` |
| **llm** | `llm-output` | `llm-input` | Model config under `llm_config` |
| **tool** | `tool-output` | `tool-input` | Tool provider under `tool_config` |
| **answer** | — | `answer-input` | Final output node |
| **code** | `code-output` | `code-input` | Python/JS code execution |
| **if-else** | `if-else-true`, `if-else-false` | `if-else-input` | Conditional branching |
| **variable-x** | `var-assigner-output` | `var-assigner-input` | Variable assignment |
| **variable-aggregator** | `var-aggregator-output` | `var-aggregator-input` | Collection/array assembly |
| **iteration** | `iteration-output` | `iteration-input` | Loop over arrays |

## Node ID Convention

Node IDs must be **numeric strings** (like `1749000000100`). These are Unix timestamp + sequence numbers. Convention:

- Start: `1749000000100`
- Tool: `1749000000200`
- LLM:  `1749000000300`
- Answer: `1749000000400`
- Next group: `1749000000500` etc.

Edge IDs use: `edge-1749000001000`, `edge-1749000001001`, etc.

## Common Node Configurations

### Start Node
```yaml
- data:
    title: 开始
    type: start
    variables:
    - allowed_roles:
      - user
      description: "输入描述"
      label: "输入标签"
      max_length: 500
      options: []
      required: true
      type: text-input
      variable: query
  height: 198
  id: "1749000000100"
  position:
    x: 80
    y: 50
  type: start
  width: 320
```

### Tool Node (e.g., Tavily Search)
```yaml
- data:
    title: Tavily 搜索
    type: tool
    tool_config:
      provider: tavily/tavily          # marketplace plugin format
      tool_name: tavily_search
      tool_parameters:
        query: "{{#1749000000100.query#}}"  # reference syntax
        search_depth: advanced
        include_answer: true
        include_raw_content: false
        include_images: false
        max_results: 5
      tool_provider: tavily
  height: 198
  id: "1749000000200"
  # ...
  type: tool
```

### LLM Node (e.g., DeepSeek)
```yaml
- data:
    title: DeepSeek 总结
    type: llm
    llm_config:
      model:
        provider: deepseek
        name: deepseek-chat            # model ID from Dify provider
        mode: chat
        completion_params:
          stop: []
          temperature: 0.7
          max_tokens: 4096
          top_p: 0.95
      prompt_config:
        system: |
          系统提示词内容
        pre_prompt: |
          用户问题：{{#1749000000100.query#}}
          搜索结果：{{#1749000000200.text#}}
        post_prompt: ''
      memory:
        enabled: true
        window:
          enabled: true
          size: 10
      context:
        enabled: false
      vision:
        enabled: false
  height: 298
  id: "1749000000300"
  # ...
  type: llm
```

### Answer Node (Final Output)
```yaml
- data:
    answer: "{{#1749000000300.text#}}"   # LLM output text
    title: 回答
    type: answer
  height: 118
  id: "1749000000400"
  # ...
  type: answer
```

## Variable Reference Syntax

Dify uses `{{#node_id.variable_name#}}` for cross-node references:

| Reference | Meaning |
|-----------|---------|
| `{{#1749000000100.query#}}` | Start node's input `query` |
| `{{#1749000000200.text#}}` | Tool node's default `text` output |
| `{{#1749000000300.text#}}` | LLM node's response text |
| `{{#1749000000500.result#}}` | Code node's output |

## Plugin Dependencies

Tavily and other marketplace plugins must be installed in Dify **before** importing the DSL. The DSL does NOT carry plugin installation — Dify will error if a referenced plugin is missing.

Common plugins and their provider strings:

| Plugin | Provider String | Install Location |
|--------|----------------|-----------------|
| Tavily | `tavily/tavily` | Dify Plugin Marketplace |
| OpenAI | `langgenius/openai` | Dify Plugin Marketplace |
| DeepSeek | `langgenius/deepseek` | Pre-installed with Dify |
| JSON Process | `langgenius/json_process` | Dify Plugin Marketplace |
| Wikipedia | `langgenius/wikipedia` | Dify Plugin Marketplace |

## Workflow vs Chatflow

| Aspect | Workflow | Chatflow (advanced-chat) |
|--------|----------|-------------------------|
| `mode` | `workflow` | `advanced-chat` |
| Memory | No memory | Has conversation memory |
| `sys.query` | Not available | Available |
| Use case | Batch processing, backend | Multi-turn conversation |
| Start node | Has `variables` (form-like) | Has `sys.query` built-in |

## Pitfalls

- **JSON instead of YAML**: Dify DSL MUST be YAML. JSON files will fail to import silently.
- **Wrong handle names**: Using generic names like `source`/`target` instead of exact handles like `start-source`/`tool-input` will cause broken edges.
- **Missing `kind: app`**: The top-level `kind: app` field is required.
- **Missing `version`**: Must be present at top level.
- **Plugin not installed**: If the DSL references a plugin not installed in Dify, import fails with no clear error. Always tell the user to install plugins first.
- **Node ID collisions**: Each node ID must be unique. Use timestamp-based IDs to avoid collisions.
- **Provider name mismatch**: DeepSeek provider in Dify is `deepseek` (not `deepseek-chat`), while the model name IS `deepseek-chat`.
- **Tool output text**: The default output variable for tool nodes is `text`, not a custom key. LLM output is also `text`.
- Indentation: YAML is whitespace-sensitive. Node data indentation must be consistent.
- **Position coordinates**: `x: 80` first node, then increment y by ~250-300 for each subsequent node to avoid visual overlap.

## Reference File

A complete Tavily Search + DeepSeek Summary Chatflow DSL is saved as a reference:

- `references/tavily-deepseek-search-workflow.dsl` — working example covering Start → Tavily → LLM → Answer with correct handles, provider configs, and prompt setup. Import-ready after Tavily plugin is installed.
