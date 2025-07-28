# controller/main_controller.py
from controller.main_workflow.step_prepare_project import prepare_project
from controller.main_workflow.step_create_mr import create_merge_request
from controller.main_workflow.step_debug_loop import run_debug_loop
from controller.main_workflow.step_merge_mr import merge_mr_and_wait_pipeline
from controller.main_workflow.step_post_merge_monitor import monitor_post_merge_pipeline

class MainController:
    def __init__(self, config):
        self.config = config

    def run(self):
        project_info = prepare_project(self.config)
        mr = create_merge_request(self.config, project_info)
        run_debug_loop(self.config, project_info, mr)
        merge_mr_and_wait_pipeline(self.config, project_info, mr)
        monitor_post_merge_pipeline(self.config, project_info)