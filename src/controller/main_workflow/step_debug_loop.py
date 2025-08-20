# controller/main_workflow/step_debug_loop.py

import time
from controller.pipeline_monitor_controller import PipelineMonitorController
from controller.trace_controller import TraceController
from controller.source_code_controller import SourceCodeController
from controller.prompt_controller import PromptController
from controller.llm_controller import LLMController
from controller.grpc_controller import GrpcController
from controller.loop_controller import LoopController
from clients.logging.logger import logger

def run_debug_loop(config, project_info, mr):
    pipeline_monitor = PipelineMonitorController(config)
    trace_ctrl = TraceController()
    source_ctrl = SourceCodeController(config)
    prompt_ctrl = PromptController()
    llm_ctrl = LLMController(config)
    grpc_ctrl = GrpcController(config)
    loop_ctrl = LoopController(config)

    def loop_body(debug_idx):
        logger.info(f"调试循环第 {debug_idx + 1} 次开始")
        print(f"\n🔄 调试循环第 {debug_idx + 1} 次开始", flush=True)
        
        status, jobs = pipeline_monitor.monitor(project_info["project_id"], project_info["pipeline_id"])
        
        if status == "success":
            print("✅ Pipeline执行成功，调试循环结束", flush=True)
            logger.info("Pipeline执行成功，调试循环结束")
            return True
            
        if status == "failed":
            print("❌ Pipeline执行失败，开始错误分析...", flush=True)
            logger.info("Pipeline执行失败，开始错误分析")
            
            # 获取失败的Job日志
            trace = trace_ctrl.get_failed_trace(project_info["project_id"], jobs)
            if not trace:
                print("⚠️ 未找到失败的Job日志", flush=True)
                logger.warning("未找到失败的Job日志")
                return False
            
            print(f"📋 获取到失败日志，长度: {len(trace)}", flush=True)
            logger.info(f"获取到失败日志，长度: {len(trace)}")
            
            # 使用流式API分析日志
            print("🤖 开始AI分析Pipeline日志...", flush=True)
            analysis_result = llm_ctrl.analyze_pipeline_logs(trace)
            
            if not analysis_result:
                print("❌ AI分析失败", flush=True)
                logger.error("AI分析失败")
                return False
            
            # 获取源代码
            print("📁 获取项目源代码...", flush=True)
            source_code = source_ctrl.get_failed_source_codes(project_info["project_id"], jobs)
            if not source_code:
                print("⚠️ 未找到相关源代码", flush=True)
                logger.warning("未找到相关源代码")
                return False
            
            # 生成修复提示词
            print("📝 生成修复提示词...", flush=True)
            prompt = prompt_ctrl.generate_fix_prompt(trace, source_code, analysis_result)
            
            # 使用流式API修复代码
            print("🛠️ 开始AI代码修复...", flush=True)
            fixed_code = llm_ctrl.fix_code_with_llm_stream(prompt)
            
            if not fixed_code:
                print("❌ 代码修复失败", flush=True)
                logger.error("代码修复失败")
                return False
            
            # 应用修复的代码
            print("💾 应用修复的代码...", flush=True)
            if not source_ctrl.apply_fixed_code(fixed_code):
                print("❌ 应用修复代码失败", flush=True)
                logger.error("应用修复代码失败")
                return False
            
            # 提交修复
            print("📤 提交修复到Git...", flush=True)
            if not grpc_ctrl.commit_and_push_changes(f"Fix: 调试循环第{debug_idx + 1}次修复"):
                print("❌ 提交修复失败", flush=True)
                logger.error("提交修复失败")
                return False
            
            print("✅ 修复已提交，等待新的Pipeline...", flush=True)
            time.sleep(30)  # 等待新Pipeline启动
            
            # 获取新的Pipeline ID
            new_pipeline = pipeline_monitor.get_latest_pipeline(project_info["project_id"], mr["iid"])
            if new_pipeline:
                project_info["pipeline_id"] = new_pipeline["id"]
                print(f"🔄 新Pipeline ID: {project_info['pipeline_id']}", flush=True)
            
            return False  # 继续下一次循环
        
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