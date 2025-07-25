# controller/source_code_controller.py

from operations.source.source_reader import SourceConcatenatorClient
from clients.logging.logger import logger

class SourceCodeController:
    def __init__(self, config):
        self.config = config
        self.concatenator = SourceConcatenatorClient(config.services.llm_url)

    def get_failed_source_codes(self, project_name):
        git_dir = self.config.paths.git_work_dir
        project_path = f"{git_dir}/{project_name}"
        result = self.concatenator.get_project_document(project_path)
        code = result.document
        logger.info(f"源码获取成功，长度: {len(code)}")
        return code