# controller/input_project_controller.py
from utils.url_utils import encode_project_path
from clients.gitlab.project_client import ProjectClient
from clients.logging.logger import logger
from utils.helpers import prompt_user
from utils.exceptions import ProjectNotFoundError
class InputProjectController:
    def __init__(self):
        self.project_client = ProjectClient()
    def get_project_info(self, project_name: str = None):
        """
        获取项目信息，支持传入项目名称（用于Web API）或交互式输入（用于控制台）
        """
        if not project_name:
            # 控制台模式：交互式输入
            default_name = "ai/dotnet-ai-demo"
            inp = input(f"输入平台项目组/项目名 ([默认为: {default_name}]: ").strip()
            project_name = inp if inp else default_name
        logger.info(f"Checking for project: {project_name}")
        encoded_path = encode_project_path(project_name)
        project = self.project_client.get_project_by_name(project_name)
        if not project:
            logger.error(f"Project '{project_name}' not found.")
            # Web API 模式：直接抛出异常，不进行交互式确认
            if project_name == "ai/dotnet-ai-demo":  # 如果是默认项目名，说明是Web API调用
                raise ProjectNotFoundError(f"Project '{project_name}' not found.")
            # 控制台模式：询问用户是否继续
            if not prompt_user(f"Project '{project_name}' not found. Continue anyway?"):
                raise ProjectNotFoundError(f"Project '{project_name}' not found.")
        else:
            logger.info(f"Project '{project_name}' found (or proceeding per user input).")
        project_id = project.id if project else None
        return project_name, encoded_path, project, project_id