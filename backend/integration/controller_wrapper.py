import logging
from typing import Dict, Any, Optional, Callable
from contextlib import contextmanager
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from config.config_models import AppConfig

logger = logging.getLogger("controller_wrapper")

class ControllerWrapper:
    """Wrapper for existing controllers to provide web-compatible interface"""

    def __init__(self, config: AppConfig):
        self.config = config
        self.log_capture = []
        self.progress_callback: Optional[Callable] = None

    def set_progress_callback(self, callback: Callable[[float, str], None]):
        """Set callback for progress updates"""
        self.progress_callback = callback

    def update_progress(self, progress: float, message: str):
        """Update progress and call callback if set"""
        if self.progress_callback:
            self.progress_callback(progress, message)
        logger.info(f"Progress: {progress:.1f}% - {message}")

    @contextmanager
    def capture_logs(self):
        """Context manager to capture logs during execution"""
        self.log_capture = []
        old_handler = None

        try:
            # Setup log capture
            import logging
            capture_handler = LogCaptureHandler(self.log_capture)
            root_logger = logging.getLogger()
            old_level = root_logger.level
            root_logger.addHandler(capture_handler)

            yield self.log_capture

        finally:
            # Cleanup
            if capture_handler in root_logger.handlers:
                root_logger.removeHandler(capture_handler)

    def wrap_input_project_controller(self):
        """Wrap input project controller for web use"""
        from controller.input_project_controller import InputProjectController

        class WebInputProjectController(InputProjectController):
            def __init__(self, wrapper):
                super().__init__()
                self.wrapper = wrapper

            def get_project_info(self, project_name: str = None):
                """Override to use provided project name instead of input"""
                if not project_name:
                    project_name = "ai/dotnet-ai-demo"

                self.wrapper.update_progress(10, f"Checking project: {project_name}")

                project = self.project_client.get_project_by_name(project_name)
                if not project:
                    raise ValueError(f"Project '{project_name}' not found")

                project_id = project.id if project else None
                encoded_path = project_name  # Simplified for web use

                self.wrapper.update_progress(20, "Project validation completed")

                return project_name, encoded_path, project, project_id

        return WebInputProjectController(self)

    def wrap_repo_sync_controller(self):
        """Wrap repo sync controller for web use"""
        from controller.repo_sync_controller import RepoSyncController

        class WebRepoSyncController(RepoSyncController):
            def __init__(self, config, wrapper):
                super().__init__(config)
                self.wrapper = wrapper

            def sync_repo(self, project_name):
                self.wrapper.update_progress(30, f"Syncing repository: {project_name}")
                result = super().sync_repo(project_name)
                self.wrapper.update_progress(50, "Repository sync completed")
                return result

        return WebRepoSyncController(self.config, self)

    def wrap_pipeline_monitor_controller(self):
        """Wrap pipeline monitor controller for web use"""
        from controller.pipeline_monitor_controller import PipelineMonitorController

        class WebPipelineMonitorController(PipelineMonitorController):
            def __init__(self, config, wrapper):
                super().__init__(config)
                self.wrapper = wrapper

            def monitor(self, project_id, pipeline_id):
                self.wrapper.update_progress(60, f"Monitoring pipeline: {pipeline_id}")

                # Override the monitoring logic to provide progress updates
                last_statuses = {}
                dot_counters = {}

                while True:
                    jobs = self.job_client.list_jobs(project_id, pipeline_id)
                    all_status = [j.status for j in jobs]

                    # Calculate progress based on job completion
                    total_jobs = len(jobs)
                    completed_jobs = len([j for j in jobs if j.status in ["success", "failed", "canceled"]])
                    progress = 60 + (completed_jobs / total_jobs * 30) if total_jobs > 0 else 60

                    self.wrapper.update_progress(progress, f"Pipeline progress: {completed_jobs}/{total_jobs} jobs completed")

                    # Check completion status
                    if all(s in ["success", "skipped", "canceled"] for s in all_status):
                        self.wrapper.update_progress(90, "Pipeline completed successfully")
                        return "success", jobs

                    if any(s in ["failed"] for s in all_status):
                        self.wrapper.update_progress(90, "Pipeline failed, entering debug mode")
                        return "failed", jobs

                    # Continue monitoring
                    import time
                    time.sleep(self.interval)

        return WebPipelineMonitorController(self.config, self)

    def get_captured_logs(self) -> list:
        """Get captured logs"""
        return self.log_capture.copy()

class LogCaptureHandler(logging.Handler):
    """Custom logging handler to capture logs in memory"""

    def __init__(self, log_list):
        super().__init__()
        self.log_list = log_list

    def emit(self, record):
        log_entry = self.format(record)
        self.log_list.append(log_entry)