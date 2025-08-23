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
        """
        try:
            from codefileexecutorlib import CodeFileExecutor
            ai_work_dir = self.config.paths.ai_work_dir
            absolute_path = os.path.abspath(ai_work_dir)
            logger.info(f"使用 codefileexecutorlib 应用修复代码到: {absolute_path}")
            print(f"💾 应用修复代码到: {absolute_path}", flush=True)
            # 创建执行器实例，设置为ERROR级别日志，禁用备份
            executor = CodeFileExecutor(log_level="ERROR", backup_enabled=False)
            # 执行代码修复
            has_error = False
            success_count = 0
            total_count = 0
            for stream in executor.codeFileExecutHelper(absolute_path, fixed_code):
                stream_type = stream.get('type', 'info')
                message = stream.get('message', '')
                timestamp = stream.get('timestamp', '')
                # 打印所有 codefileexecutorlib 的日志信息
                print(f"[{stream_type.upper()}] {message}", flush=True)
                logger.info(f"CodeFileExecutor: [{stream_type}] {message}")
                # 处理汇总信息
                if stream_type == 'summary':
                    data = stream.get('data', {})
                    total_count = data.get('total_tasks', 0)
                    success_count = data.get('successful_tasks', 0)
                    failed_count = data.get('failed_tasks', 0)
                    execution_time = data.get('execution_time', 'N/A')
                    print(f"📊 执行汇总: 总任务 {total_count}, 成功 {success_count}, 失败 {failed_count}, 用时 {execution_time}", flush=True)
                    logger.info(f"CodeFileExecutor 执行汇总: 总任务 {total_count}, 成功 {success_count}, 失败 {failed_count}")
                    if failed_count > 0:
                        has_error = True
                elif stream_type == 'error':
                    has_error = True
                    logger.error(f"CodeFileExecutor 执行出错: {message}")
            # 检查是否有错误
            if has_error:
                error_msg = "codefileexecutorlib 执行过程中出现错误"
                logger.error(error_msg)
                print(f"❌ {error_msg}", flush=True)
                print("🚨 按要求，codefileexecutorlib出错则退出程序", flush=True)
                sys.exit(1)  # 按要求，如果出错则退出程序
            if success_count > 0:
                logger.info(f"成功应用 {success_count} 个代码修复任务")
                print(f"✅ 成功应用 {success_count} 个代码修复任务", flush=True)
                return True
            else:
                logger.warning("没有成功应用任何代码修复任务")
                print("⚠️ 没有成功应用任何代码修复任务", flush=True)
                return False
        except ImportError as e:
            error_msg = "codefileexecutorlib 库未安装，请先安装相关依赖"
            logger.error(error_msg)
            print(f"❌ {error_msg}", flush=True)
            print("🚨 按要求，codefileexecutorlib出错则退出程序", flush=True)
            sys.exit(1)  # 按要求，如果出错则退出程序
        except Exception as e:
            error_msg = f"codefileexecutorlib 执行失败: {e}"
            logger.error(error_msg)
            print(f"❌ {error_msg}", flush=True)
            print("🚨 按要求，codefileexecutorlib出错则退出程序", flush=True)
            sys.exit(1)  # 按要求，如果出错则退出程序