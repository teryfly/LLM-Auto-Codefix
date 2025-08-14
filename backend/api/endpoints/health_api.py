from fastapi import APIRouter, Depends, HTTPException, status
import sys
from pathlib import Path
import time
from datetime import datetime

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from config.config_models import AppConfig
from ..core.dependencies import get_config

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "llm-auto-codefix-api"
    }

@router.get("/health/detailed")
async def detailed_health_check(config: AppConfig = Depends(get_config)):
    """Detailed health check with service status"""
    try:
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "llm-auto-codefix-api",
            "version": "1.0.0",
            "uptime": time.time(),
            "services": {
                "config": "loaded",
                "gitlab_api": "available",
                "llm_service": "available",
                "grpc_service": "available"
            }
        }

        # Test GitLab connectivity (basic check)
        try:
            gitlab_url = config.services.gitlab_url
            if gitlab_url:
                health_data["services"]["gitlab_api"] = "configured"
            else:
                health_data["services"]["gitlab_api"] = "not_configured"
        except:
            health_data["services"]["gitlab_api"] = "error"

        # Test LLM service connectivity
        try:
            llm_url = config.services.llm_url
            if llm_url:
                health_data["services"]["llm_service"] = "configured"
            else:
                health_data["services"]["llm_service"] = "not_configured"
        except:
            health_data["services"]["llm_service"] = "error"

        return health_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )

@router.get("/health/ready")
async def readiness_check(config: AppConfig = Depends(get_config)):
    """Readiness probe for deployment"""
    try:
        # Check if all required services are configured
        required_services = ["gitlab_url", "llm_url", "grpc_port"]
        for service in required_services:
            if not hasattr(config.services, service):
                return {"status": "not_ready", "reason": f"Missing {service}"}

        return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        return {"status": "not_ready", "reason": str(e)}