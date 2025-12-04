# app/main.py

import uuid
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.chat_router import router as chat_router
from app.api.routes.session import router as session_router
from app.core.logging import log_info, log_error

app = FastAPI(
    title="Notebook LM - Agentic RAG Backend",
    version="1.0.0",
    description="Backend powering Query Understanding -> Retrieval -> Response Synthesis"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(session_router)

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    trace_id = str(uuid.uuid4())
    start_time = time.time()

    # Log incoming request
    log_info(
        f"Incoming request: {request.method} {request.url.path}",
        trace_id=trace_id
    )

    try:
        response = await call_next(request)

    except Exception as e:
        # Log error
        log_error(
            f"Unhandled exception: {str(e)} | path={request.url.path}",
            trace_id=trace_id
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "trace_id": trace_id,
                "details": str(e)
            }
        )

    # Log response time
    elapsed = round((time.time() - start_time) * 1000, 2)

    log_info(
        f"Completed request: {request.method} {request.url.path} ({elapsed} ms)",
        trace_id=trace_id
    )

    # Attach trace ID to response
    response.headers["X-Trace-ID"] = trace_id

    return response


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "message": "Notebook LM Backend Running"
    }

@app.get("/")
async def home():
    return {
        "status": "ok",
        "message": "Intellisense-AI Backend Running"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    trace_id = request.headers.get("X-Trace-ID", "none")

    log_error(
        f"GLOBAL ERROR: {exc} | path={request.url.path}",
        trace_id=trace_id
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "trace_id": trace_id,
            "details": str(exc)
        }
    )


__all__ = ["app"]
