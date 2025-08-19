import asyncio
import logging
from typing import Dict, Any, Optional
import sys
from pathlib import Path
from datetime import datetime
import subprocess
import threading
import queue
import time
# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))
from config.config_models import AppConfig
from models.web.api_models import WorkflowStartRequest, WorkflowStatusResponse
from models.web.workflow_models import WorkflowState, WorkflowStep
from services.web.session_service import SessionService
from services.background.workflow_executor import WorkflowExecutor
logger = logging.getLogger("workflow_service")
class WorkflowService:
    def __init__(self, config: AppConfig, session_service: SessionService):
        self.config = config
        self.session_service = session_service
        self.active_workflows: Dict[str, WorkflowExecutor] = {}
        # MR ID到Session ID的映射
        self.mr_to_session_mapping: Dict[str, str] = {}
        # 错误监控
        self.workflow_errors: Dict[str, str] = {}
    def start_workflow(self, session_id: str, request: WorkflowStartRequest) -> None:
        """Start a new workflow execution"""
        if session_id in self.active_workflows:
            raise ValueError(f"Workflow already running for session {session_id}")
        # Create workflow executor
        executor = WorkflowExecutor(self.config, session_id, request)
        self.active_workflows[session_id] = executor
        # Update session with initial workflow state
        self.session_service.update_session(
            session_id, 
            workflow_state=executor.get_current_state()
        )
        # Start workflow in background with error monitoring
        asyncio.create_task(self._run_workflow_with_monitoring(session_id, executor))
        logger.info(f"Workflow started for session {session_id}")
    async def _run_workflow_with_monitoring(self, session_id: str, executor: WorkflowExecutor):
        """Run workflow in background with error monitoring"""
        try:
            # 启动错误监控线程
            error_monitor = threading.Thread(
                target=self._monitor_workflow_errors,
                args=(session_id, executor),
                daemon=True
            )
            error_monitor.start()
            await executor.execute()
            # 执行完成后，如果有MR信息，建立映射关系
            final_state = executor.get_current_state()
            if (final_state.pipeline_info and 
                final_state.pipeline_info.get('merge_request') and
                final_state.project_info and
                final_state.project_info.get('project_name')):
                mr_info = final_state.pipeline_info['merge_request']
                project_name = final_state.project_info['project_name']
                mr_id = str(mr_info.get('iid') or mr_info.get('id'))
                if mr_id:
                    mr_key = f"{project_name}:{mr_id}"
                    self.mr_to_session_mapping[mr_key] = session_id
                    logger.info(f"Established MR mapping: {mr_key} -> {session_id}")
        except Exception as e:
            logger.error(f"Workflow execution failed for session {session_id}: {e}")
            # 记录错误信息
            self.workflow_errors[session_id] = str(e)
            # 更新workflow状态为failed
            try:
                current_state = executor.get_current_state()
                current_state.status = "failed"
                current_state.error_message = str(e)
                self.session_service.update_session(
                    session_id, 
                    workflow_state=current_state
                )
            except Exception as update_error:
                logger.error(f"Failed to update session state after error: {update_error}")
        finally:
            # Update session with final workflow state
            try:
                self.session_service.update_session(
                    session_id, 
                    workflow_state=executor.get_current_state()
                )
            except Exception as e:
                logger.error(f"Failed to update session state for {session_id}: {e}")
            # Clean up completed workflow
            if session_id in self.active_workflows:
                del self.active_workflows[session_id]
    def _monitor_workflow_errors(self, session_id: str, executor: WorkflowExecutor):
        """Monitor workflow logs for fatal errors"""
        fatal_keywords = [
            "fatal:",
            "FATAL",
            "fatal error",
            "Unencrypted HTTP is not supported",
            "Authentication failed",
            "Permission denied",
            "Repository not found",
            "Connection refused"
        ]
        check_interval = 2  # 每2秒检查一次
        last_log_count = 0
        while session_id in self.active_workflows:
            try:
                current_state = executor.get_current_state()
                current_logs = current_state.logs
                # 检查新增的日志
                if len(current_logs) > last_log_count:
                    new_logs = current_logs[last_log_count:]
                    for log_entry in new_logs:
                        log_lower = log_entry.lower()
                        for keyword in fatal_keywords:
                            if keyword.lower() in log_lower:
                                error_msg = f"Fatal error detected: {log_entry.strip()}"
                                logger.error(f"Fatal error detected in session {session_id}: {error_msg}")
                                # 停止工作流
                                executor.stop(force=True)
                                # 更新状态
                                current_state.status = "failed"
                                current_state.error_message = error_msg
                                self.workflow_errors[session_id] = error_msg
                                # 更新session
                                try:
                                    self.session_service.update_session(
                                        session_id,
                                        workflow_state=current_state
                                    )
                                except Exception as e:
                                    logger.error(f"Failed to update session after fatal error: {e}")
                                return  # 退出监控
                    last_log_count = len(current_logs)
                time.sleep(check_interval)
            except Exception as e:
                logger.error(f"Error in workflow error monitoring: {e}")
                time.sleep(check_interval)
    def get_workflow_status(self, session_id: str) -> WorkflowStatusResponse:
        """Get current workflow status"""
        session = self.session_service.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        executor = self.active_workflows.get(session_id)
        if executor:
            # Workflow is running - get real-time state
            current_state = executor.get_current_state()
            # 检查是否有fatal错误
            if session_id in self.workflow_errors:
                current_state.status = "failed"
                current_state.error_message = self.workflow_errors[session_id]
            # Update session with current state
            try:
                self.session_service.update_session(
                    session_id, 
                    workflow_state=current_state
                )
            except Exception as e:
                logger.warning(f"Failed to update session state: {e}")
            # 增强pipeline_info以包含MR信息
            enhanced_pipeline_info = current_state.pipeline_info or {}
            if hasattr(executor, 'mr_info') and executor.mr_info:
                enhanced_pipeline_info['merge_request'] = {
                    'id': getattr(executor.mr_info, 'id', None),
                    'iid': getattr(executor.mr_info, 'iid', None),
                    'web_url': getattr(executor.mr_info, 'web_url', None),
                    'title': getattr(executor.mr_info, 'title', None)
                }
            return WorkflowStatusResponse(
                session_id=session_id,
                status=current_state.status,
                current_step=current_state.current_step,
                steps=current_state.steps,
                project_info=current_state.project_info,
                pipeline_info=enhanced_pipeline_info,
                error_message=current_state.error_message,
                started_at=current_state.started_at,
                updated_at=datetime.utcnow()
            )
        else:
            # Workflow completed or not started - get stored state
            workflow_state = session.workflow_state
            if workflow_state:
                # 检查是否有记录的错误
                if session_id in self.workflow_errors:
                    workflow_state.status = "failed"
                    workflow_state.error_message = self.workflow_errors[session_id]
                return WorkflowStatusResponse(
                    session_id=session_id,
                    status=workflow_state.status,
                    current_step=workflow_state.current_step,
                    steps=workflow_state.steps,
                    project_info=workflow_state.project_info,
                    pipeline_info=workflow_state.pipeline_info,
                    error_message=workflow_state.error_message,
                    started_at=workflow_state.started_at,
                    updated_at=workflow_state.updated_at
                )
            else:
                raise ValueError(f"No workflow state found for session {session_id}")
    def get_workflow_status_by_mr(self, project_name: str, mr_id: str) -> WorkflowStatusResponse:
        """Get workflow status by MR ID"""
        mr_key = f"{project_name}:{mr_id}"
        # 先查找映射关系
        session_id = self.mr_to_session_mapping.get(mr_key)
        if session_id:
            try:
                return self.get_workflow_status(session_id)
            except:
                # 如果session不存在，继续查找
                pass
        # 如果没有找到映射，搜索所有session
        all_sessions = self.session_service.list_active_sessions()
        for session_id, session in all_sessions.items():
            if (session.workflow_state and 
                session.workflow_state.pipeline_info and
                session.workflow_state.project_info):
                # 检查项目名称匹配
                if session.workflow_state.project_info.get('project_name') == project_name:
                    # 检查MR ID匹配
                    mr_info = session.workflow_state.pipeline_info.get('merge_request')
                    if mr_info:
                        stored_mr_id = str(mr_info.get('iid') or mr_info.get('id', ''))
                        if stored_mr_id == mr_id:
                            # 建立映射关系
                            self.mr_to_session_mapping[mr_key] = session_id
                            return self.get_workflow_status(session_id)
        # 如果都没找到，创建一个基于MR信息的状态响应
        return self._create_mr_based_status(project_name, mr_id)
    def _create_mr_based_status(self, project_name: str, mr_id: str) -> WorkflowStatusResponse:
        """创建基于MR信息的状态响应，用于恢复workflow状态"""
        from models.web.workflow_models import WorkflowStep, StepStatus
        # 创建默认的步骤状态
        steps = {
            "prepare_project": WorkflowStep(
                name="prepare_project",
                display_name="项目准备和代码同步",
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
        }
        # 尝试从GitLab API获取MR信息来推断状态
        try:
            current_step, updated_steps = self._determine_workflow_status_from_gitlab(
                project_name, mr_id, steps
            )
        except Exception as e:
            logger.warning(f"Failed to determine status from GitLab: {e}")
            current_step = "prepare_project"
            updated_steps = steps
        return WorkflowStatusResponse(
            session_id=f"mr-{project_name.replace('/', '-')}-{mr_id}",
            status="recovered",
            current_step=current_step,
            steps=updated_steps,
            project_info={"project_name": project_name},
            pipeline_info={"merge_request": {"iid": int(mr_id)}},
            error_message=None,
            started_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    def _determine_workflow_status_from_gitlab(self, project_name: str, mr_id: str, steps: Dict):
        """从GitLab API确定workflow状态"""
        from clients.gitlab.project_client import ProjectClient
        from clients.gitlab.merge_request_client import MergeRequestClient
        from clients.gitlab.pipeline_client import PipelineClient
        from models.web.workflow_models import StepStatus
        try:
            # 获取项目信息
            project_client = ProjectClient()
            project = project_client.get_project_by_name(project_name)
            if not project:
                return "prepare_project", steps
            # 项目存在，标记第一步完成
            steps["prepare_project"].status = StepStatus.COMPLETED
            # 检查MR是否存在
            mr_client = MergeRequestClient()
            try:
                mr = mr_client.get_merge_request(project.id, int(mr_id))
                if mr:
                    # MR存在，标记第二步完成
                    steps["create_mr"].status = StepStatus.COMPLETED
                    # 检查MR状态
                    if mr.state == "merged":
                        # MR已合并，标记调试循环和合并步骤完成
                        steps["debug_loop"].status = StepStatus.COMPLETED
                        steps["merge_mr"].status = StepStatus.COMPLETED
                        # 检查合并后的pipeline状态
                        pipeline_client = PipelineClient()
                        pipelines = pipeline_client.list_pipelines(project.id, ref="dev")
                        if pipelines:
                            latest_pipeline = pipelines[0]
                            if latest_pipeline.status in ["success", "passed"]:
                                steps["post_merge_monitor"].status = StepStatus.COMPLETED
                                return "post_merge_monitor", steps
                            elif latest_pipeline.status in ["running", "pending"]:
                                steps["post_merge_monitor"].status = StepStatus.RUNNING
                                return "post_merge_monitor", steps
                            else:
                                steps["post_merge_monitor"].status = StepStatus.FAILED
                                return "post_merge_monitor", steps
                        return "post_merge_monitor", steps
                    elif mr.state == "opened":
                        # MR打开状态，检查pipeline
                        pipeline_client = PipelineClient()
                        pipelines = pipeline_client.list_pipelines(project.id, ref="ai")
                        if pipelines:
                            latest_pipeline = pipelines[0]
                            if latest_pipeline.status in ["success", "passed"]:
                                steps["debug_loop"].status = StepStatus.COMPLETED
                                return "merge_mr", steps
                            elif latest_pipeline.status in ["running", "pending"]:
                                steps["debug_loop"].status = StepStatus.RUNNING
                                return "debug_loop", steps
                            else:
                                steps["debug_loop"].status = StepStatus.RUNNING
                                return "debug_loop", steps
                        else:
                            steps["debug_loop"].status = StepStatus.RUNNING
                            return "debug_loop", steps
                    return "create_mr", steps
                else:
                    return "create_mr", steps
            except:
                return "create_mr", steps
        except Exception as e:
            logger.error(f"Error determining status from GitLab: {e}")
            return "prepare_project", steps
    def stop_workflow(self, session_id: str, force: bool = False) -> None:
        """Stop a running workflow"""
        executor = self.active_workflows.get(session_id)
        if executor:
            executor.stop(force)
            logger.info(f"Workflow stop requested for session {session_id}")
        else:
            raise ValueError(f"No active workflow found for session {session_id}")
    def get_workflow_logs(self, session_id: str, offset: int = 0, limit: int = 100) -> list:
        """Get workflow execution logs"""
        session = self.session_service.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        # Get logs from executor or session
        executor = self.active_workflows.get(session_id)
        if executor:
            return executor.get_logs(offset, limit)
        else:
            # Return stored logs from session
            if session.workflow_state and session.workflow_state.logs:
                return session.workflow_state.logs[offset:offset+limit]
            return session.logs[offset:offset+limit] if session.logs else []
    def cleanup_completed_workflows(self) -> None:
        """Clean up completed workflow executors"""
        completed = []
        for session_id, executor in self.active_workflows.items():
            if executor.is_completed():
                completed.append(session_id)
        for session_id in completed:
            del self.active_workflows[session_id]
            logger.info(f"Cleaned up completed workflow for session {session_id}")