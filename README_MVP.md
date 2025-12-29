## Contract Forge MVP（对齐 req_new.md 的“全编排”模式）

### 当前架构（MVP）
- **N8N**：主编排（串行/分支/可扩展，工作流文件见 `n8n_workflows/contract_mvp.json`）
- **FastAPI**：工具与状态服务（步骤级 API `/api/v1/steps/*`，状态/日志 `/state` `/logs`）
- **前端**：上传、状态、日志、流程图、聊天（支持 Markdown）

### 关键接口
- **仅上传并准备任务（给 N8N 用）**：`POST /api/v1/upload`（multipart）
  - 返回：`{ status, task_id, file_path }`
- **步骤级 API（给 N8N 编排调用）**：
  - `POST /api/v1/steps/parse`
  - `POST /api/v1/steps/retrieve`
  - `POST /api/v1/steps/evaluate`
  - `POST /api/v1/steps/approval`
  - `POST /api/v1/steps/report`
  - 均使用统一 DTO：`{ input: {...}, context: { task_id, step_id, history_results } }`
- **查询**：
  - `GET /api/v1/state/{task_id}`
  - `GET /api/v1/logs/{task_id}`

### N8N 工作流导入与触发（本地）
1. 在 N8N 中导入 `n8n_workflows/contract_mvp.json`
2. 启动 FastAPI（`localhost:8000`）
3. 触发 webhook（默认本地）：`POST http://localhost:5678/webhook/contractforge-mvp`
   - body 示例：`{ "file_path": "<后端返回的file_path>", "task_id": "<后端返回的task_id>" }`

### 前端使用模式
前端支持两种模式：
- **默认（N8N 全编排）**：上传调用 `/upload`，再触发 N8N webhook，由 N8N 编排所有步骤
- **旧模式（LangGraph 一次跑完）**：上传直接调用后端 `/audit`

使用旧模式（回退）：
- 设置前端环境变量：`VITE_USE_LEGACY_AUDIT=true`

N8N webhook URL 配置（可选）：
- 默认：`http://localhost:5678/webhook/contractforge-mvp`
- 自定义：设置 `VITE_N8N_WEBHOOK_URL=<your-webhook-url>`

### 日志与可观测
- 服务端日志文件：`backend/logs/app.log`
- 任务日志接口：`/api/v1/logs/{task_id}`（包含 level：info/warn/error/success）


