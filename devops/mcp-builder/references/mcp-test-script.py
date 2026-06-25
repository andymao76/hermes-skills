#!/usr/bin/env python3
"""
MCP Server Batch Test — sends initialize + tools/list to each stdio MCP server.

Usage:
  python3 mcp-test-script.py

Requires: `mcp` and `json` from stdlib; subprocess spawning.
"""
import subprocess, json, sys, os, time

SERVERS = {
    "csdn": {
        "cmd": ["/home/andymao/.hermes/hermes-agent/venv/bin/python3",
                "/home/andymao/.hermes/mcp-servers/csdn/server.py"],
        "timeout": 15
    },
    "db-query": {
        "cmd": ["/home/andymao/.hermes/venv/bin/python3",
                "/home/andymao/.hermes/scripts/db_query_server.py"],
        "env": {"DB_PATH": os.path.expanduser("~/.hermes/query_db.sqlite")},
        "timeout": 15
    },
    "taobao": {
        "cmd": ["/home/andymao/.hermes/hermes-agent/venv/bin/python3",
                "/home/andymao/.hermes/taobao_mcp/server.py"],
        "env": {"DISPLAY": ":99", "NO_PROXY": "*"},
        "timeout": 20
    },
    "wikipedia": {
        "cmd": ["/home/andymao/.hermes/hermes-agent/venv/bin/wikipedia-mcp",
                "--language", "zh", "--enable-cache"],
        "env": {"HTTP_PROXY": "http://127.0.0.1:7897",
                "HTTPS_PROXY": "http://127.0.0.1:7897"},
        "timeout": 15
    },
    "xiaohongshu": {
        "cmd": ["/home/andymao/.hermes/venv/bin/python3",
                "/home/andymao/.hermes/scripts/xiaohongshu_bridge.py"],
        "timeout": 15
    },
    "zhihu": {
        "cmd": ["/home/andymao/.hermes/hermes-agent/venv/bin/python3",
                "/home/andymao/.hermes/mcp-servers/zh_mcp_server/run.py"],
        "env": {"json_path": "/home/andymao/.hermes/mcp-servers/zh_mcp_server/data"},
        "timeout": 15
    },
    "github-gov1": {
        "cmd": ["/home/andymao/bin/github-mcp-wrapper.sh", "stdio"],
        "timeout": 15
    },
}


def test_server(name, cfg):
    """Test a single stdio MCP server."""
    env = os.environ.copy()
    if cfg.get("env"):
        env.update(cfg["env"])

    proc = None
    try:
        proc = subprocess.Popen(
            cfg["cmd"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, env=env
        )

        # Send initialize
        init = json.dumps({
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2024-11-05",
                       "capabilities": {},
                       "clientInfo": {"name": "test", "version": "1.0"}}
        }) + "\n"
        proc.stdin.write(init.encode())
        proc.stdin.flush()

        init_resp = b""
        deadline = time.time() + cfg["timeout"]
        while time.time() < deadline:
            line = proc.stdout.readline()
            if line:
                init_resp += line
                try:
                    data = json.loads(line)
                    if data.get("id") == 1:
                        break
                except json.JSONDecodeError:
                    pass
            else:
                break

        if not init_resp:
            return {"name": name, "status": "❌", "tools": 0,
                    "server": "no response to initialize"}

        init_data = json.loads(init_resp.strip())
        si = init_data.get("result", {}).get("serverInfo", {})
        svr_name = si.get("name", "?")
        svr_ver = si.get("version", "?")

        # Send tools/list
        lst = json.dumps({
            "jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}
        }) + "\n"
        proc.stdin.write(lst.encode())
        proc.stdin.flush()

        lst_resp = b""
        deadline = time.time() + cfg["timeout"]
        while time.time() < deadline:
            line = proc.stdout.readline()
            if line:
                lst_resp += line
                try:
                    data = json.loads(line)
                    if data.get("id") == 2:
                        break
                except json.JSONDecodeError:
                    pass
            else:
                break

        if not lst_resp:
            return {"name": name, "status": "⚠️", "tools": 0,
                    "server": f"{svr_name} v{svr_ver}", "detail": "no tools/list response"}

        tools_data = json.loads(lst_resp.strip())
        tools = tools_data.get("result", {}).get("tools", [])
        return {"name": name, "status": "✅" if tools else "⚠️",
                "tools": len(tools),
                "server": f"{svr_name} v{svr_ver}"}

    except FileNotFoundError as e:
        return {"name": name, "status": "❌", "tools": 0,
                "server": f"binary not found: {e}"}
    except Exception as e:
        return {"name": name, "status": "❌", "tools": 0,
                "server": f"{type(e).__name__}: {str(e)[:60]}"}
    finally:
        if proc:
            try:
                proc.stdin.close()
                proc.terminate()
                proc.wait(timeout=3)
            except:
                proc.kill()


if __name__ == "__main__":
    print(f"\n{'='*60}")
    print(f"  MCP Server Batch Test  —  {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    results = []
    for name, cfg in SERVERS.items():
        r = test_server(name, cfg)
        results.append(r)
        status_icon = r["status"]
        tools_str = f"({r['tools']} tools)" if r["tools"] else ""
        print(f"  {status_icon}  {r['name']:20s}  {r['server'][:35]:35s}  {tools_str}")

    ok = sum(1 for r in results if r["status"] == "✅")
    warn = sum(1 for r in results if r["status"] == "⚠️")
    fail = sum(1 for r in results if r["status"] == "❌")

    print(f"\n{'='*60}")
    print(f"  总结: ✅ {ok}  ⚠️ {warn}  ❌ {fail}  |  总计 {len(results)}")
    print(f"{'='*60}\n")

    sys.exit(1 if fail > 0 else 0)
