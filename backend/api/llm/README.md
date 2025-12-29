# LLM 对话 API

提供与 LLM 对话的接口，支持工具调用（特别是 N8N 工作流触发）。

## 接口说明

### 1. 对话接口（支持工具调用）

**POST** `/api/llm/chat`

与 LLM 进行对话，支持自动工具调用。

**请求体**：
```json
{
    "messages": [
        {"role": "user", "content": "帮我处理一下 test_contract.pdf"}
    ],
    "temperature": 0.7,
    "max_tokens": 2000,
    "enable_tools": true
}
```

**响应**：
```json
{
    "message": "我已经为您触发了合同处理流程...",
    "tool_calls": [
        {
            "tool_name": "n8n_workflow_trigger",
            "parameters": {
                "file_name": "test_contract.pdf"
            },
            "result": {
                "success": true,
                "data": {...}
            }
        }
    ],
    "usage": {
        "prompt_tokens": 1000,
        "completion_tokens": 500,
        "total_tokens": 1500
    }
}
```

### 2. 简单对话接口

**POST** `/api/llm/chat/simple?user_message=处理文件&system_message=你是一个助手`

简化的对话接口，只需提供用户消息。

**参数**：
- `user_message` (必需): 用户消息
- `system_message` (可选): 系统消息

## 工具调用逻辑

### N8N 工作流触发（优先使用）

当用户要求处理文件但没有指定具体工具时，LLM 会自动调用 `n8n_workflow_trigger` 工具。

**触发场景**：
- ✅ "处理 test_contract.pdf"
- ✅ "分析这个合同"
- ✅ "帮我审核一下合同"
- ✅ "处理文件 test.pdf"

### 其他工具调用

如果用户明确指定工具，LLM 会调用对应的工具：
- "解析文档 test.pdf" → `document_parser`
- "进行风险评估" → `risk_assessment`
- "查询法规" → `regulation_search`

## 使用示例

### Python 示例

```python
import requests

# 对话请求
response = requests.post(
    "http://localhost:8000/api/llm/chat",
    json={
        "messages": [
            {"role": "user", "content": "帮我处理一下 test_contract.pdf"}
        ],
        "enable_tools": True
    }
)

result = response.json()
print(result["message"])
if result.get("tool_calls"):
    for tool_call in result["tool_calls"]:
        print(f"调用了工具: {tool_call['tool_name']}")
```

### cURL 示例

```bash
curl -X POST "http://localhost:8000/api/llm/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "帮我处理一下 test_contract.pdf"}
    ],
    "enable_tools": true
  }'
```

## 提示词优化

系统提示词已经过优化，特别强调：

1. **N8N 工作流优先**：当用户要求处理文件但没有指定具体工具时，优先使用 N8N 工作流
2. **工具描述完整**：包含所有可用工具的详细描述和参数说明
3. **调用格式明确**：要求 LLM 使用 JSON 格式进行工具调用
4. **场景识别**：能够识别用户意图，智能选择工具

## 注意事项

1. 确保工具已初始化（系统会自动初始化）
2. 确保 N8N API 地址已配置（通过 `N8N_API` 环境变量）
3. 文件需要在 `uploads` 目录下，或提供完整路径
4. 工具调用支持多轮迭代（最多 3 轮）

