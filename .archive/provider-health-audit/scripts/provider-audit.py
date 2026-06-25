#!/usr/bin/env python3
"""
Reusable API provider health probe.
Reads ~/.hermes/config.yaml, tests every configured provider,
reports status, latency, and detects key corruption.
"""
import yaml, os, time, json, sys
import requests
from datetime import datetime

HOME = os.path.expanduser('~')
CONFIG = os.path.join(HOME, '.hermes', 'config.yaml')
ENV_FILE = os.path.join(HOME, '.hermes', '.env')
PROXY = {"https": "http://127.0.0.1:7897", "http": "http://127.0.0.1:7897"}
TEST_PROMPT = [{"role": "user", "content": "回复一个字：好"}]

def load_env():
    """Load ~/.hermes/.env into a dict (raw binary read to bypass redact)."""
    env = {}
    if not os.path.exists(ENV_FILE):
        return env
    with open(ENV_FILE, 'rb') as f:
        for line in f.read().split(b'\n'):
            if b'=' not in line:
                continue
            k, v = line.split(b'=', 1)
            env[k.decode('ascii', errors='replace').strip()] = v.decode('ascii', errors='replace').strip()
    return env

def test_provider(name, url, api_key, model, needs_proxy=False, timeout=30):
    """Test a single provider endpoint."""
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    chat_url = url.rstrip('/') + '/chat/completions'
    payload = {"model": model, "messages": TEST_PROMPT, "max_tokens": 10, "temperature": 0.1}
    proxies = PROXY if needs_proxy else None

    start = time.time()
    try:
        resp = requests.post(chat_url, json=payload, headers=headers, timeout=timeout, proxies=proxies)
        latency = round((time.time() - start) * 1000)
        if resp.status_code == 200:
            content = resp.json().get('choices', [{}])[0].get('message', {}).get('content', '')
            return "OK", latency, content[:60] or "(empty)"
        elif resp.status_code == 401:
            return "401 KEY_INVALID", latency, "API key rejected"
        elif resp.status_code == 402:
            return "402 BALANCE_EXHAUSTED", latency, "Payment required"
        elif resp.status_code == 429:
            return "429 RATE_LIMITED", latency, resp.text[:120]
        elif resp.status_code == 503:
            return "503 BUSY", latency, "Service temporarily unavailable"
        else:
            return f"ERR_{resp.status_code}", latency, resp.text[:120]
    except requests.Timeout:
        return "TIMEOUT", -1, f"Request timed out (>={timeout}s)"
    except requests.ConnectionError as e:
        return "CONN_FAIL", -1, str(e)[:100]
    except Exception as e:
        return "EXCEPTION", -1, f"{type(e).__name__}: {str(e)[:100]}"

def main():
    # Load config and env
    with open(CONFIG) as f:
        cfg = yaml.safe_load(f)
    env = load_env()
    providers = cfg.get('providers', {})

    results = []
    print(f"Provider Health Audit — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)

    for name, p in providers.items():
        url = p.get('base_url', '?')
        model = p.get('model', p.get('default', '?'))
        api_key = p.get('api_key', '')
        key_env = p.get('api_key_env', '')

        # Resolve key: env var takes precedence if key_env is set
        if key_env and env.get(key_env):
            api_key = env[key_env]

        # Determine proxy need
        needs_proxy = False
        if 'googleapis' in url or 'openrouter' in url or name == 'siliconflow':
            needs_proxy = True
        if name == 'siliconflow-cn' or 'dashscope' in url or 'deepseek' in url:
            needs_proxy = False

        print(f"\n--- {name} ---")
        print(f"  Endpoint: {url}")
        print(f"  Model:    {model}")
        print(f"  Key:      {'✅ set' if api_key else '❌ missing'} ({len(api_key) if api_key else 0} chars)")

        # Check for truncated key
        known_lengths = {
            'deepseek': (28, 50),
            'openrouter': (40, 70),
            'siliconflow': (40, 55),
            'dashscope': (30, 40),
            'gemini': (35, 42),
        }
        for key_str, (min_l, max_l) in known_lengths.items():
            if key_str in url.lower() or key_str in name.lower():
                if len(api_key) < min_l and len(api_key) > 0:
                    print(f"  ⚠️  Key may be TRUNCATED: {len(api_key)} chars, expected {min_l}-{max_l}")
                break

        if not api_key:
            print(f"  ❌ SKIPPED (no key)")
            continue

        # Test with default proxy setting
        status, lat, detail = test_provider(name, url, api_key, model, needs_proxy=needs_proxy)
        proxy_label = "(代理)" if needs_proxy else "(直连)"
        lat_str = f"{lat}ms" if lat >= 0 else "N/A"
        print(f"  {status} {proxy_label} | {lat_str} | {detail[:60]}")

        # If failed, try opposite proxy mode for diagnostics
        if status not in ("OK",):
            opp_status, opp_lat, opp_detail = test_provider(name, url, api_key, model, needs_proxy=not needs_proxy)
            opp_label = "(直连)" if needs_proxy else "(代理)"
            opp_lat_str = f"{opp_lat}ms" if opp_lat >= 0 else "N/A"
            print(f"    Failed with {'proxy' if needs_proxy else 'direct'}, trying opposite:")
            print(f"    {opp_status} {opp_label} | {opp_lat_str} | {opp_detail[:60]}")

        results.append((name, status, lat))

    # Summary table
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"{'Provider':25s} | {'Status':20s} | {'Latency'}")
    print("-" * 60)
    for name, status, lat in results:
        lat_str = f"{lat}ms" if lat >= 0 else "N/A"
        print(f"{name:25s} | {status:20s} | {lat_str}")

if __name__ == '__main__':
    main()
