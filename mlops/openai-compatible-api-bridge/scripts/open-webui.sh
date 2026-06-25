#!/usr/bin/env bash
# Open WebUI 管理脚本（带外部连接配置持久化）
# 用法: ./open-webui.sh start|stop|status|logs|restart

OWU_DIR="$HOME/open-webui"
VENV_PYTHON="$OWU_DIR/.venv/bin/python"
OWU_CMD="$OWU_DIR/.venv/bin/open-webui"
PIDFILE="$OWU_DIR/webui.pid"
LOGFILE="$OWU_DIR/webui.log"

# --- 从安全存储读取凭据 ---
# 从 ~/.hermes/.env 加载（如果存在）
ENV_FILE="$HOME/.hermes/.env"
OWU_EMAIL=""
OWU_PASSWORD=""
if [ -f "$ENV_FILE" ]; then
    # 只读取特定行，不 source 整个文件
    OWU_EMAIL=$(grep -m1 '^OWU_ADMIN_EMAIL=' "$ENV_FILE" 2>/dev/null | cut -d= -f2-)
    OWU_PASSWORD=$(grep -m1 '^OWU_ADMIN_PASSWORD=' "$ENV_FILE" 2>/dev/null | cut -d= -f2-)
fi
# 回退到默认值（如果 .env 中没有配置）
: "${OWU_EMAIL:=andymao76@gmail.com}"
: "${OWU_PASSWORD:=tgehltb5}"

start() {
    if [ -f "$PIDFILE" ] && kill -0 $(cat "$PIDFILE") 2>/dev/null; then
        echo "Already running (PID $(cat $PIDFILE))"
        return
    fi
    mkdir -p "$(dirname "$LOGFILE")"
    nohup "$VENV_PYTHON" "$OWU_CMD" serve --port 3000 \
        >> "$LOGFILE" 2>&1 &
    echo $! > "$PIDFILE"
    sleep 8

    # 等待服务就绪后，通过 API 配置外部连接
    echo "Configuring external connections..."
    for i in {1..10}; do
        TOKEN=$(curl -s -X POST http://localhost:3000/api/v1/auths/signin \
            -H "Content-Type: application/json" \
            -d "{\"email\":\"${OWU_EMAIL}\",\"password\": \"${OWU_PASSWORD}\"}" 2>/dev/null | \
            python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('token',''))" 2>/dev/null)
        if [ -n "$TOKEN" ]; then
            curl -s -X POST http://localhost:3000/api/v1/configs/connections \
                -H "Authorization: Bearer *** \
                -H "Content-Type: application/json" \
                -d '{"ENABLE_DIRECT_CONNECTIONS":true,"ENABLE_BASE_MODELS_CACHE":true,"OPENAI_API_BASE_URLS":"http://localhost:9099/v1","OPENAI_API_KEYS":""}' > /dev/null
            echo "  External connections configured (Hermes Bridge: http://localhost:9099/v1)"
            break
        fi
        sleep 3
    done

    echo "Open WebUI started (PID $(cat $PIDFILE))"
    status
}

stop() {
    if [ ! -f "$PIDFILE" ]; then echo "Not running"; return; fi
    kill $(cat "$PIDFILE") 2>/dev/null && echo "Stopped" || echo "Process not found"
    rm -f "$PIDFILE"
}

status() {
    if [ -f "$PIDFILE" ] && kill -0 $(cat "$PIDFILE") 2>/dev/null; then
        local uptime=$(ps -o etime= -p $(cat "$PIDFILE") 2>/dev/null | tr -d ' ')
        echo "Open WebUI RUNNING (PID $(cat $PIDFILE), uptime $uptime)"
        curl -s http://localhost:3000/ > /dev/null 2>&1 && echo "  http://localhost:3000 ✅" || echo "  (not ready)"
    else
        echo "Open WebUI STOPPED"
    fi
}

logs() { tail -30 "$LOGFILE" 2>/dev/null || echo "No logs"; }

case "${1:-status}" in
    start)   start ;;
    stop)    stop ;;
    restart) stop; sleep 2; start ;;
    status)  status ;;
    logs)    logs ;;
    *)       echo "Usage: $0 {start|stop|restart|status|logs}" ;;
esac
