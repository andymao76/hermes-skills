version: "0.6.0"
kind: app
app:
  description: 使用 Tavily 搜索实时信息，DeepSeek 分析总结的网络搜索助手
  icon: 🔍
  icon_background: "#D1E9FF"
  icon_type: emoji
  mode: advanced-chat
  name: AI 网络搜索助手
  use_icon_as_answer_icon: false
workflow:
  conversation_variables:
    - id: cv-001
      value: ""
      value_type: string
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
    opening_statement: ""
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
      - data:
          sourceType: start
          targetType: tool
        id: edge-start-to-tavily
        source: start-node
        sourceHandle: start-source
        target: tavily-node
        targetHandle: tool-input
      - data:
          sourceType: tool
          targetType: llm
        id: edge-tavily-to-llm
        source: tavily-node
        sourceHandle: tool-output
        target: llm-node
        targetHandle: llm-input
      - data:
          sourceType: llm
          targetType: answer
        id: edge-llm-to-answer
        source: llm-node
        sourceHandle: llm-output
        target: answer-node
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
        id: start-node
        position:
          x: 100
          y: 50
        positionAbsolute:
          x: 100
          y: 50
        type: start
        width: 320
      - data:
          title: Tavily 搜索
          type: tool
          tool_config:
            provider: tavily/tavily
            tool_name: tavily_search
            tool_provider: tavily
            tool_parameters:
              query: "{{#start-node.query#}}"
              search_depth: advanced
              include_answer: true
              include_raw_content: false
              include_images: false
              max_results: 5
        height: 198
        id: tavily-node
        position:
          x: 100
          y: 320
        positionAbsolute:
          x: 100
          y: 320
        type: tool
        width: 320
      - data:
          title: DeepSeek 总结
          type: llm
          llm_config:
            completion_params:
              max_tokens: 4096
              stop: []
              temperature: 0.7
              top_p: 0.95
            memory:
              enabled: true
              window:
                enabled: true
                size: 10
            model:
              completion_params:
                stop: []
                temperature: 0.7
                max_tokens: 4096
                top_p: 0.95
              mode: chat
              name: deepseek-chat
              provider: deepseek
            prompt_config:
              pre_prompt: |
                用户问题：{{#start-node.query#}}

                搜索结果详情：{{#tavily-node.text#}}

                请基于以上搜索结果，用专业、有条理的方式回答用户的问题。
              system: |
                你是一个专业的AI搜索助手。你的任务是基于以下搜索结果，用中文清晰、有条理地回答用户问题。

                要求：
                1. 回答要包含具体的事实和数据
                2. 如果搜索结果提供的信息有限，要如实说明
                3. 使用标题和分段让回答结构清晰
                4. 在关键信息处标注引用来源的序号
                5. 最后提供信息来源列表
              post_prompt: ""
            context:
              enabled: false
            vision:
              enabled: false
        height: 358
        id: llm-node
        position:
          x: 100
          y: 600
        positionAbsolute:
          x: 100
          y: 600
        type: llm
        width: 320
      - data:
          answer: "{{#llm-node.text#}}"
          title: 回答
          type: answer
        height: 118
        id: answer-node
        position:
          x: 100
          y: 1040
        positionAbsolute:
          x: 100
          y: 1040
        type: answer
        width: 320
  title: AI 网络搜索助手
dependencies: []
