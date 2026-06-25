# Provider/Model Tool Calling Compatibility for Cron Jobs

Cron jobs that need to use agent tools (web_search, web_extract, etc.) require a model that supports **function calling** (tool use). Not all providers/models do, even if they produce text output.

## Compatibility Matrix (tested 2026-06-09)

| Provider | Model | Text Generation | Tool Calling | Notes |
|----------|-------|:---------------:|:------------:|-------|
| OpenRouter | anthropic/claude-sonnet-4 | ✅ | ✅ | **Recommended for cron jobs that need tools** |
| SiliconFlow (國際) | deepseek-ai/DeepSeek-V3 | ✅ | ❌ | Responds with "好的" and stops — no tool calls ever fired |
| SiliconFlow (國際) | Qwen/Qwen3.6-35B-A3B | ❌ (System msg error) | ❌ | "System message must be at the beginning" — incompatible with Hermes agent loop |

## Key Discovery

**"Test with text" is NOT enough.** A model can pass a simple "回复一句话：测试通过" test but STILL not support tool calling. The DeepSeek-V3 on SiliconFlow is a concrete example: it responds to text queries fine but exits immediately when asked to call tools.

**Correct test pattern for cron jobs:**
1. Test text connectivity: `hermes chat -q "简短测试" --provider PROVIDER --model MODEL -Q`
2. Test tool calling: `hermes chat -q "请用 web_search 搜索'今天头条新闻'并总结结果" --provider PROVIDER --model MODEL -Q`
   - If the model only says "好的" / "我来搜索" without actual tool execution → tool calling unsupported
   - If the model actually searches and returns results → tool calling works

## Recommended Configuration

For cron jobs that use web_search or other agent tools:

```yaml
# cronjob update
cronjob(
    action='update',
    job_id='...',
    model={"provider": "openrouter", "model": "anthropic/claude-sonnet-4"}
)
```

OpenRouter Claude Sonnet 4 supports full tool calling and has lenient content policies (no "Content Exists Risk" blocks).

## Workflow: Test First, Then Update

When switching a cron job's model/provider to fix failures:

1. **Test in current session**: Use `hermes chat -q` with the actual task prompt and target model
2. **Verify tool calling works**: Check that web_search / other tools are actually executed
3. **Verify format**: For multi-platform delivery (telegram,discord), ensure the output format is clean
4. **Update the job**: Only after all tests pass
5. **Trigger one manual run**: `cronjob(action='run', job_id='...')`
6. **Verify delivery**: Check `agent.log` for "delivered to" lines and cron list for `last_status: ok`
