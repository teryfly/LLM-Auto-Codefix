# controller/main_workflow/step_prepare_project.py
import datetime
from controller.input_project_controller import InputProjectController
from controller.repo_sync_controller import RepoSyncController
from controller.ai_to_git_sync_controller import AiToGitSyncController
from controller.git_push_controller import GitPushController
from clients.logging.logger import logger
def prepare_project(config, project_name: str = None):
    """
    准备项目步骤，支持传入项目名称
    正确的流程：
    1. 获取项目信息
    2. 同步远程仓库到 git_work_dir（强制更新）
    3. 将 ai_work_dir 的代码覆盖到 git_work_dir
    4. 提交并推送到远程 ai 分支
    """
    logger.info("开始项目准备阶段")
    print("🚀 开始项目准备阶段", flush=True)
    # 1. 获取项目信息
    logger.info("步骤 1: 获取项目信息")
    print("📋 步骤 1: 获取项目信息", flush=True)
    input_project_ctrl = InputProjectController()
    project_name, encoded_path, project, project_id = input_project_ctrl.get_project_info(project_name)
    print(f"✅ 项目信息获取成功: {project_name}", flush=True)
    # 2. 同步远程仓库到 git_work_dir（强制更新，确保与远端一致）
    logger.info("步骤 2: 同步远程仓库到本地工作目录")
    print("🔄 步骤 2: 同步远程仓库（强制更新）", flush=True)
    repo_sync_ctrl = RepoSyncController(config)
    local_dir = repo_sync_ctrl.sync_repo(project_name)
    print(f"✅ 远程仓库同步完成: {local_dir}", flush=True)
    # 3. 将 ai_work_dir 的代码覆盖到 git_work_dir
    logger.info("步骤 3: 将 AI 工作目录的代码同步到 Git 工作目录")
    print("📁 步骤 3: 同步 AI 代码到 Git 工作目录", flush=True)
    ai_to_git_sync_ctrl = AiToGitSyncController(config)
    ai_to_git_sync_ctrl.sync_ai_to_git(local_dir)
    # 可选：验证同步
    if ai_to_git_sync_ctrl.verify_sync(local_dir):
        print("✅ AI 代码同步验证通过", flush=True)
    else:
        print("⚠️ AI 代码同步验证有警告，但继续执行", flush=True)
    # 4. 提交并推送到远程 ai 分支
    logger.info("步骤 4: 提交并推送代码到远程 ai 分支")
    print("📤 步骤 4: 提交并推送到远程 ai 分支", flush=True)
    git_push_ctrl = GitPushController(config)
    commit_message = f"LLM auto sync - {datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    git_push_ctrl.push_to_ai(local_dir, commit_message=commit_message)
    print("✅ 代码推送完成", flush=True)
    logger.info("项目准备阶段完成")
    print("🎉 项目准备阶段完成", flush=True)
    return {
        "project_id": project_id,
        "project_name": project_name,
        "encoded_path": encoded_path,
        "local_dir": local_dir,
    }