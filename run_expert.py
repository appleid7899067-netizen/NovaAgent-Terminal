"""Run the isolated Expert API with safe loopback defaults."""

import os

import uvicorn
from fastapi import FastAPI

from expert_system.api import router


app = FastAPI(
    title="Expert Orchestrator API",
    docs_url=None if os.environ.get("EXPERT_API_DOCS", "0") != "1" else "/docs",
    redoc_url=None if os.environ.get("EXPERT_API_DOCS", "0") != "1" else "/redoc",
    openapi_url=None if os.environ.get("EXPERT_API_DOCS", "0") != "1" else "/openapi.json",
)
app.include_router(router)


if __name__ == "__main__":
    host = os.environ.get("EXPERT_API_HOST", "127.0.0.1")
    port = int(os.environ.get("EXPERT_API_PORT", "8001"))
    print(f"🚀 Expert API listening on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)
