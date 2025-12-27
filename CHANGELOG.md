# 更新日志 - 基于新需求文档的代码修改

## 概述

根据 `req_modified.md` 的新需求，将系统从 Microsoft Copilot 迁移到 React 前端 + 大语言模型实现。主要实现了自然语言交互、流程可视化、执行日志展示和智能报告生成功能。

## 后端修改

### 1. 新增大语言模型服务模块
- **文件**: `backend/utils/llm_service.py`
- **功能**:
  - `chat()`: 自然语言交互，根据用户消息生成智能回复
  - `generate_report()`: 基于审计数据生成 Markdown 格式的智能报告
  - `analyze_logs()`: 分析执行日志，生成诊断报告
- **说明**: 当前使用模拟实现，后续可接入 OpenAI、Anthropic 或本地模型

### 2. 增强 API 路由
- **文件**: `backend/api/routes.py`
- **新增接口**:
  - `POST /api/v1/chat`: 自然语言交互（增强版，支持上下文）
  - `GET /api/v1/state/{task_id}`: 获取详细流程状态（包含步骤信息）
  - `GET /api/v1/logs/{task_id}`: 获取任务执行日志
  - `POST /api/v1/report/generate`: 生成智能报告
- **改进**:
  - `/api/v1/audit` 接口现在会记录任务状态和日志
  - 添加了任务状态存储（当前使用内存，生产环境应使用 Redis 或数据库）

### 3. 更新数据模型
- **文件**: `backend/api/schemas.py`
- **新增模型**:
  - `ChatRequest`: 支持上下文信息（task_id, user_id, session_id）
  - `ChatResponse`: 包含 response, suggested_actions, confidence
  - `FlowStateResponse`: 流程状态响应（包含详细步骤信息）
  - `StepInfo`: 步骤信息模型
  - `ReportGenerateRequest/Response`: 报告生成请求和响应

## 前端修改

### 1. 更新 API 客户端
- **文件**: `frontend/src/api/client.ts`
- **新增接口**:
  - `getFlowState()`: 获取流程状态
  - `getTaskLogs()`: 获取任务日志
  - `generateReport()`: 生成智能报告
- **改进**:
  - `chat()` 接口支持传递上下文信息
  - 添加了 TypeScript 类型定义

### 2. 新增流程可视化组件
- **文件**: `frontend/src/components/FlowViewer.tsx`
- **功能**:
  - 可视化展示流程执行图
  - 显示节点状态（待执行/执行中/已完成/失败）
  - 支持当前步骤高亮显示
  - 包含图例说明

### 3. 新增执行日志组件
- **文件**: `frontend/src/components/ExecutionLogs.tsx`
- **功能**:
  - 实时展示任务执行日志
  - 支持自动刷新（可配置间隔）
  - 支持日志搜索和筛选
  - 支持导出日志为文本文件
  - 显示日志级别图标（info/success/error）

### 4. 增强主页组件
- **文件**: `frontend/src/pages/HomePage/index.tsx`
- **新增功能**:
  - 集成流程可视化组件
  - 集成执行日志组件
  - 添加标签页切换（步骤/流程图/日志）
  - 增强聊天功能，支持上下文传递
  - 自动获取和更新流程状态
  - 智能报告生成按钮
  - 文件上传后自动触发审计

### 5. 更新文件上传组件
- **文件**: `frontend/src/components/FileUpload.tsx`
- **改进**:
  - 添加 `onFileUpload` 回调，支持文件上传后自动触发审计

## 功能特性

### ✅ 已实现

1. **自然语言交互**
   - React 前端聊天界面
   - 后端大语言模型服务（当前为模拟实现）
   - 支持上下文传递（task_id, user_id, session_id）
   - 智能回复和建议操作

2. **流程可视化**
   - 使用自定义组件展示流程图
   - 实时显示节点状态
   - 支持当前步骤高亮

3. **执行日志**
   - 实时日志展示
   - 自动刷新功能
   - 日志搜索和导出

4. **智能报告生成**
   - 基于审计数据生成 Markdown 报告
   - 包含风险详情和建议
   - 支持自定义模板和格式

5. **流程状态管理**
   - 详细步骤信息记录
   - 实时状态更新
   - 任务状态持久化（当前为内存存储）

### ⚠️ 待实现（可选）

1. **WebSocket 实时推送**
   - 当前使用轮询方式获取日志
   - 可升级为 WebSocket 实现实时推送

2. **真实大语言模型集成**
   - 当前使用模拟实现
   - 需要接入 OpenAI、Anthropic 或本地模型 API

3. **流式响应**
   - 大语言模型支持流式输出
   - 前端实时渲染流式响应

4. **持久化存储**
   - 任务状态和日志应存储到数据库或 Redis
   - 当前使用内存存储，服务重启会丢失

## 使用说明

### 后端启动

```bash
cd backend
pip install -r requirements.txt
python main.py
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

### 使用流程

1. **上传合同**: 在左侧面板上传 PDF/DOCX 文件
2. **自动审计**: 文件上传后自动触发审计流程
3. **查看状态**: 
   - 在右侧面板的"步骤"标签查看处理进度
   - 在"流程图"标签查看可视化流程图
   - 在"日志"标签查看执行日志
4. **智能对话**: 在中间聊天界面与 AI 助手对话，查询状态、获取建议
5. **生成报告**: 审计完成后，点击"生成智能报告"按钮

## 技术栈

- **后端**: FastAPI, LangGraph, ChromaDB
- **前端**: React, TypeScript, Tailwind CSS
- **大语言模型**: 当前为模拟实现，可接入 OpenAI/Anthropic/本地模型

## 注意事项

1. 当前大语言模型服务为模拟实现，需要根据实际需求接入真实 API
2. 任务状态和日志使用内存存储，生产环境应使用持久化存储
3. 日志刷新使用轮询方式，可升级为 WebSocket 实现
4. 流程可视化使用自定义组件，可升级为 React Flow 等专业库

## 后续优化建议

1. 接入真实大语言模型 API（OpenAI/Anthropic）
2. 实现 WebSocket 实时日志推送
3. 使用数据库或 Redis 持久化任务状态
4. 升级流程可视化组件（React Flow）
5. 添加流式响应支持
6. 实现报告导出为 PDF/Word 格式
7. 添加用户认证和权限管理

