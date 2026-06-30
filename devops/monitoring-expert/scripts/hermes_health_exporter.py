#!/usr/bin/env python3
"""
Hermes Health Exporter v2 — Prometheus 指标暴露器
端口 9800，全面监控：系统负载 / MCP / Provider / API / Docker / 数据库 / Skill / 知识库

用法:
  python3 hermes_health_exporter.py

环境变量:
  HERMES_EXPORTER_PORT=9800  (默认)

指标分类:
  hermes_load*               → 系统负载
  hermes_mcp_*               → MCP server 在线率与详情
  hermes_provider_*          → LLM Provider 连通性+延迟
  hermes_api_*               → 内部 API 端点健康
  hermes_docker_*            → Docker 容器监控
  hermes_db_*                → SQLite/Doris 数据库
  hermes_skills_*            → Skill 活跃比
  hermes_kb_* / qdrant_*     → 知识库状态
  hermes_clash_*             → Clash 代理节点
  hermes_cron_*              → Cron 作业统计
  hermes_up                  → 综合健康度
"""
import http.server
import json
import os
import subprocess
import time
import re
from urllib.parse import urlparse

METRICS = {}
LAST_CHECK = 0
CACHE_TTL = 30

def run_cmd(cmd, timeout=10):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, '', 'timeout'
    except FileNotFoundError:
        return -2, '', 'not found'

# ── 系统负载 ──
def check_system():
    results = {}
    with open('/proc/loadavg') as f:
        parts = f.read().strip().split()
        results['load_1'] = float(parts[0])
        results['load_5'] = float(parts[1])
        results['load_15'] = float(parts[2])
    with open('/proc/meminfo') as f:
        mem = {}
        for line in f:
            for k in ('MemTotal', 'MemAvailable', 'SwapTotal', 'SwapFree'):
                if line.startswith(k + ':'):
                    mem[k] = int(line.split()[1])
    results['mem_total'] = mem.get('MemTotal', 0)
    results['mem_avail'] = mem.get('MemAvailable', 0)
    st = os.statvfs('/')
    results['disk_total'] = st.f_frsize * st.f_blocks
    results['disk_avail'] = st.f_frsize * st.f_bavail
    return results

# ── MCP 监控 (全部 MCP server) ──
def check_mcp():
    results = {}
    rc, out, _ = run_cmd(['hermes', 'mcp', 'list'], timeout=15)
    results['cli_reachable'] = 1 if rc == 0 and out.strip() else 0
    mcp_servers = []
    for line in out.splitlines():
        m = re.match(r'\s{2}(\S+)\s+\S+\s+\S+\s+([✓✗])\s+(\S+)', line)
        if m:
            name = m.group(1)
            status = 1 if m.group(2) == '✓' else 0
            enabled = 1 if m.group(3) == 'enabled' else 0
            mcp_servers.append((name, status, enabled))
            results[f'server_{name}_up'] = status
            results[f'server_{name}_enabled'] = enabled
    results['server_count'] = len(mcp_servers)
    results['server_up_count'] = sum(1 for _, s, _ in mcp_servers if s)
    results['server_ratio'] = (results['server_up_count'] / results['server_count'] * 100) if results['server_count'] else 0
    # process-level checks
    mcp_procs = {
        'obsidian_mcp': 'obsidian-mcp-server',
        'xiaohongshu': 'xiaohongshu_bridge',
    }
    for key, pattern in mcp_procs.items():
        rc, _, _ = run_cmd(['pgrep', '-f', pattern])
        results[f'proc_{key}'] = 1 if rc == 0 else 0
    # systemd services
    mcp_services = {
        'xiaohongshu': 'xiaohongshu-mcp',
        'chrome_cdp': 'hermes-chrome-cdp',
        'health_exporter': 'hermes-health-exporter',
    }
    for key, svc in mcp_services.items():
        rc, out, _ = run_cmd(['systemctl', '--user', 'is-active', svc])
        results[f'service_{key}'] = 1 if out == 'active' else 0
    # ports
    rc, out, _ = run_cmd(['ss', '-tln'])
    for port, name in {'18060': 'xiaohongshu_http', '9222': 'chrome_cdp', '9800': 'health_exporter'}.items():
        results[f'port_{name}'] = 1 if f':{port} ' in out else 0
    return results

