# operations/template/prompt_builder.py
from .template_manager import TemplateManager
from clients.logging.logger import logger
import re

class PromptBuilder:
    def __init__(self):
        self.template_manager = TemplateManager()

    def extract_build_failed_content(self, trace: str) -> str:
        """
        从日志中提取 Build FAILED 之后的内容；若未找到：
        - 回退到查找包含 'FAILED' 的任意行，从该行（含）开始截取
        - 若仍未找到，则返回原始日志
        Args:
            trace: 完整的日志内容
        Returns:
            str: 截取后的日志内容
        """
        try:
            logger.debug("开始提取 Build FAILED/FAILED 之后的内容")
            lines = trace.split('\n')

            # 1) 优先查找 'Build FAILED'（不区分大小写）
            build_failed_index = -1
            for i, line in enumerate(lines):
                if re.search(r'build\s+failed', line, re.IGNORECASE):
                    build_failed_index = i
                    logger.debug(f"找到 Build FAILED 在第 {i+1} 行: {line.strip()}")
                    break
            if build_failed_index >= 0:
                failed_content = '\n'.join(lines[build_failed_index:])
                logger.info(f"成功提取 Build FAILED 后的内容，长度: {len(failed_content)}")
                return failed_content

            # 2) 若未找到，则查找包含 'FAILED' 的任意行
            generic_failed_index = -1
            for i, line in enumerate(lines):
                if re.search(r'\bFAILED\b', line, re.IGNORECASE):
                    generic_failed_index = i
                    logger.debug(f"找到 FAILED 在第 {i+1} 行: {line.strip()}")
                    break
            if generic_failed_index >= 0:
                failed_content = '\n'.join(lines[generic_failed_index:])
                logger.info(f"成功提取 FAILED 后的内容，长度: {len(failed_content)}")
                return failed_content

            # 3) 都未找到，返回原始内容
            logger.info("未找到 Build FAILED 或 FAILED 关键字，使用完整日志")
            return trace
        except Exception as e:
            logger.warning(f"提取 FAILED 内容时出错: {e}，使用完整日志")
            return trace

    def build_fix_bug_prompt(self, trace: str, source_code: str) -> str:
        """
        构建修复 bug 的提示词
        直接使用模板中定义的占位符进行替换
        Args:
            trace: 错误日志
            source_code: 源代码
        Returns:
            str: 构建好的提示词
        """
        try:
            logger.info("开始构建修复提示词")
            # 1. 提取 Build FAILED/FAILED 之后的内容
            filtered_trace = self.extract_build_failed_content(trace)
            logger.debug(f"过滤后的日志长度: {len(filtered_trace)}")
            # 2. 获取模板
            template = self.template_manager.get_fix_bug_prompt()
            logger.debug(f"模板长度: {len(template)}")
            # 3. 替换模板中的占位符
            final_prompt = template.replace("___SOURCE_CODE_PLACEHOLDER___", source_code)
            final_prompt = final_prompt.replace("___TRACE_CONTENT_PLACEHOLDER___", filtered_trace)
            logger.info(f"提示词构建成功，最终长度: {len(final_prompt)}")
            return final_prompt
        except Exception as e:
            logger.error(f"构建提示词时发生错误: {e}")
            # 备用方案：直接构建简单的提示词
            fallback_prompt = f"""请分析以下错误日志并提供修复方案：
--- ERROR TRACE BEGIN ---
{filtered_trace if 'filtered_trace' in locals() else trace}
--- ERROR TRACE END ---
--- SOURCE CODE BEGIN ---
{source_code}
--- SOURCE CODE END ---
请提供详细的修复建议和代码。"""
            logger.info("使用备用提示词格式")
            return fallback_prompt