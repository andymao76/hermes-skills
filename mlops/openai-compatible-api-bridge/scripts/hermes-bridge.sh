#!/usr/bin/env bash
# Hermes Bridge 管理脚本
# 用法: ./hermes-bridge.sh start|stop|status|logs|restart

BRIDGE_PY="$HOME/.hermes/scripts/openwebui-bridge.py"
VENV_PYTHON="$HOME/.hermes/venv/bin/python3"
PIDFILE="$HOME/.hermes/bridge.pid"
LOGFILE="$HOME/.hermes/logs/bridge.log"

start() {
    if [ -f "$PIDFILE" ] && kill -0 $(cat "$PIDFILE") 2>/dev/null; then
        echo "Already running (PID $(cat $PIDFILE))"
        return
    fi
    mkdir -p "$(dirname "$LOGFILE")"
    nohup env \
        HERMES_HOME="$HOME/.hermes" \
        HTTPS_PROXY="http://127.0.0.1:7897" \
        HTTP_PROXY="http://127.0.0.1:7897" \
        "$VENV_PYTHON" "$BRIDGE_PY" \
        >> "$LOGFILE" 2>&1 &
    echo $! > "$PIDFILE"
    sleep 2
    echo "Hermes Bridge started (PID $(cat $PIDFILE))"
    status
}

stop() {
    if [ ! -f "$PIDFILE" ]; then
        echo "Not running (no pidfile)"
        return
    fi
    PID=$(cat "$PIDFILE")
    kill "$PID" 2>/dev/null && echo "Stopped (PID $PID)" || echo "Process not found"
    rm -f "$PIDFILE"
}

status() {
    if [ -f "$PIDFILE" ] && kill -0 $(cat "$PIDFILE") 2>/dev/null; then
        echo "Hermes Bridge is RUNNING (PID $(cat $PIDFILE))"
        curl -s http://localhost:9099/ 2>/dev/null || echo "  (not responding yet)"
    else
        echo "Hermes Bridge is STOPPED"
    fi
}

logs() {
    tail -30 "$LOGFILE" 2>/dev/null || echo "No logs yet"
}

case "${1:-status}" in
    start)    start ;;
    stop)     stop ;;
    restart)  stop; sleep 1; start ;;
    status)   status ;;
    logs)     logs ;;
    *)        echo "Usage: $0 {start|stop|restart|status|logs}" ;;
esac