# ── Provider HTTP 监控 (带延迟) ──
def check_providers():
    results = {}
    providers = {
        'deepseek': ('https://api.deepseek.com/v1/models', True),
        'siliconflow': ('https://api.siliconflow.com/v1/models', True),
        'siliconflow_cn': ('https://api.siliconflow.cn/v1/models', False),
    }
    for name, (url, use_proxy) in providers.items():
        start = time.time()
        cmd = ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', '--max-time', '8']
        cmd += ['-x', 'http://127.0.0.1:7897'] if use_proxy else ['--noproxy', '*']
        cmd.append(url)
        rc, out, _ = run_cmd(cmd, timeout=10)
        elapsed = round(time.time() - start, 3)
        results[name] = 1 if out in ('200', '401', '429') else 0
        results[f'{name}_http'] = out or '000'
        results[f'{name}_latency'] = elapsed
    return results

# ── API 监控 (Hermes 内部 API 端点) ──
def check_apis():
    results = {}
    apis = {
        'gateway': ('http://127.0.0.1:8088/health', 3),
        'openwebui': ('http://127.0.0.1:3001/health', 3),
        'prometheus': ('http://127.0.0.1:9090/api/v1/status/buildinfo', 3),
        'grafana': ('http://admin:admin@127.0.0.1:3000/api/health', 3),
        'clash_api': ('http://127.0.0.1:9090/version', 3),
    }
    for name, (url, timeout) in apis.items():
        start = time.time()
        rc, out, _ = run_cmd(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', '--max-time', str(timeout), url], timeout=timeout+2)
        elapsed = round(time.time() - start, 3)
        results[name] = 1 if out in ('200', '204', '301', '302') else 0
        results[f'{name}_http'] = out or '000'
        results[f'{name}_latency'] = elapsed
    return results

# ── Docker 监控 ──
def check_docker():
    results = {}
    rc, _, _ = run_cmd(['pgrep', '-f', 'dockerd'])
    results['dockerd'] = 1 if rc == 0 else 0
    rc, out, _ = run_cmd(['docker', 'ps', '-q', '--no-trunc'])
    results['api'] = 1 if rc == 0 else 0
    rc, out, _ = run_cmd(['docker', 'ps', '-a', '-q'])
    results['container_total'] = len(out.splitlines()) if out else 0
    rc, out, _ = run_cmd(['docker', 'ps', '-q'])
    results['container_running'] = len(out.splitlines()) if out else 0
    results['container_ratio'] = (results['container_running'] / results['container_total'] * 100) if results['container_total'] else 0
    for name in ('prometheus', 'grafana', 'node_exporter', 'cadvisor'):
        rc, out, _ = run_cmd(['docker', 'ps', '-q', '-f', f'name={name}', '-f', 'status=running'])
        results[f'container_{name}'] = 1 if out.strip() else 0
    return results

# ── 数据库监控 ──
def check_databases():
    results = {}
    home = '/home/andymao'
    dbs = {
        'hermes_state': f'{home}/.hermes/state.db',
        'query_cache': f'{home}/.hermes/query_db.sqlite',
        'kb_index': f'{home}/.hermes/knowledge_index.db',
        'memory_store': f'{home}/.hermes/memory_store.db',
        'session_db': f'{home}/.hermes/sessions/sessions.db',
    }
    for name, path in dbs.items():
        if os.path.isfile(path):
            results[f'{name}_bytes'] = os.path.getsize(path)
            results[f'{name}_exists'] = 1
            rc, _, _ = run_cmd(['sqlite3', path, 'SELECT 1;'], timeout=3)
            results[f'{name}_reachable'] = 1 if rc == 0 else 0
        else:
            results[f'{name}_bytes'] = 0
            results[f'{name}_exists'] = 0
            results[f'{name}_reachable'] = 0
    # Doris
    rc, out, _ = run_cmd(['hermes', 'tool', 'search', 'doris'], timeout=8)
    results['doris_reachable'] = 1 if rc == 0 else 0
    return results

# ── Skill 活跃比 ──
def check_skills():
    results = {}
    sd = '/home/andymao/.hermes/skills'
    if os.path.isdir(sd):
        all_skills = [d for d in os.listdir(sd) if os.path.isdir(os.path.join(sd, d))]
        results['total'] = len(all_skills)
        now = time.time()
        week_ago = now - 7 * 86400
        modified = 0
        for d in all_skills:
            sp = os.path.join(sd, d, 'SKILL.md')
            if os.path.isfile(sp) and os.path.getmtime(sp) > week_ago:
                modified += 1
        results['modified_7d'] = modified
        results['active_ratio'] = round(modified / results['total'] * 100, 1) if results['total'] else 0
        results['inactive_7d'] = results['total'] - modified
    return results

# ── 知识库监控 ──
def check_knowledge():
    results = {}
    kb = '/home/andymao/knowledge'
    if os.path.isdir(kb):
        total_size = 0; total_files = 0
        for root, dirs, files in os.walk(kb):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            md_files = [f for f in files if f.endswith('.md')]
            if md_files:
                total_size += sum(os.path.getsize(os.path.join(root, f)) for f in md_files)
                total_files += len(md_files)
        results['total_files'] = total_files
        results['total_bytes'] = total_size
    import subprocess as sp
    try:
        qr = sp.run(
            ['curl', '-s', '-o', '-', '-w', '%{http_code}', 'http://localhost:6333/collections'],
            capture_output=True, text=True, timeout=5
        )
        if qr.stdout.strip() == '200':
            import json as _json
            raw = qr.stderr if qr.stderr else ''
            # re-run to get body
            qb = sp.run(
                ['curl', '-s', 'http://localhost:6333/collections'],
                capture_output=True, text=True, timeout=5
            )
            data = _json.loads(qb.stdout) if qb.stdout else {}
            cols = data.get('result', {}).get('collections', [])
            results['qdrant_collections'] = len(cols)
            results['qdrant_reachable'] = 1
        else:
            results['qdrant_collections'] = 0
            results['qdrant_reachable'] = 0
    except Exception:
        results['qdrant_collections'] = 0
        results['qdrant_reachable'] = 0
    md = '/home/andymao/.hermes/memories'
    if os.path.isdir(md):
        total = 0
        for f in os.listdir(md):
            fp = os.path.join(md, f)
            if os.path.isfile(fp) and not f.endswith('.lock'):
                total += os.path.getsize(fp)
        results['memories_bytes'] = total
    return results

# ── Clash 代理 ──
def check_clash():
    results = {}
    rc, out, _ = run_cmd(['curl', '-s', '--max-time', '3', '--unix-socket', '/tmp/verge/verge-mihomo.sock', 'http://localhost/proxies'])
    if rc == 0 and out:
        try:
            data = json.loads(out).get('proxies', {})
            results['api_ok'] = 1
            for name in ('主代理', 'GLOBAL'):
                if name in data:
                    results['main_now'] = data[name].get('now', '?')
                    results['main_alive'] = 1 if data[name].get('alive') else 0
                    break
            proxy_types = ('Shadowsocks', 'VMess', 'Trojan', 'Hysteria2', 'VLESS', 'Hysteria', 'TUIC', 'Tuic')
            results['total_proxies'] = sum(1 for k, v in data.items() if isinstance(v, dict) and v.get('type') in proxy_types)
        except Exception:
            results['api_ok'] = 0
    else:
        results['api_ok'] = 0
    return results

# ── 代理基础检查 ──
def check_proxy():
    results = {}
    rc, _, _ = run_cmd(['pgrep', '-f', 'clash-verge'])
    results['gui'] = 1 if rc == 0 else 0
    rc, _, _ = run_cmd(['pgrep', '-f', 'verge-mihomo'])
    results['mihomo'] = 1 if rc == 0 else 0
    rc, out, _ = run_cmd(['ss', '-tln'])
    results['port'] = 1 if ':7897 ' in out else 0
    rc, out, _ = run_cmd(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
                          '--max-time', '5', '-x', 'http://127.0.0.1:7897',
                          'https://www.google.com/generate_204'])
    results['google_reachable'] = 1 if out in ('204', '200', '301', '302') else 0
    return results

