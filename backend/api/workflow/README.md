# 工作流状态管理 API

工作流状态管理模块用于跟踪和管理 N8N 工作流的执行状态。

## API 接口

### 1. 更新工作流状态

**POST** `/api/workflow/status/update`

更新工作流状态。此接口由 N8N 工作流在完成或失败时调用。

**请求体**：
```json
{
  "workflow_id": "工作流 ID",
  "status": "completed",  // pending, running, completed, failed
  "message": "可选的消息",
  "result": {  // 可选的结果数据
    "file_path": "文件路径",
    "risk_level": "风险等级"
  },
  "error": "错误信息（仅当 status 为 failed 时）"
}
```

**响应**：
```json
{
  "success": true,
  "workflow_id": "工作流 ID",
  "message": "工作流状态已更新"
}
```

### 2. 查询工作流状态

**GET** `/api/workflow/status/{workflow_id}`

查询指定工作流的状态。前端可以使用此接口轮询工作流状态。

**响应**：
```json
{
  "workflow_id": "工作流 ID",
  "status": "completed",  // pending, running, completed, failed
  "file_path": "文件路径",
  "result": {
    "file_path": "文件路径",
    "risk_level": "风险等级"
  },
  "message": "状态消息",
  "error": null,
  "created_at": "2025-12-31T10:00:00",
  "updated_at": "2025-12-31T10:05:00"
}
```

### 3. 创建工作流状态记录

**POST** `/api/workflow/status/create?file_path={file_path}&initial_status={initial_status}`

创建工作流状态记录。在启动工作流之前调用此接口创建状态记录，获取 workflow_id。

**查询参数**：
- `file_path` (必需): 文件相对路径（相对于 uploads 目录）
- `initial_status` (可选): 初始状态，默认为 "pending"

**响应**：
```json
{
  "workflow_id": "工作流 ID",
  "status": "pending",
  "file_path": "文件路径",
  "result": null,
  "message": null,
  "error": null,
  "created_at": "2025-12-31T10:00:00",
  "updated_at": "2025-12-31T10:00:00"
}
```

## 状态值说明

- `pending`: 等待中（工作流已创建但尚未开始执行）
- `running`: 运行中（工作流正在执行）
- `completed`: 已完成（工作流成功执行完成）
- `failed`: 失败（工作流执行失败）

## 使用流程

1. **启动工作流**：`n8n_workflow_trigger` 工具会自动创建工作流状态记录，并将 `workflow_id` 传递给 N8N 工作流
2. **工作流执行**：N8N 工作流执行过程中，状态自动设置为 `running`
3. **工作流完成**：工作流完成时，调用 `/api/workflow/status/update` 接口更新状态为 `completed`
4. **前端轮询**：前端每 2 秒调用 `/api/workflow/status/{workflow_id}` 查询状态，直到状态变为 `completed` 或 `failed`

## 前端集成示例

```typescript
// 1. 调用工作流触发接口，获取 workflow_id
const response = await fetch('/api/llm/chat_with_file_name', {
  method: 'POST',
  body: JSON.stringify({
    file_path: '2025-12-29/test_contract.pdf',
    messages: [{ role: 'user', content: '处理一下这个合同' }]
  })
});

const { workflow_id } = await response.json();

// 2. 轮询工作流状态
const pollInterval = setInterval(async () => {
  const statusResponse = await fetch(`/api/workflow/status/${workflow_id}`);
  const status = await statusResponse.json();
  
  if (status.status === 'completed') {
    clearInterval(pollInterval);
    // 处理完成状态
    console.log('工作流完成:', status.result);
  } else if (status.status === 'failed') {
    clearInterval(pollInterval);
    // 处理失败状态
    console.error('工作流失败:', status.error);
  }
  // status === 'running' 或 'pending' 时继续轮询
}, 2000); // 每 2 秒轮询一次
```

