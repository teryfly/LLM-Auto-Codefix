import asyncio
import logging
from typing import Optional
from datetime import datetime
import sys
from pathlib import Path
import subprocess
import os
import threading
import time

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
        self.is_running = False
        self.stop_requested = False
        self.logs = []
        self.process = None
        self.error_monitor_thread = None
        self.stop_monitoring = False

    async def execute(self):
        """Execute the complete workflow"""
        try:
            self.is_running = True
            self.workflow_state.status = "running"
            self.add_log("Workflow execution started")

            # 启动错误监控线程
            self.start_error_monitoring()

            # Execute each step
            await self._execute_step("prepare_project")
            if self.stop_requested:
                return

            await self._execute_step("create_mr")
            if self.stop_requested:
                return

            await self._execute_step("debug_loop")
            if self.stop_requested:
                return

            await self._execute_step("merge_mr")
            if self.stop_requested:
                return

            await self._execute_step("post_merge_monitor")

            # Workflow completed successfully
            self.workflow_state.status = "completed"
            self.workflow_state.completed_at = datetime.utcnow()
            self.add_log("Workflow completed successfully")

        except Exception as e:
            self.workflow_state.status = "failed"
            self.workflow_state.error_message = str(e)
            self.workflow_state.completed_at = datetime.utcnow()
            self.add_log(f"Workflow failed: {e}")
            logger.error(f"Workflow execution failed for session {self.session_id}: {e}", exc_info=True)
        finally:
            self.is_running = False
            self.stop_monitoring = True
            if self.error_monitor_thread and self.error_monitor_thread.is_alive():
                self.error_monitor_thread.join(timeout=2)

    def start_error_monitoring(self):
        """启动错误监控线程"""
        self.error_monitor_thread = threading.Thread(
            target=self._monitor_subprocess_errors,
            daemon=True
        )
        self.error_monitor_thread.start()

    def _monitor_subprocess_errors(self):
        """监控子进程输出中的错误"""
        fatal_keywords = [
            "fatal:",
            "fatal error",
            "unencrypted http is not supported",
            "authentication failed",
            "permission denied",
            "repository not found",
            "connection refused",
            "access denied",
            "could not read from remote repository",
            "repository does not exist"
        ]

        while not self.stop_monitoring and self.is_running:
            try:
                # 检查最近的日志条目
                recent_logs = self.logs[-10:] if len(self.logs) > 10 else self.logs
                
                for log_entry in recent_logs:
                    log_lower = log_entry.lower()
                    for keyword in fatal_keywords:
                        if keyword in log_lower:
                            error_msg = f"Fatal error detected: {log_entry.strip()}"
                            logger.error(f"Fatal error detected in session {self.session_id}: {error_msg}")
                            
                            # 更新工作流状态
                            self.workflow_state.status = "failed"
                            self.workflow_state.error_message = error_msg
                            self.workflow_state.completed_at = datetime.utcnow()
                            
                            # 更新当前步骤状态
                            current_step = self.workflow_state.current_step
                            if current_step in self.workflow_state.steps:
                                self.workflow_state.steps[current_step].status = StepStatus.FAILED
                                self.workflow_state.steps[current_step].error_message = error_msg
                                self.workflow_state.steps[current_step].completed_at = datetime.utcnow()
                            
                            self.add_log(f"FATAL ERROR: {error_msg}")
                            self.stop(force=True)
                            return

                time.sleep(2)  # 每2秒检查一次
                
            except Exception as e:
                logger.error(f"Error in subprocess error monitoring: {e}")
                time.sleep(2)

    async def _execute_step(self, step_name: str):
        """Execute a single workflow step"""
        if self.stop_requested:
            return

        self.workflow_state.current_step = step_name
        step = self.workflow_state.steps[step_name]
        step.status = StepStatus.RUNNING
        step.started_at = datetime.utcnow()
        self.workflow_state.updated_at = datetime.utcnow()

        self.add_log(f"Starting step: {step.display_name}")

        try:
            # Execute step using the bridge
            result = await self.bridge.execute_step(step_name, self.workflow_state, self.request)

            # Update workflow state with step result
            if result and isinstance(result, dict):
                if "project_info" in result:
                    self.workflow_state.project_info = result["project_info"]
                if "pipeline_info" in result:
                    self.workflow_state.pipeline_info = result["pipeline_info"]
                if "merge_request" in result:
                    if not self.workflow_state.pipeline_info:
                        self.workflow_state.pipeline_info = {}
                    self.workflow_state.pipeline_info["merge_request"] = result["merge_request"]

            step.status = StepStatus.COMPLETED
            step.completed_at = datetime.utcnow()
            self.add_log(f"Completed step: {step.display_name}")

        except Exception as e:
            step.status = StepStatus.FAILED
            step.completed_at = datetime.utcnow()
            step.error_message = str(e)
            self.add_log(f"Step failed: {step.display_name} - {e}")
            
            # 检查是否是fatal错误
            error_str = str(e).lower()
            fatal_keywords = ["fatal", "authentication failed", "permission denied", "repository not found"]
            if any(keyword in error_str for keyword in fatal_keywords):
                self.workflow_state.status = "failed"
                self.workflow_state.error_message = str(e)
                self.workflow_state.completed_at = datetime.utcnow()
                self.add_log(f"FATAL ERROR in step {step_name}: {e}")
            
            raise

    def get_current_state(self) -> WorkflowState:
        """Get current workflow state"""
        return self.workflow_state

    def stop(self, force: bool = False):
        """Stop the workflow execution"""
        self.stop_requested = True
        self.stop_monitoring = True
        self.add_log(f"Workflow stop requested (force={force})")
        
        if force:
            self.workflow_state.status = "cancelled"
            self.workflow_state.completed_at = datetime.utcnow()
            
        # 如果有子进程在运行，终止它
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                time.sleep(2)
                if self.process.poll() is None:
                    self.process.kill()
            except Exception as e:
                logger.error(f"Error terminating subprocess: {e}")

    def is_completed(self) -> bool:
        """Check if workflow is completed"""
        return self.workflow_state.status in ["completed", "failed", "cancelled"]

    def get_logs(self, offset: int = 0, limit: int = 100) -> list:
        """Get workflow execution logs"""
        return self.logs[offset:offset+limit]

    def add_log(self, message: str):
        """Add a log entry"""
        timestamp = datetime.utcnow().isoformat()
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        self.workflow_state.add_log(message)
        logger.info(f"[{self.session_id}] {message}")
        
        # 立即检查是否包含fatal错误
        message_lower = message.lower()
        fatal_keywords = ["fatal:", "fatal error", "unencrypted http", "authentication failed"]
        if any(keyword in message_lower for keyword in fatal_keywords):
            self.workflow_state.status = "failed"
            self.workflow_state.error_message = message
            self.workflow_state.completed_at = datetime.utcnow()
            
            # 更新当前步骤状态
            current_step = self.workflow_state.current_step
            if current_step in self.workflow_state.steps:
                self.workflow_state.steps[current_step].status = StepStatus.FAILED
                self.workflow_state.steps[current_step].error_message = message
                self.workflow_state.steps[current_step].completed_at = datetime.utcnow()