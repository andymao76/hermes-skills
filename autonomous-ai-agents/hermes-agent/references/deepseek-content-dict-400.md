# DeepSeek 400 - content is dict 案例

## 现象

2026-06-08 会话中，Hermes 调用 DeepSeek deepseek-chat 返回 HTTP 400：

```
HTTP 400: Failed to deserialize the JSON body into the target type: messages[12]: content should be a string or a list at line 1 column 43527
```

## 请求 Dump

文件：`/home/andymao/.hermes/sessions/request_dump_20260608_221148_a6bed3_20260608_221453_253764.json`

## 根因

`messages[12]` 的 content 是 dict 类型：

```json
{
  "role": "tool",
  "name": "brain_pinned_context",
  "content": {
    "content": [{"type": "text", "text": "{\n  \"absolute_path\": \"/home/andymao/Documents/Obsidian Vault/Brain/pinned.md\",\n  \"content\": \"\",\n  \"operation\": \"read\",\n  \"path\": \"Brain/pinned.md\",\n  \"present\": false\n}"}],
    "structuredContent": {
      "operation": "read",
      "present": false,
      "path": "Brain/pinned.md",
      "absolute_path": "/home/andymao/Documents/Obsidian Vault/Brain/pinned.md",
      "content": ""
    },
    "isError": false
  },
  "tool_call_id": "call_00_3XUiUGptBdV6E9N8HTVi4626"
}
```

`brain_pinned_context` 工具（Dep 封装）返回了带有 `structuredContent` 和 `isError` 字段的结构化 dict，但 `make_tool_result_message()` 没有将其序列化为字符串，直接作为 dict 传给了 DeepSeek。

## 检查结果

dump 中 14 条消息，仅 messages[12] 的 content 类型是 dict：

```
 0 system str
 1 system str
 2 user str
 3 assistant str
 4 tool str
 5 assistant str
 6 tool str
 7 assistant str
 8 tool str
 9 assistant str
10 user str
11 assistant str
12 tool dict  keys: ['content', 'structuredContent', 'isError']
13 user str
```

其余 13 条全是 str。

## 结论

这不是 API Key、余额、网络或代理问题。是 Hermes 请求体 message content 结构不兼容 DeepSeek。

## 修复位置

Hermes 需要在发送给 DeepSeek（以及所有不支持复杂 content 类型的 provider）前，在 `ProviderProfile.prepare_messages()` 或消息发送前处理中，对所有消息的 content 做强制字符串化。
