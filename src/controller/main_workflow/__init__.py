# controller/main_workflow/__init__.py

from .step_prepare_project import prepare_project
from .step_create_mr import create_merge_request
from .step_debug_loop import run_debug_loop
from .step_merge_mr import merge_mr_and_wait_pipeline
from .step_post_merge_monitor import monitor_post_merge_pipeline
from .step_load_config import load_and_validate_config, get_config
from .step_display_banner import display_application_banner, display_completion_message, display_custom_banner
from .step_error_handling import (
    handle_fatal_error,
    handle_workflow_error,
    safe_execute_step,
    handle_keyboard_interrupt,
    handle_unhandled_error
)

# These imports are kept separate to avoid circular imports
def get_init_controller_functions():
    from .step_init_controller import initialize_workflow_controller, create_controller_with_config
    return initialize_workflow_controller, create_controller_with_config

def get_execute_workflow_functions():
    from .step_execute_workflow import execute_main_workflow, run_workflow_with_error_handling
    return execute_main_workflow, run_workflow_with_error_handling

def get_app_lifecycle_functions():
    from .step_app_lifecycle import (
        initialize_application,
        run_application_workflow,
        finalize_application,
        run_complete_application
    )
    return initialize_application, run_application_workflow, finalize_application, run_complete_application

__all__ = [
    # Core workflow steps
    "prepare_project",
    "create_merge_request",
    "run_debug_loop",
    "merge_mr_and_wait_pipeline",
    "monitor_post_merge_pipeline",
    
    # Configuration steps
    "load_and_validate_config",
    "get_config",
    
    # Display steps
    "display_application_banner",
    "display_completion_message",
    "display_custom_banner",
    
    # Error handling steps
    "handle_fatal_error",
    "handle_workflow_error",
    "safe_execute_step",
    "handle_keyboard_interrupt",
    "handle_unhandled_error",
    
    # Function getters to avoid circular imports
    "get_init_controller_functions",
    "get_execute_workflow_functions",
    "get_app_lifecycle_functions"
]