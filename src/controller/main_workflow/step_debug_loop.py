# controller/main_workflow/step_debug_loop.py
import time
import datetime
from controller.pipeline_monitor_controller import PipelineMonitorController
from controller.trace_controller import TraceController
from controller.source_code_controller import SourceCodeController
from controller.prompt_controller import PromptController
from controller.llm_controller import LLMController
from controller.git_push_controller import GitPushController
from controller.loop_controller import LoopController
from controller.mr_create_controller import MrCreateController
from clients.gitlab.merge_request_client import MergeRequestClient
from clients.gitlab.pipeline_client import PipelineClient
from clients.logging.logger import logger
def run_debug_loop(config, project_info, mr):
    pipeline_monitor = PipelineMonitorController(config)
    trace_ctrl = TraceController()
    source_ctrl = SourceCodeController(config)
    prompt_ctrl = PromptController()
    llm_ctrl = LLMController(config)
    git_push_ctrl = GitPushController(config)
    loop_ctrl = LoopController(config)
    mr_ctrl = MrCreateController(config)
    mr_client = MergeRequestClient()
    pipeline_client = PipelineClient()
    # 修复前关闭当前 MR（GitLab v4 无删除接口，仅支持关闭）
    def close_mr_if_exists(project_id, mr_iid):
        if not mr_iid:
            return
        try:
            logger.info(f"尝试关闭 MR iid={mr_iid}")
            print(f"🔒 关闭当前 MR iid={mr_iid}", flush=True)
            result = mr_ctrl.mr_client.close_merge_request(project_id, mr_iid)
            if result:
                logger.info(f"MR {mr_iid} 已关闭")
                print(f"✅ 成功关闭 MR {mr_iid}", flush=True)
            else:
                logger.warning(f"关闭 MR {mr_iid} 失败")
                print(f"⚠️ 关闭 MR {mr_iid} 失败", flush=True)
        except Exception as e:
            logger.error(f"关闭 MR {mr_iid} 时出错: {e}")
            print(f"❌ 关闭 MR {mr_iid} 时出错: {e}", flush=True)
    # 从配置文件获取调试循环间隔时间
    debug_interval = getattr(config.retry_config, 'debug_loop_interval', 10)
    logger.info(f"调试循环间隔时间: {debug_interval} 秒")
    print(f"⏱️ 调试循环间隔时间: {debug_interval} 秒", flush=True)
    # 当前活跃的MR变量
    current_mr = mr
    current_mr_pipeline_id = project_info.get("pipeline_id")
    def loop_body(debug_idx):
        nonlocal current_mr, current_mr_pipeline_id
        logger.info(f"调试循环第 {debug_idx + 1} 次开始")
        print(f"\n🔄 调试循环第 {debug_idx + 1} 次开始", flush=True)
        # 1. 监控当前MR的Pipeline状态
        if current_mr_pipeline_id:
            print(f"🔍 监控 MR Pipeline ID: {current_mr_pipeline_id}", flush=True)
            status, jobs = pipeline_monitor.monitor(project_info["project_id"], current_mr_pipeline_id)
        else:
            print("⚠️ 没有Pipeline ID，跳过监控", flush=True)
            status = "failed"
            jobs = []
        if status == "success":
            print("✅ MR Pipeline执行成功，调试循环结束", flush=True)
            logger.info("MR Pipeline执行成功，调试循环结束")
            # 更新project_info中的信息，供后续合并使用
            project_info["current_mr"] = current_mr
            project_info["current_mr_pipeline_id"] = current_mr_pipeline_id
            return True
        if status == "failed":
            print("❌ MR Pipeline执行失败，开始错误分析...", flush=True)
            logger.info("MR Pipeline执行失败，开始错误分析")
            # 修复前关闭当前MR
            current_mr_iid = getattr(current_mr, "iid", None) if current_mr else None
            if current_mr_iid:
                close_mr_if_exists(project_info["project_id"], current_mr_iid)
            # 2. 获取失败的Job日志 (Trace)
            trace = trace_ctrl.get_failed_trace(project_info["project_id"], jobs)
            if not trace:
                print("⚠️ 未找到失败的Job日志", flush=True)
                logger.warning("未找到失败的Job日志")
                return False
            print(f"📋 获取到失败日志，长度: {len(trace)}", flush=True)
            print("=" * 80)
            print("📄 Pipeline Job Trace 日志内容:")
            print(trace)
            print("=" * 80)
            logger.info(f"获取到失败日志，长度: {len(trace)}")
            # 3. 获取源代码 (使用 source-code-concatenator API，从 ai_work_dir)
            print("📁 获取项目源代码...", flush=True)
            try:
                source_code = source_ctrl.get_project_source_from_ai_dir()
            except Exception as e:
                print(f"❌ 获取源代码失败: {e}", flush=True)
                logger.error(f"获取源代码失败: {e}")
                return False
            if not source_code:
                print("⚠️ 未找到相关源代码", flush=True)
                logger.warning("未找到相关源代码")
                return False
            # 4. 构建修复提示词
            print("📝 构建修复提示词...", flush=True)
            try:
                prompt = prompt_ctrl.build_fix_prompt(trace, source_code)
                logger.info("修复提示词构建成功")
                print(f"✅ 修复提示词构建成功，长度: {len(prompt)}", flush=True)
            except Exception as e:
                print(f"❌ 构建提示词失败: {e}", flush=True)
                logger.error(f"构建提示词失败: {e}")
                return False
            # 5. 调用 LLM 流式 API 修复代码
            print("🛠️ 开始AI代码修复...", flush=True)
            print("🤖 正在连接AI服务端...", flush=True)
            print("🤖 调用 LLM 流式 API 进行代码修复...", flush=True)
            try:
                fixed_code = llm_ctrl.fix_code_with_llm_stream(prompt)
            except Exception as e:
                print(f"❌ LLM代码修复失败: {e}", flush=True)
                logger.error(f"LLM代码修复失败: {e}")
                return False
            if not fixed_code or not fixed_code.strip():
                print("❌ LLM返回空的修复代码", flush=True)
                logger.error("LLM返回空的修复代码")
                return False
            print(f"\n🤖 LLM返回的修复代码 (长度: {len(fixed_code)}):")
            print("=" * 80)
            print("📝 Feedback Code:")
            print(fixed_code)
            print("=" * 80)
            # 6. 使用 CodeFileExecutorLib 应用修复的代码，并收集输出
            print("💾 使用 CodeFileExecutorLib 应用修复的代码...", flush=True)
            try:
                apply_success, executor_output_lines = source_ctrl.apply_fixed_code_with_executor(fixed_code)
                if not apply_success:
                    print("❌ 代码应用失败", flush=True)
                    logger.error("代码应用失败")
                    return False
            except SystemExit:
                # 函数内部在错误时按要求直接退出；此处兜底避免异常向外传播破坏流程日志
                return False
            except Exception as e:
                print(f"❌ 应用修复代码异常: {e}", flush=True)
                logger.error(f"应用修复代码异常: {e}")
                return False
            # 7. 提取步骤信息作为commit消息
            step_lines = [line for line in executor_output_lines if "Step [" in line]
            if step_lines:
                commit_note = "\n".join(step_lines)
                logger.info(f"提取到 {len(step_lines)} 个步骤信息作为commit消息")
                print(f"📋 提取到 {len(step_lines)} 个步骤信息作为commit消息", flush=True)
            else:
                commit_note = f"LLM auto fix - 调试循环第{debug_idx + 1}次修复"
                logger.info("未找到步骤信息，使用默认commit消息")
                print("📋 使用默认commit消息", flush=True)
            # 8. 执行git操作（add, commit, push）
            print("🔄 修复完成，推送代码并创建新MR", flush=True)
            logger.info("修复完成，推送代码并创建新MR")
            from controller.main_workflow.step_preparation_phase import (
                git_add_and_show_changes,
                git_commit_with_note,
                git_push_changes
            )
            ai_work_dir = config.paths.ai_work_dir
            # git add .
            print("📝 添加所有修改到暂存区", flush=True)
            add_result = git_add_and_show_changes(ai_work_dir)
            if add_result["status"] != "success":
                print(f"❌ git add 失败: {add_result['message']}", flush=True)
                logger.error(f"git add 失败: {add_result['message']}")
                return False
            # git commit
            print(f"💾 提交修改: {commit_note}", flush=True)
            commit_result = git_commit_with_note(ai_work_dir, commit_note)
            if commit_result["status"] != "success":
                print(f"❌ git commit 失败: {commit_result['message']}", flush=True)
                logger.error(f"git commit 失败: {commit_result['message']}")
                return False
            # git push
            print("📤 推送到远程仓库", flush=True)
            push_result = git_push_changes(ai_work_dir)
            if push_result["status"] != "success":
                print(f"❌ git push 失败: {push_result['message']}", flush=True)
                logger.error(f"git push 失败: {push_result['message']}")
                return False
            # 9. 创建新的MR
            print("📝 创建新的 MR...", flush=True)
            logger.info("创建新的 MR")
            try:
                now = datetime.datetime.now().strftime("%H%M%S")
                mr_title = f"LLM Auto Merge ai->dev [Fix-{debug_idx + 1}-{now}]"
                # 使用带冲突解决的创建方法
                new_mr = mr_ctrl.create_mr_with_conflict_resolution(
                    project_info["project_id"], 
                    "ai", 
                    "dev", 
                    mr_title
                )
                current_mr = new_mr
                logger.info(f"新MR创建成功: iid={new_mr.iid}")
                print(f"✅ 新MR创建成功: iid={new_mr.iid}", flush=True)
            except Exception as e:
                error_msg = f"创建MR失败: {e}"
                logger.error(error_msg)
                print(f"❌ {error_msg}", flush=True)
                return False
            # 10. 等待并获取新MR的Pipeline
            print("⏳ 等待新MR的Pipeline启动...", flush=True)
            time.sleep(30)  # 等待Pipeline启动
            # 获取MR的Pipeline
            try:
                mr_pipelines = mr_client.get_merge_request_pipelines(project_info["project_id"], new_mr.iid)
                if mr_pipelines:
                    latest_mr_pipeline = mr_pipelines[0]  # 获取最新的Pipeline
                    current_mr_pipeline_id = latest_mr_pipeline["id"]
                    print(f"🔄 找到新MR Pipeline ID: {current_mr_pipeline_id}", flush=True)
                    logger.info(f"找到新MR Pipeline ID: {current_mr_pipeline_id}")
                    # 检查Pipeline状态
                    pipeline_status = str(latest_mr_pipeline.get("status", "")).lower()
                    logger.info(f"新MR Pipeline状态: {pipeline_status}")
                    print(f"🔍 新MR Pipeline状态: {pipeline_status}", flush=True)
                    if pipeline_status in {"success", "skipped", "canceled"}:
                        print("✅ 新MR Pipeline已成功，结束调试循环进入下一阶段", flush=True)
                        logger.info("新MR Pipeline已成功，结束调试循环进入下一阶段")
                        # 更新project_info供后续使用
                        project_info["current_mr"] = current_mr
                        project_info["current_mr_pipeline_id"] = current_mr_pipeline_id
                        return True
                    else:
                        print(f"🔄 新MR Pipeline状态为 {pipeline_status}，继续监控", flush=True)
                        logger.info(f"新MR Pipeline状态为 {pipeline_status}，继续监控")
                else:
                    print("⚠️ 未找到新MR的Pipeline，继续下一次循环", flush=True)
                    logger.warning("未找到新MR的Pipeline")
                    current_mr_pipeline_id = None
            except Exception as e:
                error_msg = f"获取MR Pipeline失败: {e}"
                logger.error(error_msg)
                print(f"❌ {error_msg}", flush=True)
                current_mr_pipeline_id = None
            # 使用配置的间隔时间
            if debug_interval > 0:
                print(f"⏳ 等待 {debug_interval} 秒后继续下一次循环...", flush=True)
                time.sleep(debug_interval)
            return False  # 继续下一次循环
        # 其他状态继续等待
        print("⏳ MR Pipeline仍在运行中...", flush=True)
        return False
    # 执行调试循环
    print("🚀 开始调试循环阶段", flush=True)
    logger.info("开始调试循环阶段")
    success = loop_ctrl.run_loop(loop_body, config.retry_config.debug_max_time)
    if success:
        print("🎉 调试循环成功完成", flush=True)
        logger.info("调试循环成功完成")
        return {"status": "success", "message": "调试循环成功完成"}
    else:
        print("❌ 调试循环达到最大次数限制", flush=True)
        logger.error("调试循环达到最大次数限制")
        return {"status": "failed", "message": "调试循环达到最大次数限制"}