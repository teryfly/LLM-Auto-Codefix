# controller/main_workflow/step_merge_mr.py
import time
from controller.mr_merge_controller import MrMergeController
from clients.logging.logger import logger
from clients.gitlab.pipeline_client import PipelineClient

def merge_mr_and_wait_pipeline(config, project_info, mr=None):
    mr_merge_ctrl = MrMergeController(config)
    pipeline_client = PipelineClient()
    print("准备部署中，请等待...")
    time.sleep(3)  # 给 GitLab 几秒触发新 pipeline
    
    # 优先使用调试循环阶段更新的当前MR，如果没有则使用传入的MR
    current_mr = project_info.get("current_mr") or mr
    if not current_mr:
        error_msg = "没有找到可用的 MR 进行合并"
        logger.error(error_msg)
        print(f"❌ {error_msg}", flush=True)
        raise RuntimeError(error_msg)
    
    # 使用 MR 的 iid 字段进行合并操作
    mr_iid = getattr(current_mr, "iid", None)
    if not mr_iid:
        error_msg = "MR 对象缺少 iid 字段"
        logger.error(error_msg)
        print(f"❌ {error_msg}", flush=True)
        raise RuntimeError(error_msg)
    
    logger.info(f"Attempting to merge current active MR iid={mr_iid}")
    print(f"🔄 准备合并当前活跃的 MR: iid={mr_iid}", flush=True)
    
    # 显示MR信息
    mr_title = getattr(current_mr, "title", "Unknown")
    mr_web_url = getattr(current_mr, "web_url", "N/A")
    print(f"📋 MR信息: {mr_title}", flush=True)
    print(f"🔗 MR链接: {mr_web_url}", flush=True)
    logger.info(f"MR详情 - 标题: {mr_title}, URL: {mr_web_url}")
    
    try:
        merge_result = mr_merge_ctrl.merge_mr(project_info["project_id"], mr_iid)
        
        # 检查合并结果
        if isinstance(merge_result, dict) and merge_result.get("status") == "cannot_merge":
            error_reason = merge_result.get('reason')
            logger.error(f"MR {mr_iid} merge failed: {error_reason}")
            print(f"❌ Merge failed: {error_reason}")
            
            # 特殊处理：如果是因为没有差异导致无法合并，这可能是正常情况
            if "no changes" in error_reason.lower() or "no differences" in error_reason.lower():
                logger.info("MR无法合并是因为源分支和目标分支没有差异，这可能表示代码已经是最新的")
                print("ℹ️ 源分支和目标分支没有差异，可能代码已经是最新的")
                print("💡 建议：检查ai分支和dev分支是否已经同步")
                
                # 标记为特殊状态，允许后续流程继续或跳过
                project_info["merge_skipped"] = True
                project_info["merge_skip_reason"] = "no_changes_detected"
                project_info["merged_pipeline_id"] = None
                
                logger.info("由于没有差异，跳过合并步骤")
                print("⏭️ 跳过合并步骤，继续后续流程")
                return
            else:
                # 其他类型的合并失败，抛出异常
                project_info["merge_failed"] = True
                project_info["merge_error"] = error_reason
                raise RuntimeError(f"Merge Request merge failed: {error_reason}")
        
        # 合并成功，等待新的pipeline
        logger.info(f"MR {mr_iid} merged successfully")
        print(f"✅ MR {mr_iid} 合并成功")
        
    except Exception as e:
        # 处理合并过程中的其他异常
        error_msg = f"合并过程中发生异常: {str(e)}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        project_info["merge_failed"] = True
        project_info["merge_error"] = str(e)
        raise RuntimeError(error_msg)
    
    # 等待合并后的新pipeline
    time.sleep(5)
    pipelines = pipeline_client.list_pipelines(project_info["project_id"], ref="dev")
    if not pipelines:
        logger.warning("Merge 后未发现新的 pipeline，可能需要更长时间等待")
        print("⚠️  No new pipeline detected after merge. This may be normal for some projects.")
        project_info["merged_pipeline_id"] = None
    else:
        merged_pipeline = pipelines[0]
        project_info["merged_pipeline_id"] = merged_pipeline.id
        logger.info(f"Found post-merge pipeline: {merged_pipeline.id}")
        print(f"✅ 发现合并后Pipeline: {merged_pipeline.id}")