# main.py

import sys
from config.config_manager import ConfigManager
from config.config_validator import validate_config
from utils.helpers import exit_with_error
from controller.main_controller import MainController

BANNER = r"""
===============================================================
   LLM-Auto-Codefix CI/CD Pipeline Orchestrator (for GitLab)
===============================================================
"""

def main():
    print(BANNER)
    print("[INFO] Loading configuration from config.yaml ...")
    try:
        config = ConfigManager.load_config("config.yaml")
        validate_config(config)
        print("[SUCCESS] Configuration loaded and validated.")
    except Exception as e:
        exit_with_error(f"[FATAL] Configuration error: {e}")

    print("[INFO] Initializing workflow controller ...")
    try:
        controller = MainController(config)
        print("[INFO] Starting main workflow ...")
        controller.run()
        print("\n[FINISH] All tasks completed successfully.\n")
    except KeyboardInterrupt:
        print("\n[ABORT] User interrupted execution.")
        sys.exit(130)
    except Exception as e:
        print(f"\n[FAIL] {e}\n")
        exit_with_error(f"[FATAL] Unhandled error: {e}")

    print("Thank you for using LLM-Auto-Codefix!\n"
          "For logs and trace information, check the logs directory or designated output files.\n")

if __name__ == "__main__":
    main()