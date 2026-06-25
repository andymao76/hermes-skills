#!/usr/bin/env python3
"""
Hermes Agent → OpenAI 兼容 API 代理服务
让 Open WebUI 等第三方前端通过此代理连接到 Hermes Agent。

原理：暴露 /v1/chat/completions 和 /v1/models 端点（OpenAI 兼容），
收到请求后通过 Hermes CLI (hermes chat -q) 单次调用进行推理。

这就是一个轻量级的 "Hermes-as-OpenAI-API" 桥接器。

用法：
  ~/.hermes/venv/bin/python ~/.hermes/scripts/openwebui-bridge.py
  # 服务监听 http://0.0.0.0:9099

环境变量：
  BRIDGE_HOST    监听地址 (默认 0.0.0.0)
  BRIDGE_PORT    监听端口 (默认 9099)
  BRIDGE_API_KEY 可选 API Key 认证

在 Open WebUI 中添加外部连接：
  URL: http://<服务器IP>:9099/v1
  Key: 留空（除非设置了 BRIDGE_API_KEY）
"""

import os, sys, json, uuid, time, subprocess, asyncio, logging
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

# ── 配置 ──
HOST = os.environ.get("BRIDGE_HOST", "0.0.0.0")
PORT = int(os.environ.get("BRIDGE_PORT", "9099"))
API_KEY = os.environ.get("BRIDGE_API_KEY", "")
HERMES_HOME = os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))
HERMES_VENV_PYTHON = os.path.join(HERMES_HOME, "venv", "bin", "python3")

# 可用的模型映射（provider + model 参数传给 Hermes CLI）
# 如需添加更多模型，在此扩展
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("hermes-bridge")

app = FastAPI(title="Hermes Bridge (OpenAI Compatible)")

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "deepseek-chat"
    messages: list[ChatMessage]
    stream: bool = False

class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int = 0
    owned_by: str = "hermes-agent"

# ── 安全中间件 ──
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if API_KEY and request.url.path not in ("/v1/models", "/health", "/"):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer ") or auth.removeprefix("Bearer ") != API_KEY:
            return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    return await call_next(request)

# ── 核心：调用 Hermes CLI ──
def call_hermes(provider: str, model: str, user_message: str) -> str:
    """通过 Hermes CLI 单次 -q 调用获取回复（无工具调用，纯文本）。"""
    cfg = MODEL_MAP.get(provider if provider in MODEL_MAP else "deepseek-chat", {})
    prov = cfg.get("provider", provider)
    mdl = cfg.get("model", model)

    cmd = [HERMES_VENV_PYTHON, "-m", "hermes_cli.main", "chat", "-q", user_message,
           "--provider", prov, "--model", mdl, "-Q"]
    env = os.environ.copy()
    env["HERMES_HOME"] = HERMES_HOME

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=env,
                                 cwd=os.path.expanduser("~"))
        return (result.stdout or result.stderr or "").strip()
    except subprocess.TimeoutExpired:
        return "请求超时，请重试。"
    except Exception as e:
        return f"处理请求时出错: {e}"

# ── API 端点 ──
@app.get("/")
async def root():
    return {"service": "Hermes Bridge", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/v1/models")
async def list_models():
    return {"object": "list", "data": [ModelInfo(id=mid, owned_by="hermes-agent") for mid in MODEL_MAP]}

@app.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest):
    user_message = next((m.content for m in req.messages if m.role == "user"), "")
    if not user_message:
        raise HTTPException(status_code=400, detail="No user message provided")

    if req.stream:
        return StreamingResponse(
            _stream_response(req.model, user_message),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
        )

    content = call_hermes(req.model, req.model, user_message)
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": req.model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }

async def _stream_response(model: str, user_message: str):
    content = call_hermes(model, model, user_message)
    response_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    for i in range(0, len(content), 20):
        chunk = content[i:i+20]
        yield f"data: {json.dumps({'id': response_id, 'object':'chat.completion.chunk','created':int(time.time()),'model':model,'choices':[{'index':0,'delta':{'content':chunk},'finish_reason':None}]}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.02)
    yield f"data: {json.dumps({'id': response_id, 'object':'chat.completion.chunk','created':int(time.time()),'model':model,'choices':[{'index':0,'delta':{},'finish_reason':'stop'}]}, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"

if __name__ == "__main__":
    log.info("Hermes Bridge — OpenAI Compatible API on :%s", PORT)
    log.info("Models: %s", ", ".join(MODEL_MAP.keys()))
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
