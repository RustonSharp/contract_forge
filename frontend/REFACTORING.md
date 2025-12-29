# 前端重构说明

## 重构概述

根据后端实际提供的接口，对前端代码进行了全面重构，删除了不存在的接口调用，更新为正确的后端 API。

## 后端接口清单

### 文件管理接口 (`/api/files`)
- `POST /api/files/upload` - 上传文件
- `GET /api/files/list` - 查询文件列表（支持日期筛选和分页）
- `GET /api/files/list/dates` - 获取所有有文件的日期列表
- `GET /api/files/info/{file_name}` - 获取文件信息

### LLM 对话接口 (`/api/llm`)
- `POST /api/llm/chat` - 与 LLM 对话（支持工具调用）
- `POST /api/llm/chat/simple` - 简单对话接口

### 工具管理接口 (`/api/tools`)
- `GET /api/tools` - 获取所有工具列表
- `GET /api/tools/{tool_name}` - 获取工具信息
- `POST /api/tools/execute` - 执行工具
- `GET /api/tools/names` - 获取所有工具名称

## 主要变更

### 1. API 客户端重构 (`src/api/client.ts`)

**删除的接口**：
- ❌ `/api/v1/chat` - 不存在
- ❌ `/api/v1/audit` - 不存在
- ❌ `/api/v1/upload` - 不存在
- ❌ `/api/v1/state/{taskId}` - 不存在
- ❌ `/api/v1/logs/{taskId}` - 不存在
- ❌ `/api/v1/report/generate` - 不存在
- ❌ N8N Webhook 直接调用 - 已由后端 LLM 工具调用处理

**新增的接口**：
- ✅ `uploadFile()` - 文件上传
- ✅ `listFiles()` - 文件列表查询
- ✅ `listDates()` - 日期列表
- ✅ `getFileInfo()` - 文件信息
- ✅ `chat()` - LLM 对话
- ✅ `chatSimple()` - 简单对话
- ✅ `listTools()` - 工具列表
- ✅ `getToolInfo()` - 工具信息
- ✅ `executeTool()` - 执行工具
- ✅ `listToolNames()` - 工具名称列表

**配置变更**：
- 基础 URL 从 `http://localhost:8000/api/v1` 改为 `http://localhost:8000/api`

### 2. 文件上传组件重构 (`src/components/FileUpload.tsx`)

**新增功能**：
- ✅ 使用新的文件上传接口 (`/api/files/upload`)
- ✅ 自动加载已上传的文件列表
- ✅ 显示上传进度
- ✅ 错误处理优化

**删除功能**：
- ❌ 本地文件状态管理（改为从后端加载）

### 3. 主页重构 (`src/pages/HomePage/index.tsx`)

**删除的功能**：
- ❌ 流程状态查询 (`fetchFlowState`)
- ❌ 任务日志查询 (`getTaskLogs`)
- ❌ 智能报告生成 (`generateReport`)
- ❌ N8N 工作流直接触发
- ❌ 流程步骤显示
- ❌ 流程图显示
- ❌ 执行日志显示

**保留/更新的功能**：
- ✅ LLM 对话功能（使用新的 `/api/llm/chat` 接口）
- ✅ 文件上传功能（通过 FileUpload 组件）
- ✅ 消息历史记录
- ✅ Markdown 渲染

**简化**：
- 移除了右侧面板的流程/日志/流程图标签页
- 移除了流程状态轮询
- 移除了任务 ID 管理

### 4. 删除的组件

- ❌ `src/components/ExecutionLogs.tsx` - 依赖不存在的日志接口
- ❌ `src/components/FlowViewer.tsx` - 依赖不存在的流程状态接口
- ❌ `src/components/RiskBadge.tsx` - 未使用的组件

## 使用说明

### 文件上传

1. 用户上传文件后，文件会自动保存到后端 `uploads/YYYY-MM-DD/` 目录
2. 文件列表会自动从后端加载
3. 支持按日期筛选（未来可扩展）

### LLM 对话

1. 用户可以通过对话与 LLM 交互
2. LLM 会根据用户需求自动调用工具（如 N8N 工作流）
3. 当用户说"帮我处理一下这个合同"时，LLM 会自动调用 N8N 工作流工具

### 工具调用

工具调用由后端 LLM 服务自动处理，前端无需直接调用工具接口。用户只需通过对话与 LLM 交互即可。

## 后续优化建议

1. **文件列表筛选**：添加日期筛选下拉框
2. **工具调用显示**：在对话中显示工具调用结果
3. **错误处理**：优化错误提示和重试机制
4. **加载状态**：添加更多加载状态指示器
5. **响应式设计**：优化移动端显示

## 注意事项

- 确保后端服务运行在 `http://localhost:8000`
- 确保 CORS 配置正确
- 文件上传大小限制为 10MB
- 支持的文件类型：PDF、DOC、DOCX、JPEG、PNG