# ── Cron ──
def check_cron():
    results = {}
    rc, out, _ = run_cmd(['hermes', 'cron', 'list'], timeout=15)
    if rc == 0:
        results['active_jobs'] = len(re.findall(r'\[active\]', out))
        results['failed_jobs'] = len(re.findall(r'Delivery failed', out))
    else:
        results['active_jobs'] = 0
        results['failed_jobs'] = 0
    return results

def gather_metrics():
    global METRICS, LAST_CHECK
    now = time.time()
    if now - LAST_CHECK < CACHE_TTL and METRICS:
        return METRICS
    METRICS = {
        'system': check_system(), 'mcp': check_mcp(), 'providers': check_providers(),
        'apis': check_apis(), 'docker': check_docker(), 'databases': check_databases(),
        'skills': check_skills(), 'knowledge': check_knowledge(), 'clash': check_clash(),
        'proxy': check_proxy(), 'cron': check_cron(), 'timestamp': now,
    }
    LAST_CHECK = now
    return METRICS

def format_metrics(m):
    lines = []
    s, mc, pr, ap, dk, db, sk, kb, cl, cr, px = \
        m['system'], m['mcp'], m['providers'], m['apis'], m['docker'], \
        m['databases'], m['skills'], m['knowledge'], m['clash'], m['cron'], m['proxy']

    lines.append('# HELP hermes_load1 系统1分钟负载')
    lines.append('# TYPE hermes_load1 gauge')
    lines.append(f'hermes_load1 {s["load_1"]}')
    lines.append('# HELP hermes_load5 系统5分钟负载')
    lines.append('# TYPE hermes_load5 gauge')
    lines.append(f'hermes_load5 {s["load_5"]}')
    lines.append('# HELP hermes_load15 系统15分钟负载')
    lines.append('# TYPE hermes_load15 gauge')
    lines.append(f'hermes_load15 {s["load_15"]}')
    lines.append('# HELP hermes_mem_avail_bytes 可用内存')
    lines.append('# TYPE hermes_mem_avail_bytes gauge')
    lines.append(f'hermes_mem_avail_bytes {s["mem_avail"]*1024}')
    lines.append('# HELP hermes_mem_total_bytes 总内存')
    lines.append('# TYPE hermes_mem_total_bytes gauge')
    lines.append(f'hermes_mem_total_bytes {s["mem_total"]*1024}')
    lines.append('# HELP hermes_disk_avail_bytes 可用磁盘')
    lines.append('# TYPE hermes_disk_avail_bytes gauge')
    lines.append(f'hermes_disk_avail_bytes {s["disk_avail"]}')
    lines.append('# HELP hermes_disk_total_bytes 总磁盘')
    lines.append('# TYPE hermes_disk_total_bytes gauge')
    lines.append(f'hermes_disk_total_bytes {s["disk_total"]}')

    for key in sorted(mc):
        if key.startswith('server_') and key.endswith('_up'):
            name = key.replace('server_', '').replace('_up', '')
            lines.append(f'hermes_mcp_server_up{{server="{name}"}} {mc[key]}')
        elif key.startswith('server_') and key.endswith('_enabled'):
            name = key.replace('server_', '').replace('_enabled', '')
            lines.append(f'hermes_mcp_server_enabled{{server="{name}"}} {mc[key]}')
    lines.append('# HELP hermes_mcp_ratio MCP server 在线率')
    lines.append('# TYPE hermes_mcp_ratio gauge')
    lines.append(f'hermes_mcp_ratio {mc.get("server_ratio", 0)}')
    lines.append('# HELP hermes_mcp_cli_reachable hermes mcp list 可达')
    lines.append('# TYPE hermes_mcp_cli_reachable gauge')
    lines.append(f'hermes_mcp_cli_reachable {mc.get("cli_reachable", 0)}')

    lines.append('# HELP hermes_provider_up Provider API 连通性')
    lines.append('# TYPE hermes_provider_up gauge')
    for p in ('deepseek', 'siliconflow', 'siliconflow_cn'):
        lines.append(f'hermes_provider_up{{provider="{p}"}} {pr.get(p, 0)}')
    lines.append('# HELP hermes_provider_http_code Provider HTTP 状态码')
    lines.append('# TYPE hermes_provider_http_code gauge')
    for p in ('deepseek', 'siliconflow', 'siliconflow_cn'):
        code = pr.get(f'{p}_http', '0')
        try: code = int(code)
        except: code = 0
        lines.append(f'hermes_provider_http_code{{provider="{p}"}} {code}')
    lines.append('# HELP hermes_provider_latency_seconds Provider 响应延迟')
    lines.append('# TYPE hermes_provider_latency_seconds gauge')
    for p in ('deepseek', 'siliconflow', 'siliconflow_cn'):
        lines.append(f'hermes_provider_latency_seconds{{provider="{p}"}} {pr.get(f"{p}_latency", 0)}')

    lines.append('# HELP hermes_api_up 内部 API 端点连通性')
    lines.append('# TYPE hermes_api_up gauge')
    for api in ('gateway', 'openwebui', 'prometheus', 'grafana', 'clash_api'):
        lines.append(f'hermes_api_up{{api="{api}"}} {ap.get(api, 0)}')
    lines.append('# HELP hermes_api_latency_seconds API 响应延迟')
    lines.append('# TYPE hermes_api_latency_seconds gauge')
    for api in ('gateway', 'openwebui', 'prometheus', 'grafana', 'clash_api'):
        lines.append(f'hermes_api_latency_seconds{{api="{api}"}} {ap.get(f"{api}_latency", 0)}')

    lines.append('# HELP hermes_docker_up Docker daemon 运行状态')
    lines.append('# TYPE hermes_docker_up gauge')
    lines.append(f'hermes_docker_up {dk["dockerd"]}')
    lines.append('# HELP hermes_docker_container_running 运行中容器数')
    lines.append('# TYPE hermes_docker_container_running gauge')
    lines.append(f'hermes_docker_container_running {dk["container_running"]}')
    lines.append('# HELP hermes_docker_container_total 容器总数')
    lines.append('# TYPE hermes_docker_container_total gauge')
    lines.append(f'hermes_docker_container_total {dk["container_total"]}')
    lines.append('# HELP hermes_docker_container_ratio 容器运行率')
    lines.append('# TYPE hermes_docker_container_ratio gauge')
    lines.append(f'hermes_docker_container_ratio {dk["container_ratio"]}')
    for name in ('prometheus', 'grafana', 'node_exporter', 'cadvisor'):
        lines.append(f'hermes_docker_container_up{{name="{name}"}} {dk.get(f"container_{name}", 0)}')

    db_labels = {'hermes_state': 'Hermes会话', 'query_cache': '查询缓存',
                 'kb_index': '知识索引', 'memory_store': '记忆存储', 'session_db': '历史会话'}
    lines.append('# HELP hermes_db_bytes 数据库文件大小')
    lines.append('# TYPE hermes_db_bytes gauge')
    for key, label in db_labels.items():
        lines.append(f'hermes_db_bytes{{db="{label}"}} {db.get(f"{key}_bytes", 0)}')
    lines.append('# HELP hermes_db_reachable 数据库连通性')
    lines.append('# TYPE hermes_db_reachable gauge')
    for key, label in db_labels.items():
        lines.append(f'hermes_db_reachable{{db="{label}"}} {db.get(f"{key}_reachable", 0)}')
    lines.append('# HELP hermes_db_doris_reachable Doris 数据库连通')
    lines.append('# TYPE hermes_db_doris_reachable gauge')
    lines.append(f'hermes_db_doris_reachable {db.get("doris_reachable", 0)}')

    lines.append('# HELP hermes_skills_total Skill 总数')
    lines.append('# TYPE hermes_skills_total gauge')
    lines.append(f'hermes_skills_total {sk.get("total", 0)}')
    lines.append('# HELP hermes_skills_modified_7d 近7天修改的 Skill 数')
    lines.append('# TYPE hermes_skills_modified_7d gauge')
    lines.append(f'hermes_skills_modified_7d {sk.get("modified_7d", 0)}')
    lines.append('# HELP hermes_skills_active_ratio Skill 活跃比')
    lines.append('# TYPE hermes_skills_active_ratio gauge')
    lines.append(f'hermes_skills_active_ratio {sk.get("active_ratio", 0)}')
    lines.append('# HELP hermes_skills_inactive_7d 近7天未修改的 Skill 数')
    lines.append('# TYPE hermes_skills_inactive_7d gauge')
    lines.append(f'hermes_skills_inactive_7d {sk.get("inactive_7d", 0)}')

    lines.append('# HELP hermes_kb_files 知识库 Markdown 文件数')
    lines.append('# TYPE hermes_kb_files gauge')
    lines.append(f'hermes_kb_files {kb.get("total_files", 0)}')
    lines.append('# HELP hermes_kb_bytes 知识库总大小')
    lines.append('# TYPE hermes_kb_bytes gauge')
    lines.append(f'hermes_kb_bytes {kb.get("total_bytes", 0)}')
    lines.append('# HELP hermes_qdrant_reachable Qdrant 搜索后端可达性')
    lines.append('# TYPE hermes_qdrant_reachable gauge')
    lines.append(f'hermes_qdrant_reachable {kb.get("qdrant_reachable", 0)}')
    lines.append('# HELP hermes_qdrant_collections Qdrant 集合数')
    lines.append('# TYPE hermes_qdrant_collections gauge')
    lines.append(f'hermes_qdrant_collections {kb.get("qdrant_collections", 0)}')

    lines.append('# HELP hermes_clash_api Clash API 连通性')
    lines.append('# TYPE hermes_clash_api gauge')
    lines.append(f'hermes_clash_api {cl.get("api_ok", 0)}')
    lines.append('# HELP hermes_clash_total_proxies 代理节点总数')
    lines.append('# TYPE hermes_clash_total_proxies gauge')
    lines.append(f'hermes_clash_total_proxies {cl.get("total_proxies", 0)}')

    lines.append('# HELP hermes_cron_active_jobs 活跃 Cron 作业数')
    lines.append('# TYPE hermes_cron_active_jobs gauge')
    lines.append(f'hermes_cron_active_jobs {cr.get("active_jobs", 0)}')
    lines.append('# HELP hermes_cron_failed_jobs 推送失败的作业数')
    lines.append('# TYPE hermes_cron_failed_jobs gauge')
    lines.append(f'hermes_cron_failed_jobs {cr.get("failed_jobs", 0)}')

    all_ok = all([px['gui'], px['mihomo'],
                  mc.get('server_ratio', 0) > 50,
                  any(pr[p] for p in ('deepseek', 'siliconflow')),
                  dk['dockerd'], dk['api']])
    lines.append('# HELP hermes_up 综合健康度 (1=正常)')
    lines.append('# TYPE hermes_up gauge')
    lines.append(f'hermes_up {1 if all_ok else 0}')
    lines.append(f'# hermes_health_last_check {int(m["timestamp"])}')
    return '\n'.join(lines) + '\n'

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/metrics':
            body = format_metrics(gather_metrics()).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif parsed.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        elif parsed.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<h1>Hermes Health Exporter v2</h1><p><a href="/metrics">Metrics</a></p>')
        else:
            self.send_response(404)
            self.end_headers()
    def log_message(self, fmt, *args):
        pass

if __name__ == '__main__':
    port = int(os.environ.get('HERMES_EXPORTER_PORT', '9800'))
    server = http.server.HTTPServer(('0.0.0.0', port), Handler)
    print(f'Hermes Health Exporter v2 running on :{port}')
    server.serve_forever()
