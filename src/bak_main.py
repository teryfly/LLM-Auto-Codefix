# main.py

import sys
from clients.logging.logger import logger

BANNER = r"""
===============================================================
   LLM-Auto-Codefix CI/CD Pipeline Orchestrator (for GitLab)
===============================================================
"""

def main():
    """
    主程序入口点
    使用重构后的步骤模块来执行完整的应用程序生命周期
    """
    try:
        # 显示横幅
        print(BANNER)
        
        # 延迟导入避免循环导入问题
        from controller.main_workflow.step_load_config import load_and_validate_config
        from controller.main_workflow.step_init_controller import initialize_workflow_controller
        from controller.main_workflow.step_execute_workflow import execute_main_workflow
        from controller.main_workflow.step_error_handling import handle_fatal_error
        
        print("[INFO] Loading configuration from config.yaml ...")
        config = load_and_validate_config("config.yaml")
        
        print("[INFO] Initializing workflow controller ...")
        controller = initialize_workflow_controller(config)
        
        print("[INFO] Starting main workflow ...")
        result = execute_main_workflow(controller)
        
        print("\n[FINISH] All tasks completed successfully.\n")
        print("Thank you for using LLM-Auto-Codefix!\n"
              "For logs and trace information, check the logs directory or designated output files.\n")
        
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n[ABORT] User interrupted execution.")
        logger.warning("User interrupted execution")
        sys.exit(130)
        
    except Exception as e:
        print(f"\n[FAIL] {e}\n")
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()