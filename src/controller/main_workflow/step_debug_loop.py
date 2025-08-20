# controller/main_workflow/step_debug_loop.py
import time
from controller.pipeline_monitor_controller import PipelineMonitorController
from controller.trace_controller import TraceController
from controller.source_code_controller import SourceCodeController
from controller.prompt_controller import PromptController
from controller.llm_controller import LLMController
from controller.git_push_controller import GitPushController
from controller.loop_controller import LoopController
from clients.logging.logger import logger
def run_debug_loop(config, project_info, mr):
    pipeline_monitor = PipelineMonitorController(config)
    trace_ctrl = TraceController()
    source_ctrl = SourceCodeController(config)
    prompt_ctrl = PromptController()
    llm_ctrl = LLMController(config)
    git_push_ctrl = GitPushController(config)
    loop_ctrl = LoopController(config)
    def loop_body(debug_idx):
        logger.info(f"调试循环第 {debug_idx + 1} 次开始")
        print(f"\n🔄 调试循环第 {debug_idx + 1} 次开始", flush=True)
        # 1. 监控 Pipeline 状态
        status, jobs = pipeline_monitor.monitor(project_info["project_id"], project_info["pipeline_id"])
        if status == "success":
            print("✅ Pipeline执行成功，调试循环结束", flush=True)
            logger.info("Pipeline执行成功，调试循环结束")
            return True
        if status == "failed":
            print("❌ Pipeline执行失败，开始错误分析...", flush=True)
            logger.info("Pipeline执行失败，开始错误分析")
            # 2. 获取失败的Job日志 (Trace) - 按要求获取并显示打印
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
            # 4. 构建修复提示词 (使用配置文件中的 fix_bug_prompt)
            print("📝 构建修复提示词...", flush=True)
            try:
                prompt = prompt_ctrl.build_fix_prompt(trace, source_code)
                logger.info("修复提示词构建成功")
                print(f"✅ 修复提示词构建成功，长度: {len(prompt)}", flush=True)
            except Exception as e:
                print(f"❌ 构建提示词失败: {e}", flush=True)
                logger.error(f"构建提示词失败: {e}")
                return False
            # 5. 调用 LLM 流式 API 修复代码 (使用 OpenAI 标准 completions 流式API)
            print("🛠️ 开始AI代码修复...", flush=True)
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
            # 6. 使用 CodeFileExecutorLib 应用修复的代码
            print("💾 使用 CodeFileExecutorLib 应用修复的代码...", flush=True)
            try:
                apply_success = source_ctrl.apply_fixed_code_with_executor(fixed_code)
                if not apply_success:
                    print("❌ 代码应用失败", flush=True)
                    logger.error("代码应用失败")
                    return False
            except Exception as e:
                # CodeFileExecutorLib 出错会直接退出程序，这里不应该到达
                print(f"❌ 应用修复代码异常: {e}", flush=True)
                logger.error(f"应用修复代码异常: {e}")
                return False
            # 7. 提交修复的代码并推送到远程 ai 分支
            print("📤 提交修复的代码到 Git...", flush=True)
            try:
                push_success = git_push_ctrl.commit_and_push_ai_changes(f"LLM auto fix - 调试循环第{debug_idx + 1}次修复")
                if not push_success:
                    print("❌ Git 提交推送失败", flush=True)
                    logger.error("Git 提交推送失败")
                    return False
            except Exception as e:
                print(f"❌ Git 操作异常: {e}", flush=True)
                logger.error(f"Git 操作异常: {e}")
                return False
            # 8. 等待新的 Pipeline 启动并更新 pipeline_id
            print("⏳ 等待新的 Pipeline 启动...", flush=True)
            time.sleep(30)  # 等待新Pipeline启动
            # 获取新的Pipeline ID
            new_pipeline = pipeline_monitor.get_latest_pipeline(project_info["project_id"], "ai")
            if new_pipeline:
                project_info["pipeline_id"] = new_pipeline["id"]
                print(f"🔄 更新到新Pipeline ID: {project_info['pipeline_id']}", flush=True)
                logger.info(f"更新到新Pipeline ID: {project_info['pipeline_id']}")
            else:
                print("⚠️ 未找到新的 Pipeline，继续使用当前 Pipeline ID", flush=True)
                logger.warning("未找到新的 Pipeline")
            # 9. 按要求回到准备阶段重新开始循环
            print("🔄 修复完成，回到准备阶段重新开始循环", flush=True)
            logger.info("修复完成，回到准备阶段重新开始循环")
            return False  # 继续下一次循环
        # 其他状态继续等待
        print("⏳ Pipeline仍在运行中...", flush=True)
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