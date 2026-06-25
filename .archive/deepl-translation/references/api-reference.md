# DeepL API Technical Reference

## Endpoints

| Plan | Base URL |
|------|----------|
| Free | `https://api-free.deepl.com/v2/translate` |
| Pro | `https://api.deepl.com/v2/translate` |

## Authentication

Header: `Authorization: DeepL-Auth-Key <your-key>`

Key format (Free): `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx:fx`

## API Limits

| Limit | Value |
|-------|-------|
| Characters/month (Free) | 500,000 |
| Reset day | 14th of each month |
| Request body max | 128 KiB |
| Texts per request | 1-50 |
| Rate limit | ~5 requests/sec (not strictly documented) |

## Usage Check

```
GET https://api-free.deepl.com/v2/usage
Authorization: DeepL-Auth-Key <key>
```

Response:
```json
{
  "character_count": 10317,
  "character_limit": 500000
}
```

## Translate Endpoint

```
POST /v2/translate
Content-Type: application/json

{
  "text": ["Hello, world!"],
  "target_lang": "ZH",
  "source_lang": "EN",        // optional
  "formality": "prefer_more",  // optional: default/more/less/prefer_more/prefer_less
  "context": "...",            // optional: disambiguation hint (not billed)
  "split_sentences": "1",      // optional: 0/1/nonewlines
  "show_billed_characters": true
}
```

### Formality Support
`prefer_more`/`prefer_less` safe for all; strict `more`/`less` only for:
DE, FR, IT, ES, ES-419, NL, PL, PT-BR, PT-PT, JA, RU

## Language Codes

| Language | Code |
|----------|------|
| Bulgarian | BG |
| Czech | CS |
| Danish | DA |
| German | DE |
| Greek | EL |
| English | EN (all variants: EN-US, EN-GB) |
| Spanish | ES |
| Estonian | ET |
| Finnish | FI |
| French | FR |
| Hungarian | HU |
| Indonesian | ID |
| Italian | IT |
| Japanese | JA |
| Korean | KO |
| Lithuanian | LT |
| Latvian | LV |
| Dutch | NL |
| Polish | PL |
| Portuguese | PT (all variants: PT-BR, PT-PT) |
| Romanian | RO |
| Russian | RU |
| Slovak | SK |
| Slovenian | SL |
| Swedish | SV |
| Turkish | TR |
| Ukrainian | UK |
| Chinese | ZH (simplified) |

### Glossaries Support
Language pairs for glossaries: DE↔EN, FR↔EN, ES↔EN, JA↔EN, IT↔EN, NL↔EN, PL↔EN, PT↔EN, RU↔EN, ZH↔EN, KO↔EN

## Python SDK

```bash
~/.hermes/venv/bin/pip install deepl
```

```python
import deepl
client = deepl.DeepLClient(auth_key)
result = client.translate_text("Hello, world!", target_lang="ZH")
print(result.text)  # "你好，世界！"
usage = client.get_usage()
print(usage.character.used, "/", usage.character.limit)
```

Note: The SDK is installed in the Hermes venv, not system Python.
