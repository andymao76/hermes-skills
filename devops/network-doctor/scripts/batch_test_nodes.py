#!/usr/bin/env python3
"""
批量测试 Clash 所有单个节点对指定目标的连通性。

用法：
  python3 ~/.hermes/skills/devops/network-doctor/scripts/batch_test_nodes.py

原理：
  1. 将目标策略组（默认 OpenAI）指向「主代理」让流量走单节点
  2. 遍历主代理下的所有单个节点，逐一切换并测试
  3. 输出汇总表，按可用/WAF挡/不通 三级分类

依赖：
  - Clash Verge (verge-mihomo) unix socket: /tmp/verge/verge-mihomo.sock
  - curl
  - Python 3.6+
"""

import json, subprocess, time, sys

UNIX_SOCK = "/tmp/verge/verge-mihomo.sock"
PROXY_PORT = "127.0.0.1:7897"

# 目标策略组名称 - 要测试的服务对应的 Clash 策略组
TARGET_GROUP = "OpenAI"
# 主代理策略组（包含所有单个节点）
MAIN_GROUP = "主代理"
MAIN_GROUP_URL = "%E4%B8%BB%E4%BB%A3%E7%90%86"

# 测试目标 URL
TEST_GOOGLE = "https://www.google.com"
TEST_TARGET = "https://chatgpt.com"


def claw_get(path):
    r = subprocess.run(
        ["curl", "-s", "--unix-socket", UNIX_SOCK, f"http://localhost{path}"],
        capture_output=True, text=True, timeout=15
    )
    return json.loads(r.stdout)


def claw_put(path, node_name):
    payload = json.dumps({"name": node_name})
    subprocess.run(
        ["curl", "-s", "--unix-socket", UNIX_SOCK, "-X", "PUT",
         f"http://localhost{path}",
         "-H", "Content-Type: application/json",
         "-d", payload],
        capture_output=True, timeout=15
    )


def test_url(url, timeout=8):
    start = time.time()
    try:
        r = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
             "--proxy", f"http://{PROXY_PORT}",
             "--max-time", str(timeout), url],
            capture_output=True, text=True, timeout=timeout + 3
        )
        elapsed = round(time.time() - start, 3)
        code = r.stdout.strip()
        return code or "000", elapsed
    except:
        return "TIMEOUT", timeout


def main():
    # 1. 获取所有节点
    print("获取节点列表...")
    data = claw_get("/proxies")
    proxies = data["proxies"]

    # 提取单个节点（排除策略组）
    skiptypes = {"Selector", "URLTest", "Fallback", "LoadBalance",
                 "Relay", "Direct", "Reject", "Compatible", "Pass", "RejectDrop"}
    nodes = {k: v for k, v in proxies.items() if v.get("type") not in skiptypes}
    print(f"共发现 {len(nodes)} 个节点\n")

    # 2. 将目标策略组指向主代理
    print(f"配置 {TARGET_GROUP} → {MAIN_GROUP}...")
    claw_put(f"/proxies/{TARGET_GROUP}", MAIN_GROUP)
    time.sleep(0.3)

    data2 = claw_get("/proxies")
    main_now = data2["proxies"].get(MAIN_GROUP, {}).get("now", "?")
    print(f"  {MAIN_GROUP} now={main_now}\n")

    # 3. 逐个测试
    print(f"{'节点':<25} {'Google':<18} {'目标':<20}")
    print("=" * 63)

    results = []
    sorted_names = sorted(nodes.keys())
    for i, name in enumerate(sorted_names, 1):
        print(f"\r[{i:02d}/{len(sorted_names)}] {name:<20} 测试中...", end="", flush=True)

        claw_put(f"/proxies/{MAIN_GROUP_URL}", name)
        time.sleep(0.3)

        g_code, g_t = test_url(TEST_GOOGLE)
        t_code, t_t = test_url(TEST_TARGET)

        print(f"\r[{i:02d}/{len(sorted_names)}] {name:<25} {g_code:<5} ({g_t:.1f}s)     {t_code:<5} ({t_t:.1f}s)")
        results.append((name, g_code, g_t, t_code, t_t))

    # 4. 汇总
    print("\n" + "=" * 63)
    print(f"汇总：{TARGET_GROUP} 连通性测试")
    print("=" * 63)

    tiers = {
        f"✅ 可用 (HTTP 200)": [],
        f"⚠️ 连上但被WAF挡 (HTTP 403)": [],
        f"❌ 不通 (000/超时/其他)": [],
    }

    for name, g_c, g_t, t_c, t_t in results:
        g_ok = g_c in ("200", "204", "301", "302")
        if not g_ok:
            tiers["❌ 不通 (000/超时/其他)"].append(f"{name} (Google={g_c})")
            continue
        if t_c == "200":
            tiers["✅ 可用 (HTTP 200)"].append(f"{name} ({t_t:.1f}s)")
        elif t_c == "403":
            tiers["⚠️ 连上但被WAF挡 (HTTP 403)"].append(f"{name} ({t_t:.1f}s)")
        else:
            tiers["❌ 不通 (000/超时/其他)"].append(f"{name} (ChatGPT={t_c})")

    for tier_label, items in tiers.items():
        print(f"\n{tier_label} ({len(items)} 个):")
        if items:
            for n in items:
                print(f"  {n}")
        else:
            print("  (无)")

    print(f"\n{'':25} {'Google':>8} {'G_t':>6} {'ChatGPT':>8} {'C_t':>6}")
    print("-" * 55)
    for name, g_c, g_t, t_c, t_t in results:
        print(f"{name:<25} {g_c:>8} {g_t:>5.1f}s {t_c:>8} {t_t:>5.1f}s")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已中断。")
    except Exception as e:
        print(f"\n\n错误: {e}")
        sys.exit(1)
