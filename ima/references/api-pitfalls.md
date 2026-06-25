# IMA API Pitfalls & Verified Patterns

> Discovered during initial setup and testing, 2026-06-14

## Critical: Invalid Endpoints

### `openapi/list_docs` does NOT work
- Returns empty response (no error, just empty stdout)
- This is NOT a valid IMA API endpoint despite appearing in some examples
- **Use these instead:**
  - Notes: `openapi/note/v1/list_notebook` with `{"limit": 10}`
  - Knowledge base contents: `openapi/wiki/v1/get_knowledge_list` with `{"knowledge_base_id": "...", "limit": 50}`
  - Knowledge base search: `openapi/wiki/v1/search_knowledge` with `{"knowledge_base_id": "...", "query": "...", "limit": 20}`

### `openapi/wiki/v1/get_knowledge_base` requires `ids` array
- Error: `value must contain between 1 and 20 items` if `ids` is missing
- Must pass `{"ids": ["kb_id_1", "kb_id_2"]}` to get KB info

### `openapi/wiki/v1/get_addable_knowledge_base_list` requires `limit`
- Error: `value must be inside range (0, 50]` if limit is missing
- Must pass `{"limit": 50}`

## API Key Shell Escaping Issues

API keys often contain `/`, `+`, `=` (base64 characters). These cause shell parsing failures when passed via `$(cat file)` in bash one-liners:

```bash
# BROKEN — shell chokes on special chars in API key
API_KEY=*** ~/.config/ima/api_key) && curl -H "ima-openapi-apikey: $API_KEY" ...

# WORKS — use node.js to read files and make the request directly
node -e "
const fs = require('fs');
const clientId = fs.readFileSync(process.env.HOME + '/.config/ima/client_id', 'utf8').trim();
const apiKey = fs.readFileSync(process.env.HOME + '/.config/ima/api_key', 'utf8').trim();
fetch('https://ima.qq.com/openapi/note/v1/list_notebook', {
  method: 'POST',
  headers: { 'ima-openapi-clientid': clientId, 'ima-openapi-apikey': apiKey, 'Content-Type': 'application/json' },
  body: JSON.stringify({limit: 10}),
}).then(async r => console.log(await r.text()));
"
```

**Best practice**: Always use `node ima_api.cjs` which reads credentials from config files internally — avoids shell escaping entirely.

## "Shared With Me" Knowledge Bases — Not Supported

- The IMA OpenAPI does NOT expose "分享给我的知识库" (knowledge bases shared by others)
- `get_addable_knowledge_base_list` only returns the user's OWN knowledge bases
- `search_knowledge_base` only searches the user's own knowledge bases
- There is no API endpoint for listing or searching shared/received knowledge bases
- **Workaround**: User must manually check shared KBs in the IMA web/app interface

## Verified Working Endpoints (tested 2026-06-14)

| Endpoint | Method | Required Params | Notes |
|----------|--------|----------------|-------|
| `openapi/note/v1/list_notebook` | POST | `limit` (1-20) | Returns notebook list |
| `openapi/wiki/v1/get_knowledge_list` | POST | `knowledge_base_id`, `limit` | Lists KB contents |
| `openapi/wiki/v1/search_knowledge` | POST | `knowledge_base_id`, `query`, `limit` | Search within a KB |
| `openapi/wiki/v1/get_addable_knowledge_base_list` | POST | `limit` (1-50) | Lists user's own KBs |
| `openapi/wiki/v1/search_knowledge_base` | POST | `query`, `limit` | Search KB names |

## Credential Verification Quick Test

```bash
# Quick test — should return code:0 if credentials are valid
cd ~/.hermes/skills/ima && node ima_api.cjs "openapi/note/v1/list_notebook" '{"limit":5}' 2>/dev/null
# Expected: {"code":0,"msg":"success","data":{"note_folder_infos":[...],...}}
```

## Common Error Codes

| Code | Meaning | Fix |
|------|---------|-----|
| `51` | Parameter validation error | Check required params and value ranges |
| `220004` | `invalid knowledge_base_id` | Must pass valid KB ID from `get_addable_knowledge_base_list` |
| Empty response | Wrong endpoint or network issue | Verify endpoint path includes version (`/v1/`) |
