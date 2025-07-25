# controller/input_project_controller.py

from utils.url_utils import encode_project_path
from clients.gitlab.project_client import ProjectClient
from clients.logging.logger import logger
from utils.helpers import prompt_user
from utils.exceptions import ProjectNotFoundError

class InputProjectController:
    def __init__(self):
        self.project_client = ProjectClient()

    def get_project_info(self):
        default_name = "ai/llm-cicd-tester"
        inp = input(f"输入平台项目组/项目名 ([默认为: {default_name}]: ").strip()
        project_name = inp if inp else default_name
        logger.info(f"Checking for project: {project_name}")
        encoded_path = encode_project_path(project_name)
        project = self.project_client.get_project_by_name(project_name)
        if not project:
            logger.error(f"Project '{project_name}' not found.")
            if not prompt_user(f"Project '{project_name}' not found. Continue anyway?"):
                raise ProjectNotFoundError(f"Project '{project_name}' not found.")
        else:
            logger.info(f"Project '{project_name}' found (or proceeding per user input).")
        project_id = project.id if project else None
        return project_name, encoded_path, project, project_id