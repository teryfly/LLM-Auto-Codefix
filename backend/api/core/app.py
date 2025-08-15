from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import sys
from pathlib import Path
# Add src to path for importing existing modules
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))
from config.config_manager import ConfigManager
from .middleware import setup_middleware
from .exception_handlers import setup_exception_handlers
from .dependencies import get_config
from ..endpoints import (
    workflow_api,
    gitlab_proxy_api,
    pipeline_api,
    task_api,
    config_api,
    health_api,
    project_pipeline_api
)
def create_app() -> FastAPI:
    app = FastAPI(
        title="LLM-Auto-Codefix Web API",
        description="Web API for LLM-powered CI/CD code fixing",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc"
    )
    # Setup CORS - 允许前端跨域访问
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",      # Vite 开发服务器
            "http://127.0.0.1:3000",     # 本地访问
            "http://localhost:5174",     # Vite 默认端口
            "http://127.0.0.1:5173",     # 本地访问
            "*"                          # 开发环境允许所有源（生产环境请删除）
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    # Setup custom middleware
    setup_middleware(app)
    # Setup exception handlers
    setup_exception_handlers(app)
    # Include API routers
    app.include_router(workflow_api.router, prefix="/api/v1", tags=["workflow"])
    app.include_router(gitlab_proxy_api.router, prefix="/api/v1", tags=["gitlab"])
    app.include_router(pipeline_api.router, prefix="/api/v1", tags=["pipeline"])
    app.include_router(task_api.router, prefix="/api/v1", tags=["tasks"])
    app.include_router(config_api.router, prefix="/api/v1", tags=["config"])
    app.include_router(health_api.router, prefix="/api/v1", tags=["health"])
    app.include_router(project_pipeline_api.router, prefix="/api/v1", tags=["project-pipeline"])
    # Serve static files if frontend build exists
    frontend_build = project_root / "frontend" / "build"
    if frontend_build.exists():
        app.mount("/", StaticFiles(directory=str(frontend_build), html=True), name="frontend")
    return app
app = create_app()
if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )