#!/bin/bash
# Wrapper to use the stock analysis venv
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PYTHON="/tmp/stock-venv/bin/python3"

if [ "$1" = "stock_data.py" ]; then
  shift
  exec "$VENV_PYTHON" "$SCRIPT_DIR/stock_data.py" "$@"
elif [ "$1" = "stock_news.py" ]; then
  shift
  exec "$VENV_PYTHON" "$SCRIPT_DIR/stock_news.py" "$@"
else
  exec "$VENV_PYTHON" "$SCRIPT_DIR/$1" "$@"
fi
