# backend/api/endpoints/llm_api.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import Dict, Any
import sys
from pathlib import Path
import json

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from clients.llm.llm_client import LLMClient
from clients.gitlab.job_client import JobClient
from config.config_models import AppConfig
from ..core.dependencies import get_config

router = APIRouter()

@router.post("/llm/analyze-logs-stream")
async def analyze_logs_stream(
    request: Dict[str, Any],
    config: AppConfig = Depends(get_config)
):
    """流式分析Pipeline日志"""
    try:
        project_id = request.get("project_id")
        job_id = request.get("job_id")
        logs = request.get("logs")
        
        if not logs and project_id and job_id:
            # 如果没有直接提供日志，从GitLab获取
            job_client = JobClient()
            logs = job_client.get_job_trace(project_id, job_id)
        
        if not logs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No logs provided or found"
            )
        
        llm_client = LLMClient()
        
        def generate():
            try:
                for chunk in llm_client.analyze_pipeline_logs(logs):
                    # 使用Server-Sent Events格式
                    yield f"data: {json.dumps({'content': chunk, 'type': 'content'})}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'content': f'Error: {str(e)}', 'type': 'error'})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze logs: {str(e)}"
        )

@router.post("/llm/fix-code-stream")
async def fix_code_stream(
    request: Dict[str, Any],
    config: AppConfig = Depends(get_config)
):
    """流式代码修复"""
    try:
        prompt = request.get("prompt")
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prompt is required"
            )
        
        llm_client = LLMClient()
        
        def generate():
            try:
                for chunk in llm_client.fix_code_stream(prompt):
                    yield f"data: {json.dumps({'content': chunk, 'type': 'content'})}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'content': f'Error: {str(e)}', 'type': 'error'})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fix code: {str(e)}"
        )

@router.get("/llm/job-logs/{project_id}/{job_id}")
async def get_job_logs(
    project_id: int,
    job_id: int,
    config: AppConfig = Depends(get_config)
):
    """获取Job日志"""
    try:
        job_client = JobClient()
        logs = job_client.get_job_trace(project_id, job_id)
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job logs: {str(e)}"
        )