# controller/main_workflow/step_debug_loop.py

import time
from controller.pipeline_monitor_controller import PipelineMonitorController
from controller.trace_controller import TraceController
from controller.source_code_controller import SourceCodeController
from controller.prompt_controller import PromptController
from controller.llm_controller import LLMController
from controller.grpc_controller import GrpcController
from controller.loop_controller import LoopController
from clients.logging.logger import logger

def run_debug_loop(config, project_info, mr):
    pipeline_monitor = PipelineMonitorController(config)
    trace_ctrl = TraceController()
    source_ctrl = SourceCodeController(config)
    prompt_ctrl = PromptController()
    llm_ctrl = LLMController(config)
    grpc_ctrl = GrpcController(config)
    loop_ctrl = LoopController(config)

    def loop_body(debug_idx):
        status, jobs = pipeline_monitor.monitor(project_info["project_id"], project_info["pipeline_id"])
        if status == "success":
            return True
        if status == "failed":
            trace = trace_ctrl.get_failed_trace(project_info["project_id"], jobs)
            source_code = source_ctrl.get_failed_source_codes(project_info["project_name"])
            prompt = prompt_ctrl.build_fix_prompt(trace, source_code)
            fixed_code = llm_ctrl.fix_code_with_llm(prompt)
            return grpc_ctrl.run_plan(fixed_code, project_info["project_name"])
        time.sleep(10)
        return False

    loop_ctrl.run_with_timeout(loop_body)
