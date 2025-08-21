# controller/main_workflow/step_display_banner.py

from clients.logging.logger import logger

BANNER = r"""
===============================================================
   LLM-Auto-Codefix CI/CD Pipeline Orchestrator (for GitLab)
===============================================================
"""

COMPLETION_MESSAGE = """Thank you for using LLM-Auto-Codefix!
For logs and trace information, check the logs directory or designated output files.
"""

def display_application_banner() -> None:
    """
    显示应用程序启动横幅
    """
    print(BANNER)
    logger.info("Application banner displayed")

def display_completion_message() -> None:
    """
    显示应用程序完成消息
    """
    print(COMPLETION_MESSAGE)
    logger.info("Application completion message displayed")

def display_custom_banner(title: str, width: int = 63) -> None:
    """
    显示自定义横幅
    
    Args:
        title: 横幅标题
        width: 横幅宽度，默认63个字符
    """
    border = "=" * width
    padding = (width - len(title)) // 2
    padded_title = " " * padding + title + " " * padding
    
    if len(padded_title) < width:
        padded_title += " "
    
    banner = f"\n{border}\n{padded_title}\n{border}\n"
    print(banner)
    logger.info(f"Custom banner displayed: {title}")