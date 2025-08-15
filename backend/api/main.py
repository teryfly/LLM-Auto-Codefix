from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
from pathlib import Path
# Add src to path
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))
from .endpoints import workflow_api, pipeline_api, config_api, gitlab_api
app = FastAPI(title="LLM CI/CD API", version="1.0.0")
# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Include routers
app.include_router(workflow_api.router, prefix="/api/v1", tags=["workflow"])
app.include_router(pipeline_api.router, prefix="/api/v1", tags=["pipeline"])
app.include_router(config_api.router, prefix="/api/v1", tags=["config"])
app.include_router(gitlab_api.router, prefix="/api/v1", tags=["gitlab"])
@app.get("/")
async def root():
    return {"message": "LLM CI/CD API is running"}
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)