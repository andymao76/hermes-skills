# _normalize_tool_content — Source Code

Imported from `provider-api-400-debugging` skill during consolidation (2026-06-08).

## Location

`agent/tool_dispatch_helpers.py` in hermes-agent codebase.

## Code

```python
def _normalize_tool_content(content: Any) -> Any:
    """Normalize tool result content to a string or standard OpenAI content list.

    OpenAI-compatible APIs require content to be either:
    - a plain string, or
    - a list of content parts (e.g. [{"type": "text", "text": "..."}])

    Tool implementations may return arbitrary Python objects (dicts, lists with
    non-standard keys, nested structures). This function coerces those into a
    stable wire-format representation before the message reaches the provider.

    Multimodal tool results (_multimodal=True) are detected by
    _is_multimodal_tool_result and returned as-is — they carry an
    OpenAI-compatible content list already.
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        # OpenAI-compatible content parts list — valid as-is
        return content
    if _is_multimodal_tool_result(content):
        # Multimodal envelope with content parts list — pass through
        return content
    # Any other dict or object — serialize to JSON string
    return json.dumps(content, ensure_ascii=False, default=str)
```

## Test Cases Verified 2026-06-08

| Input | Expected output type | Rationale |
|-------|-------------------|-----------|
| `None` | `str` (empty) | Provider rejects null |
| `"normal string"` | `str` (unchanged) | Already valid |
| `[]` | `list` (unchanged) | Empty content parts |
| `[{"type": "text", "text": "hello"}]` | `list` (unchanged) | Standard content parts |
| `42` | `str` (`json.dumps`) | Coerce non-standard type |
| `True` | `str` (`json.dumps`) | Coerce non-standard type |
| `{"key": "value"}` | `str` (`json.dumps`) | Plain dict → JSON string |
| brain_pinned_context result (dict with structuredContent) | `str` (`json.dumps`) | The original bug case |
