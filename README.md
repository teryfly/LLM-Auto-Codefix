
# Python Backend Program for LLM Code Testing via GitLab CI/CD

## Directory Structure

```
project_root/
├── main.py
├── app.py
├── config.yaml
├── requirements.txt
├── config/
│   ├── config_manager.py
│   ├── config_models.py
│   └── config_validator.py
├── models/
│   ├── gitlab_models.py
│   ├── llm_models.py
│   ├── grpc_models.py
│   ├── pipeline_models.py
│   └── constants.py
├── utils/
│   ├── exceptions.py
│   ├── helpers.py
│   └── validators.py
├── operations/
│   ├── git/
│   │   ├── git_manager.py
│   │   ├── git_commands.py
│   │   └── git_validator.py
│   ├── file/
│   │   ├── file_manager.py
│   │   └── directory_ops.py
│   ├── source/
│   │   ├── source_reader.py
│   │   └── source_processor.py
│   └── template/
│       ├── template_manager.py
│       └── prompt_builder.py
├── clients/
│   ├── gitlab/
│   │   ├── gitlab_client.py
│   │   ├── project_client.py
│   │   ├── pipeline_client.py
│   │   ├── job_client.py
│   │   └── merge_request_client.py
│   ├── llm/
│   │   ├── llm_client.py
│   │   └── llm_formatter.py
│   ├── grpc/
│   │   ├── grpc_client.py
│   │   └── grpc_handler.py
│   └── logging/
│       ├── logger.py
│       ├── log_formatter.py
│       └── trace_logger.py
├── control/
│   ├── retry/
│   │   ├── retry_manager.py
│   │   ├── retry_strategy.py
│   │   └── retry_decorator.py
│   ├── status/
│   │   ├── status_manager.py
│   │   ├── status_monitor.py
│   │   └── status_handler.py
│   └── timeout/
│       ├── timeout_manager.py
│       └── timeout_decorator.py
├── services/
│   ├── cicd/
│   │   ├── cicd_service.py
│   │   ├── pipeline_service.py
│   │   └── job_service.py
│   ├── code_fix/
│   │   ├── code_fix_service.py
│   │   ├── bug_analyzer.py
│   │   └── fix_validator.py
│   └── project/
│       ├── project_validator.py
│       └── project_setup.py
└── controller/
    ├── main_controller.py
    ├── workflow_manager.py
    └── debug_loop_controller.py
```

## Module Responsibilities

- **config/**: Configuration management, loading, models, and validation
- **models/**: Data models for API responses, system constants
- **utils/**: Utilities, helpers, and custom exceptions
- **operations/**: Core operations (git, file, source code, templates)
- **clients/**: External service clients (GitLab, LLM, gRPC, logging)
- **control/**: Retry, status, and timeout management
- **services/**: Business services for CI/CD, code fixing, and project setup/validation
- **controller/**: Main workflow, process orchestration, debug loop control

## 使用方法 & 流程说明

### 1. 配置准备

- 编辑 `config.yaml`，设置所有路径、服务地址、Token、重试参数等。
- 推荐配置参考：
    ```yaml
    paths:
      git_work_dir: "/path/to/git/workspace"
      ai_work_dir: "/path/to/ai/workspace"
    services:
      grpc_port: "localhost:50051"
      gitlab_url: "http://gitlab.micsun.cn"
      llm_url: "http://llm.example.com/v1"
      llm_model: "GPT-4.1"
    authentication:
      gitlab_private_token: "your-gitlab-token"
    retry_config:
      retry_interval_time: 90
      retry_max_time: 10
      debug_max_time: 5
      total_timeout: 36000
    templates:
      fix_bug_prompt: "The following source code failed during CI/CD pipeline execution. Please analyze the error trace and provide the complete corrected source code."
    ```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 快速启动

```bash
python main.py
```

### 4. 工作流程

1. **配置加载与校验**  
   程序首先加载并校验 config.yaml 配置项，确保所有参数合法。
2. **GitLab 项目校验**  
   检查目标项目是否存在，若不存在可交互式提示确认及处理。
3. **仓库操作**  
   自动拉取/克隆仓库，创建/切换分支，完成分支及文件同步。
4. **触发并监控 CI/CD Pipeline**  
   创建 MR 并触发流水线，持续监控 Pipeline 及 Job 状态。
5. **错误与 Trace 处理**  
   CI/CD 失败时自动收集错误信息与 Trace，记录日志。
6. **智能修复循环**  
   调用 LLM（如 GPT-4）分析错误 Trace，自动生成修复后的代码，推送到新分支并重新触发流水线。
   - 支持最多 debug_max_time 次修复循环，单次失败自动重试（含指数退避）。
7. **终止条件**  
   - 流水线成功：流程结束。
   - 达到最大修复次数或超时：流程终止，记录详细日志。
   - 遇到 manual/pending 等人工干预节点：等待或提示。

### 5. 日志与输出

- 所有操作过程、异常与 Trace 信息将保存至日志系统。
- 关键节点（如 LLM 修复内容、Pipeline 状态、错误原因）均有详细记录，便于溯源与复盘。

### 6. 常见问题与恢复策略

- **项目不存在**：手动确认项目名后按提示处理。
- **Token 认证失败**：检查 config.yaml 内 token 正确性与权限。
- **网络/接口异常**：自动重试，频繁失败可手动介入。
- **LLM 服务异常**：支持降级/跳过智能修复，或等待人工处理。

---

## 设计原则

- 单一职责、依赖注入、配置驱动、异常友好、全面日志
- 详细的模块接口文档与严格的参数校验

