# controller/source_code_controller.py
import os
import sys
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

    def get_project_source_from_ai_dir(self):
        """
        从 ai_work_dir 获取项目源代码 (使用 source-code-concatenator API)
        """
        try:
            # 使用 source-code-concatenator API
            from code_project_reader.api import get_project_document
            ai_work_dir = self.config.paths.ai_work_dir
            absolute_path = os.path.abspath(ai_work_dir)
            logger.info(f"从 ai_work_dir 获取源代码: {absolute_path}")
            print(f"📁 从 {absolute_path} 获取项目源代码...", flush=True)
            result = get_project_document(absolute_path, save_output=False)
            document_content = result["content"]
            metadata = result["metadata"]
            logger.info(f"源代码获取成功 - 项目: {metadata['project_name']}, 总行数: {metadata['total_lines']}")
            print(f"✅ 源代码获取成功 - 项目: {metadata['project_name']}, 总行数: {metadata['total_lines']}", flush=True)
            return document_content
        except ImportError as e:
            error_msg = "source-code-concatenator 库未安装，请先安装: pip install /path/to/source-code-concatenator"
            logger.error(error_msg)
            print(f"❌ {error_msg}", flush=True)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"获取项目源代码失败: {e}"
            logger.error(error_msg)
            print(f"❌ {error_msg}", flush=True)
            raise RuntimeError(error_msg)

    def apply_fixed_code_with_executor(self, fixed_code: str):
        """
        使用 codefileexecutorlib 应用修复的代码

        Returns:
            (bool, list[str]): 
                - 第一个返回值表示是否成功应用至少一个修复且无错误
                - 第二个返回值为执行过程中收集的输出行（用于上游作为 commit 注释提取步骤行）
        """
        try:
            from codefileexecutorlib import CodeFileExecutor
            ai_work_dir = self.config.paths.ai_work_dir
            absolute_path = os.path.abspath(ai_work_dir)
            logger.info(f"使用 codefileexecutorlib 应用修复代码到: {absolute_path}")
            print(f"💾 应用修复代码到: {absolute_path}", flush=True)

            executor = CodeFileExecutor(log_level="ERROR", backup_enabled=False)

            has_error = False
            success_count = 0
            total_count = 0
            collected_output_lines = []

            for stream in executor.codeFileExecutHelper(absolute_path, fixed_code):
                stream_type = stream.get('type', 'info')
                message = stream.get('message', '')
                timestamp = stream.get('timestamp', '')

                # 统一收集一份纯文本行，供上层用于提取 commit 备注
                text_line = f"[{stream_type.upper()}] {message}"
                collected_output_lines.append(text_line)

                # 打印来自执行器的日志信息
                print(text_line, flush=True)
                logger.info(f"CodeFileExecutor: [{stream_type}] {message}")

                if stream_type == 'summary':
                    data = stream.get('data', {})
                    total_count = data.get('total_tasks', 0)
                    success_count = data.get('successful_tasks', 0)
                    failed_count = data.get('failed_tasks', 0)
                    execution_time = data.get('execution_time', 'N/A')
                    summary_line = f"📊 执行汇总: 总任务 {total_count}, 成功 {success_count}, 失败 {failed_count}, 用时 {execution_time}"
                    print(summary_line, flush=True)
                    collected_output_lines.append(summary_line)
                    logger.info(f"CodeFileExecutor 执行汇总: 总任务 {total_count}, 成功 {success_count}, 失败 {failed_count}")
                    if failed_count > 0:
                        has_error = True
                elif stream_type == 'error':
                    has_error = True
                    logger.error(f"CodeFileExecutor 执行出错: {message}")

            # 汇总成功/失败
            if has_error:
                error_msg = "codefileexecutorlib 执行过程中出现错误"
                logger.error(error_msg)
                print(f"❌ {error_msg}", flush=True)
                print("🚨 按要求，codefileexecutorlib出错则退出程序", flush=True)
                sys.exit(1)

            if success_count > 0:
                logger.info(f"成功应用 {success_count} 个代码修复任务")
                print(f"✅ 成功应用 {success_count} 个代码修复任务", flush=True)
                return True, collected_output_lines
            else:
                logger.warning("没有成功应用任何代码修复任务")
                print("⚠️ 没有成功应用任何代码修复任务", flush=True)
                return False, collected_output_lines

        except ImportError as e:
            error_msg = "codefileexecutorlib 库未安装，请先安装相关依赖"
            logger.error(error_msg)
            print(f"❌ {error_msg}", flush=True)
            print("🚨 按要求，codefileexecutorlib出错则退出程序", flush=True)
            sys.exit(1)
        except Exception as e:
            error_msg = f"codefileexecutorlib 执行失败: {e}"
            logger.error(error_msg)
            print(f"❌ {error_msg}", flush=True)
            print("🚨 按要求，codefileexecutorlib出错则退出程序", flush=True)
            sys.exit(1)