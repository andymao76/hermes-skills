#!/usr/bin/env python3
"""Generate Hermes系统健康看板 Grafana dashboard JSON (V9 layout).

用法: python3 gen-health-dash.py | python3 -m json.tool > /tmp/hermes-health.json

Layout conventions:
  - stat panels h=2, textMode=value_and_name
  - compact bricks w=2, numeric blocks w=3-4
  - bar gauges w=5-14, time series w=12
  - rows fill 24 grid units each
"""

import json

def make_dashboard():
    d = {
        "title": "Hermes 系统健康看板",
        "version": 9,
        "tags": ["hermes", "health", "monitoring"],
        "schemaVersion": 39,
        "timezone": "browser",
        "editable": True,
        "refresh": "30s",
        "panels": []
    }
    p = d["panels"]

    def row(name=""):
        return {"title": name, "type": "row", "gridPos": {"h": 1, "w": 24, "x": 0, "y": 0}, "collapsed": False}

    def brick(desc, expr, x, y, w=2, h=2):
        return {"title": "", "type": "stat", "gridPos": {"h": h, "w": w, "x": x, "y": y},
                "targets": [{"expr": expr, "refId": "A"}], "description": desc,
                "fieldConfig": {"defaults": {"thresholds": {"mode": "absolute", "steps": [{"color": "#e74c3c", "value": None}, {"color": "#27ae60", "value": 1}]}, "color": {"mode": "background"}, "unit": "none", "min": 0, "max": 1}},
                "options": {"colorMode": "background", "graphMode": "none", "textMode": "value_and_name"}}

    def numbox(desc, expr, x, y, unit="none"):
        return {"title": "", "type": "stat", "gridPos": {"h": 2, "w": 3, "x": x, "y": y},
                "targets": [{"expr": expr, "refId": "A"}], "description": desc,
                "fieldConfig": {"defaults": {"color": {"mode": "palette-classic"}, "unit": unit}},
                "options": {"colorMode": "none", "graphMode": "none", "textMode": "value_and_name"}}

    def gauge_p(title, expr, x, y, w=4, thrs=None, unit="none"):
        if thrs is None:
            thrs = [{"color": "#27ae60", "value": None}, {"color": "#f39c12", "value": 4}, {"color": "#e74c3c", "value": 8}]
        mx = thrs[-1]["value"]
        return {"title": title, "type": "gauge", "gridPos": {"h": 2, "w": w, "x": x, "y": y},
                "targets": [{"expr": expr, "refId": "A"}],
                "fieldConfig": {"defaults": {"thresholds": {"mode": "absolute", "steps": thrs}, "color": {"mode": "thresholds"}, "unit": unit, "min": 0, "max": mx, "custom": {"orientation": "horizontal"}}}}

    def bg_bar(title, targets, x, y, w=12, h=2, unit="none"):
        return {"title": title, "type": "bargauge", "gridPos": {"h": h, "w": w, "x": x, "y": y},
                "targets": targets,
                "fieldConfig": {"defaults": {"unit": unit, "color": {"mode": "thresholds"}, "min": 0, "max": 1,
                    "thresholds": {"mode": "absolute", "steps": [{"color": "#e74c3c", "value": None}, {"color": "#27ae60", "value": 1}]},
                    "custom": {"orientation": "horizontal", "displayMode": "color-on", "minWidth": 40}}}}

    def db_bar(title, targets, x, y, w=24, h=2):
        return {"title": title, "type": "bargauge", "gridPos": {"h": h, "w": w, "x": x, "y": y},
                "targets": targets,
                "fieldConfig": {"defaults": {"unit": "bytes", "color": {"mode": "continuous-GrYlRd"}, "custom": {"orientation": "horizontal", "displayMode": "gradient"}}}}

    def ts_p(title, targets, x, y):
        return {"title": title, "type": "timeseries", "gridPos": {"h": 5, "w": 12, "x": x, "y": y},
                "targets": targets,
                "fieldConfig": {"defaults": {"color": {"mode": "palette-classic"}, "custom": {"showPoints": "never"}, "unit": "none"}}}

    _y = 0

    # Row 1: Overview
    p.append(row()); _y += 1
    p.append(brick("综合健康", "hermes_up", 0, _y))
    p.append(gauge_p("系统负载", "hermes_system_load1", 2, _y, w=4))
    p.append(gauge_p("可用内存", "hermes_memory_avail_bytes", 6, _y, w=5,
        thrs=[{"color":"#e74c3c","value":None},{"color":"#f39c12","value":2000000000},{"color":"#27ae60","value":4000000000}], unit="bytes"))
    p.append(gauge_p("可用磁盘", "hermes_disk_avail_bytes", 11, _y, w=5,
        thrs=[{"color":"#e74c3c","value":None},{"color":"#f39c12","value":10000000000},{"color":"#27ae60","value":50000000000}], unit="bytes"))
    ctr = numbox("容器运行/总计", "", 17, _y)
    ctr.update({"targets": [{"expr":"hermes_docker_container_running","legendFormat":"运行","refId":"A"},{"expr":"hermes_docker_container_total","legendFormat":"总计","refId":"B"}],
        "fieldConfig": {"defaults": {"color":{"mode":"palette-classic"},"unit":"none"},
            "overrides": [{"matcher":{"id":"byName","options":"运行"},"properties":[{"id":"color","value":{"mode":"fixed","fixedColor":"#27ae60"}}]},
                          {"matcher":{"id":"byName","options":"总计"},"properties":[{"id":"color","value":{"mode":"fixed","fixedColor":"#95a5a6"}}]}]},
        "options": {"colorMode":"none","graphMode":"area","textMode":"auto"}})
    p.append(numbox("Docker", "hermes_docker_up", 20, _y))
    _y += 2

    # Row 2: Infrastructure
    p.append(row()); _y += 1
    for i, (desc, expr) in enumerate([
        ("Docker后台", "hermes_docker_up"), ("Prometheus", 'hermes_docker_container_up{name="prometheus"}'),
        ("Grafana", 'hermes_docker_container_up{name="grafana"}'), ("node_exp", 'hermes_docker_container_up{name="node_exporter"}'),
        ("cadvisor", 'hermes_docker_container_up{name="cadvisor"}'), ("Clash GUI", "hermes_proxy_clash_gui"),
        ("Clash内核", "hermes_proxy_clash_mihomo"), ("代理端口", "hermes_proxy_clash_port"),
        ("Google", "hermes_proxy_google_reachable"),
    ]):
        p.append(brick(desc, expr, i*2, _y))
    p.append(bg_bar("API Provider", [
        {"expr":'hermes_provider_up{provider="deepseek"}',"legendFormat":"DeepSeek","refId":"A"},
        {"expr":'hermes_provider_up{provider="siliconflow"}',"legendFormat":"SiliconFlow","refId":"B"},
        {"expr":'hermes_provider_up{provider="siliconflow_cn"}',"legendFormat":"SiliconFlow国内","refId":"C"},
    ], 18, _y, w=6))
    _y += 2

    # Row 3: Services/MCP
    p.append(row()); _y += 1
    for i, (desc, expr) in enumerate([
        ("Gateway", 'hermes_service_up{service="gateway"}'), ("ChromeCDP", 'hermes_service_up{service="chrome_cdp"}'),
        ("CDP9222", 'hermes_service_up{service="cdp_port"}'), ("小红书MCP", 'hermes_service_up{service="xiaohongshu_mcp"}'),
        ("ObsidianMCP", 'hermes_mcp_server_up{server="obsidian_mcp"}'), ("小红书18060", 'hermes_mcp_port_up{port="xiaohongshu_http"}'),
        ("Exp9800", 'hermes_mcp_port_up{port="health_exporter"}'), ("HermesCLI", 'hermes_process_up{process="hermes_cli"}'),
        ("HealthExp", 'hermes_mcp_service_up{service="health_exporter"}'),
    ]):
        p.append(brick(desc, expr, i*2, _y))
    _y += 2

    # Row 4: Cron + Snap
    p.append(row()); _y += 1
    p.append(bg_bar("Cron脚本", [
        {"expr":'hermes_cron_script_up{script="daily-backup.sh"}',"legendFormat":"每日备份","refId":"A"},
        {"expr":'hermes_cron_script_up{script="github-trending.py"}',"legendFormat":"GitHub","refId":"B"},
        {"expr":'hermes_cron_script_up{script="gas-price-monitor.sh"}',"legendFormat":"油价","refId":"C"},
        {"expr":'hermes_cron_script_up{script="proxy-autoheal.sh"}',"legendFormat":"自愈","refId":"D"},
        {"expr":'hermes_cron_script_up{script="audit-full-chain.sh"}',"legendFormat":"审计","refId":"E"},
        {"expr":'hermes_cron_script_up{script="ima-backup.sh"}',"legendFormat":"IMA","refId":"F"},
        {"expr":'hermes_cron_script_up{script="ensure-vault-structure.sh"}',"legendFormat":"路径","refId":"G"},
    ], 0, _y, w=14))
    p.append(bg_bar("Snap", [
        {"expr":'hermes_snap_up{snap="snap_obsidian"}',"legendFormat":"Obsidian","refId":"A"},
        {"expr":'hermes_snap_up{snap="snap_chromium"}',"legendFormat":"Chromium","refId":"B"},
        {"expr":'hermes_snap_up{snap="snap_telegram"}',"legendFormat":"Telegram","refId":"C"},
    ], 14, _y, w=5))
    p.append(numbox("MCP连通", "hermes_mcp_connected", 19, _y))
    p.append(numbox("Crontab", "hermes_cron_total_jobs", 22, _y))
    _y += 2

    # Row 5: Clash Airport
    p.append(row("Clash 机场监控")); _y += 1
    p.append(numbox("机场节点", "hermes_clash_total_proxies", 0, _y))
    p.append(numbox("剩余流量", "hermes_clash_traffic_remaining_gb", 3, _y))
    p.append(numbox("重置天数", "hermes_clash_reset_days", 6, _y))
    p.append(brick("主代理组活跃", "hermes_clash_main_alive", 9, _y, w=4))
    nb = numbox("当前节点", "", 13, _y)
    nb["targets"] = [{"expr": 'hermes_clash_main_node', "legendFormat": "{{node}}", "refId": "A"}]
    nb["fieldConfig"]["defaults"]["color"]["mode"] = "none"
    nb["options"]["textMode"] = "name"
    p.append(nb)
    _y += 2

    # Row 6: Knowledge
    p.append(row("知识库与记忆")); _y += 1
    for i, (desc, expr, unit) in enumerate([
        ("Skills", "hermes_skills_total", "none"),
        ("知识库文件", "hermes_kb_files", "none"),
        ("知识库大小", "hermes_kb_bytes", "bytes"),
        ("持久记忆", "hermes_memories_bytes", "bytes"),
        ("插件", "hermes_plugins_total", "none"),
        ("近7天改动", "hermes_skills_modified_7d", "none"),
    ]):
        p.append(numbox(desc, expr, i*4, _y, unit=unit))
    _y += 2
    p.append(db_bar("数据库大小", [
        {"expr":'hermes_db_bytes{db="会话数据库"}',"legendFormat":"会话","refId":"A"},
        {"expr":'hermes_db_bytes{db="查询缓存"}',"legendFormat":"查询","refId":"B"},
        {"expr":'hermes_db_bytes{db="知识索引"}',"legendFormat":"索引","refId":"C"},
        {"expr":'hermes_db_bytes{db="记忆存储"}',"legendFormat":"记忆","refId":"D"},
    ], 0, _y))
    _y += 2

    # Row 7: Time series
    p.append(row()); _y += 1
    p.append(ts_p("系统负载趋势", [
        {"expr":"hermes_system_load1","legendFormat":"1min","refId":"A"},
        {"expr":"hermes_system_load5","legendFormat":"5min","refId":"B"},
        {"expr":"hermes_system_load15","legendFormat":"15min","refId":"C"},
    ], 0, _y))
    p.append(ts_p("Provider HTTP码", [
        {"expr":'hermes_provider_http_code{provider="deepseek"}',"legendFormat":"DeepSeek","refId":"A"},
        {"expr":'hermes_provider_http_code{provider="siliconflow"}',"legendFormat":"SiliconFlow","refId":"B"},
        {"expr":'hermes_provider_http_code{provider="siliconflow_cn"}',"legendFormat":"SiliconFlowCN","refId":"C"},
    ], 12, _y))

    return d

if __name__ == "__main__":
    print(json.dumps(make_dashboard(), indent=2, ensure_ascii=False))
