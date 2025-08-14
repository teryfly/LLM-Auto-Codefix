import asyncio
import logging
from typing import Optional
from datetime import datetime
import sys
from pathlib import Path
# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))
from config.config_models import AppConfig
from models.web.api_models import WorkflowStartRequest
from models.web.workflow_models import WorkflowState, WorkflowStep, StepStatus
from controller.main_controller import MainController
from integration.workflow_bridge import WorkflowBridge
logger = logging.getLogger("workflow_executor")
class WorkflowExecutor:
    def __init__(self, config: AppConfig, session_id: str, request: WorkflowStartRequest):
        self.config = config
        self.session_id = session_id
        self.request = request
        self.workflow_state = WorkflowState(
            session_id=session_id,
            status="initializing",
            current_step="prepare_project",
            steps={
                "prepare_project": WorkflowStep(
                    name="prepare_project",
                    display_name="准备项目",
                    status=StepStatus.PENDING,
                    description="项目准备和代码同步"
                ),
                "create_mr": WorkflowStep(
                    name="create_mr",
                    display_name="创建合并请求",
                    status=StepStatus.PENDING,
                    description="创建MR并触发Pipeline"
                ),
                "debug_loop": WorkflowStep(
                    name="debug_loop",
                    display_name="调试循环",
                    status=StepStatus.PENDING,
                    description="监控Pipeline并执行LLM修复"
                ),
                "merge_mr": WorkflowStep(
                    name="merge_mr",
                    display_name="合并部署",
                    status=StepStatus.PENDING,
                    description="合并MR并等待部署Pipeline"
                ),
                "post_merge_monitor": WorkflowStep(
                    name="post_merge_monitor",
                    display_name="部署监控",
                    status=StepStatus.PENDING,
                    description="监控合并后的部署状态"
                )
            },
            started_at=datetime.utcnow()
        )
        self.bridge = WorkflowBridge(config)
        self.