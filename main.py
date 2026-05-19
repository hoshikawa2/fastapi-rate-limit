from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.extension import _rate_limit_exceeded_handler

import asyncio
import uvicorn

# =========================================================
# RATE LIMIT KEY
# =========================================================

def rate_limit_key(request: Request):
    session_id = request.headers.get("X-Session-Id")

    if session_id:
        return session_id

    return get_remote_address(request)


# =========================================================
# LIMITER
# =========================================================

limiter = Limiter(key_func=rate_limit_key)

# =========================================================
# FASTAPI
# =========================================================

app = FastAPI()

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)

app.add_middleware(SlowAPIMiddleware)

# =========================================================
# CONCURRENCY CONTROL
# =========================================================

WORKFLOW_SEMAPHORE = asyncio.Semaphore(2)
SSE_SEMAPHORE = asyncio.Semaphore(1)

# =========================================================
# WORKFLOW ENDPOINT
# =========================================================

@app.post("/workflows/run")
@limiter.limit("2/minute")
async def run_workflow(request: Request):

    async with WORKFLOW_SEMAPHORE:

        print("WORKFLOW START")

        await asyncio.sleep(5)

        print("WORKFLOW END")

        return {
            "status": "SUCCESS",
            "message": "Workflow executado"
        }

# =========================================================
# SSE GENERATOR
# =========================================================

async def event_generator():

    for i in range(10):
        yield f"data: evento {i}\n\n"
        await asyncio.sleep(1)

# =========================================================
# SSE ENDPOINT
# =========================================================

@app.get("/agent/sse")
@limiter.limit("2/minute")
async def sse(request: Request):

    async with SSE_SEMAPHORE:

        print("SSE START")

        response = StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )

        return response

# =========================================================
# HEALTHCHECK
# =========================================================

@app.get("/health")
async def health():
    return {"status": "ok"}

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )