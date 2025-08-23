# operations/template/template_manager.py
import os
from clients.logging.logger import logger
class TemplateManager:
    def __init__(self):
        self.template_dir = os.path.dirname(__file__)
        self._cache = {}
    def _load_template_from_file(self, filename: str) -> str:
        """
        从文件加载模板内容
        Args:
            filename: 模板文件名
        Returns:
            str: 模板内容
        """
        if filename in self._cache:
            return self._cache[filename]
        template_path = os.path.join(self.template_dir, filename)
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self._cache[filename] = content
                logger.debug(f"加载模板文件成功: {template_path}")
                return content
        except FileNotFoundError:
            logger.error(f"模板文件不存在: {template_path}")
            raise FileNotFoundError(f"Template file not found: {template_path}")
        except Exception as e:
            logger.error(f"读取模板文件失败: {template_path}, 错误: {e}")
            raise RuntimeError(f"Failed to read template file: {template_path}, error: {e}")
    def get_fix_bug_prompt(self) -> str:
        """
        获取修复Bug的提示词模板
        Returns:
            str: 修复Bug提示词模板
        """
        return self._load_template_from_file('fix_bug_prompt.txt')
    def get_system_prompt(self) -> str:
        """
        获取系统提示词模板
        Returns:
            str: 系统提示词模板
        """
        return self._load_template_from_file('system_prompt.txt')
    def clear_cache(self):
        """
        清除模板缓存
        """
        self._cache.clear()
        logger.debug("模板缓存已清除")
    def reload_template(self, filename: str) -> str:
        """
        重新加载指定模板文件
        Args:
            filename: 模板文件名
        Returns:
            str: 模板内容
        """
        if filename in self._cache:
            del self._cache[filename]
        return self._load_template_from_file(filename)