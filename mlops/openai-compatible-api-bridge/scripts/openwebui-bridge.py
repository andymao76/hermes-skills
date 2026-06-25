#!/usr/bin/env python3
"""
Hermes Agent → OpenAI 兼容 API 代理服务
让 Open WebUI 等外部工具通过此代理连接到 Hermes Agent。

用法：
  ~/.hermes/venv/bin/python ~/.hermes/scripts/openwebui-bridge.py

在 Open WebUI 中添加外部连接：
  URL: http://<你的IP>:9099/v1
  Key: 任意（可留空）
"""

import os
import sys
import json
import uuid
import time
import subprocess
import asyncio
import logging
from typing import Optional, AsyncIterator

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

# ── 配置 ──────────────────────────────────────────────────────────

HOST = os.environ.get("BRIDGE_HOST", "0.0.0.0")
PORT = int(os.environ.get("BRIDGE_PORT", "9099"))
API_KEY = os.environ.get("BRIDGE_API_KEY", "")
HERMES_HOME = os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))
HERMES_VENV_PYTHON = os.path.join(HERMES_HOME, "venv", "bin", "python3")
HERMES_CLI = os.path.join(HERMES_HOME, "venv", "bin", "hermes")

# 可用的模型列表（映射到 Hermes 的 --provider --model）
MODEL_MAP = {
    "siliconflow": {
        "id": "siliconflow",
        "provider": "siliconflow",
        "model": "Qwen/Qwen3.6-35B-A3B",
        "name": "Qwen3.6-35B (SiliconFlow)",
    },
    "deepseek-chat": {
        "id": "deepseek-chat",
        "provider": "deepseek",
        "model": "deepseek-chat",
        "name": "DeepSeek Chat",
    },
}

# ── 日志 ──────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("hermes-bridge")

# ── 模型 ──────────────────────────────────────────────────────────

app = FastAPI(title="Hermes Bridge (OpenAI Compatible)")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "deepseek-chat"
    messages: list[ChatMessage]
    stream: bool = False
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int = 0
    owned_by: str = "hermes-agent"


# ── 安全中间件 ───────────────────────────────────────────────────

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if API_KEY and request.url.path not in ("/v1/models", "/health", "/"):
        auth = request.headers.get("Authorization", "")
        expected = f"Bearer {API_KEY}"
        if auth != expected:
            return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    return await call_next(request)


# ── 调用 Hermes ─────────────────────────────────────────────────

def call_hermes(provider: str, model: str, system_prompt: str, user_message: str) -> str:
    """通过 Hermes CLI 单次调用获取回复。"""
    cfg = MODEL_MAP.get(provider if provider in MODEL_MAP else "deepseek-chat", {})
    prov = cfg.get("provider", provider)
    mdl = cfg.get("model", model)

    cmd = [
        HERMES_VENV_PYTHON, "-m", "hermes_cli.main", "chat", "-q", user_message,
        "--provider", prov, "--model", mdl, "-Q",
    ]

    env = os.environ.copy()
    env["HERMES_HOME"] = HERMES_HOME

    log.info("Calling Hermes: provider=%s model=%s", prov, mdl)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
            cwd=os.path.expanduser("~"),
        )
        output = (result.stdout or "").strip()
        if not output:
            output = (result.stderr or "").strip()
        log.info("Hermes response (%d chars)", len(output))
        return output
    except subprocess.TimeoutExpired:
        log.error("Hermes timed out after 120s")
        return "抱歉，请求超时了，请重试。"
    except Exception as e:
        log.error("Hermes call failed: %s", e)
        return f"处理请求时出错: {e}"


# ── API 端点 ──────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"service": "Hermes Bridge", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/v1/models")
async def list_models():
    models = []
    for mid in MODEL_MAP:
        models.append(ModelInfo(id=mid))
    return {"object": "list", "data": models}


@app.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest):
    system_prompt = ""
    user_message = ""
    for msg in req.messages:
        if msg.role == "system":
            system_prompt = msg.content
        elif msg.role == "user":
            user_message = msg.content

    if not user_message:
        raise HTTPException(status_code=400, detail="No user message provided")

    provider = req.model
    model = req.model

    if req.stream:
        return StreamingResponse(
            stream_response(provider, model, system_prompt, user_message),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )

    content = call_hermes(provider, model, system_prompt, user_message)
    response_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    return {
        "id": response_id,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": req.model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": content},
            "finish_reason": "stop",
        }],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }


async def stream_response(provider, model, system_prompt, user_message):
    content = call_hermes(provider, model, system_prompt, user_message)
    response_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"

    chunk_size = 20
    for i in range(0, len(content), chunk_size):
        chunk = content[i:i + chunk_size]
        data = {
            "id": response_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model,
            "choices": [{
                "index": 0,
                "delta": {"content": chunk},
                "finish_reason": None,
            }],
        }
        yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.02)

    data = {
        "id": response_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
    }
    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"


# ── 启动 ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    log.info("─" * 50)
    log.info("Hermes Bridge — OpenAI Compatible API")
    log.info(f"  Listen:  http://{HOST}:{PORT}")
    log.info(f"  Models:  {', '.join(MODEL_MAP.keys())}")
    log.info("─" * 50)
    log.info("在 Open WebUI 中添加外部连接:")
    log.info(f"  URL:  http://<你的IP>:{PORT}/v1")
    log.info(f"  Key:  {'<留空>' if not API_KEY else API_KEY}")
    log.info("─" * 50)
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
