# controller/main_workflow/step_prepare_project.py

import datetime
from controller.input_project_controller import InputProjectController
from controller.repo_sync_controller import RepoSyncController
from controller.ai_to_git_sync_controller import AiToGitSyncController
from controller.git_push_controller import GitPushController

def prepare_project(config):
    input_project_ctrl = InputProjectController()
    repo_sync_ctrl = RepoSyncController(config)
    ai_to_git_sync_ctrl = AiToGitSyncController(config)
    git_push_ctrl = GitPushController(config)

    project_name, encoded_path, project, project_id = input_project_ctrl.get_project_info()
    local_dir = repo_sync_ctrl.sync_repo(project_name)
    ai_to_git_sync_ctrl.sync_ai_to_git(local_dir)
    git_push_ctrl.push_to_ai(local_dir, commit_message="llm auto sync")

    return {
        "project_id": project_id,
        "project_name": project_name,
        "encoded_path": encoded_path,
        "local_dir": local_dir,
    }
