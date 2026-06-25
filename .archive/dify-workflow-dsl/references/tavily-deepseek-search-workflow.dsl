# Reference: Tavily Search + DeepSeek Summary Workflow DSL
# Generated: 2026-06-03
# Dify Version: 1.14.2
#
# This is a complete Chatflow (advanced-chat) that:
# 1. Takes a user query
# 2. Searches the web via Tavily (advanced depth, 5 results)
# 3. Summarizes findings using DeepSeek-chat
# 4. Returns a structured answer with source citations
#
# Prerequisites before importing:
# 1. Install Tavily plugin from Dify Plugin Marketplace
# 2. Configure DeepSeek model provider with API key
#
# Replace "tvly-你的TavilyAPIKey" with an actual Tavily API key
# in Step 2 of the import wizard, or configure it in Dify Settings
# before importing.

app:
  description: 使用 Tavily 搜索实时信息，DeepSeek 分析总结的网络搜索助手
  icon: 🔍
  icon_background: '#D1E9FF'
  mode: advanced-chat
  name: AI 网络搜索助手
kind: app
version: 0.1.5
workflow:
  conversation_variables:
  - id: 1749000000001
    value_type: string
    value: ''
    variable: search_query
  environment_variables: []
  features:
    file_upload:
      image:
        enabled: false
        number_limits: 3
        transfer_methods:
        - local_file
        - remote_url
    opening_statement: ''
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
  graph:
    edges:
    - id: edge-1749000001000
      source: 1749000000100
      target: 1749000000200
      sourceHandle: start-source
      targetHandle: tool-input
    - id: edge-1749000001001
      source: 1749000000200
      target: 1749000000300
      sourceHandle: tool-output
      targetHandle: llm-input
    - id: edge-1749000001002
      source: 1749000000300
      target: 1749000000400
      sourceHandle: llm-output
      targetHandle: answer-input
    nodes:
    - data:
        title: 开始
        type: start
        variables:
        - allowed_roles:
          - user
          description: 请输入你想搜索的问题
          label: 搜索问题
          max_length: 500
          options: []
          required: true
          type: text-input
          variable: query
      height: 198
      id: 1749000000100
      position:
        x: 80
        y: 50
      positionAbsolute:
        x: 80
        y: 50
      type: start
      width: 320
    - data:
        title: Tavily 搜索
        type: tool
        tool_config:
          provider: tavily/tavily
          tool_name: tavily_search
          tool_parameters:
            query: "{{#1749000000100.query#}}"
            search_depth: advanced
            include_answer: true
            include_raw_content: false
            include_images: false
            max_results: 5
          tool_provider: tavily
      height: 198
      id: 1749000000200
      position:
        x: 80
        y: 300
      positionAbsolute:
        x: 80
        y: 300
      type: tool
      width: 320
    - data:
        title: DeepSeek 总结
        type: llm
        llm_config:
          model:
            provider: deepseek
            name: deepseek-chat
            mode: chat
            completion_params:
              stop: []
              temperature: 0.7
              max_tokens: 4096
              top_p: 0.95
          prompt_config:
            system: |-
              你是一个专业的AI搜索助手。你的任务是基于以下搜索结果，用中文清晰、有条理地回答用户问题。

              要求：
              1. 回答要包含具体的事实和数据
              2. 如果搜索结果提供的信息有限，要如实说明
              3. 使用标题和分段让回答结构清晰
              4. 在关键信息处标注引用来源的序号
              5. 最后提供信息来源列表
            pre_prompt: |-
              用户问题：{{#1749000000100.query#}}

              搜索结果详情：{{#1749000000200.text#}}

              请基于以上搜索结果，用专业、有条理的方式回答用户的问题。
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
      id: 1749000000300
      position:
        x: 80
        y: 560
      positionAbsolute:
        x: 80
        y: 560
      type: llm
      width: 320
    - data:
        answer: "{{#1749000000300.text#}}"
        title: 回答
        type: answer
      height: 118
      id: 1749000000400
      position:
        x: 80
        y: 920
      positionAbsolute:
        x: 80
        y: 920
      type: answer
      width: 320
  title: AI 网络搜索助手
