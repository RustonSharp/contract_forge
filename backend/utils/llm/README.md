# LLM 模块使用说明

## 概述

`backend/utils/llm` 模块提供了统一的大模型调用接口，支持多种模型提供商，通过 `.env` 文件进行配置。

## 支持的提供商

- **阿里云通义千问** (`aliyun`) - 支持 qwen-long-latest 等模型（**默认**）
- **OpenAI** (`openai`) - 支持 gpt-4, gpt-3.5-turbo 等模型

## 配置

在项目根目录创建 `.env` 文件，配置以下环境变量：

### 使用阿里云通义千问（北京地域）

```env
MODEL_PROVIDER=aliyun
DASHSCOPE_API_KEY=your_aliyun_api_key
MODEL_NAME=qwen-long-latest
MODEL_REGION=beijing
MODEL_TEMPERATURE=0.7
MODEL_MAX_TOKENS=2000
MODEL_TIMEOUT=60
```

### 使用阿里云通义千问（新加坡地域）

```env
MODEL_PROVIDER=aliyun
DASHSCOPE_API_KEY=your_aliyun_api_key
MODEL_NAME=qwen-long-latest
MODEL_REGION=singapore
MODEL_TEMPERATURE=0.7
MODEL_MAX_TOKENS=2000
MODEL_TIMEOUT=60
```

**注意**：
- 推荐使用 `DASHSCOPE_API_KEY` 作为环境变量名（阿里云标准环境变量名）
- 也可以使用 `MODEL_STUDIO_KEY` 作为备选
- 北京和新加坡地域的 API Key 不同，请确保使用对应地域的密钥
- 获取 API Key：https://help.aliyun.com/zh/model-studio/get-api-key

### 使用 OpenAI

```env
MODEL_PROVIDER=openai
MODEL_STUDIO_KEY=your_openai_api_key
MODEL_NAME=gpt-3.5-turbo
MODEL_TEMPERATURE=0.7
MODEL_MAX_TOKENS=2000
MODEL_TIMEOUT=60
```

### 环境变量说明

| 变量名 | 说明 | 必需 | 默认值 |
|--------|------|------|--------|
| `MODEL_PROVIDER` | 模型提供商 (aliyun/openai) | 否 | aliyun |
| `DASHSCOPE_API_KEY` | 阿里云 API 密钥（推荐） | 是* | - |
| `MODEL_STUDIO_KEY` | API 密钥（备选，兼容旧配置） | 是* | - |
| `OPENAI_API_KEY` | OpenAI API 密钥（备选） | 是* | - |
| `MODEL_NAME` | 模型名称 | 否 | 根据提供商自动设置 |
| `MODEL_REGION` | 阿里云地域 (beijing/singapore) | 否 | beijing |
| `MODEL_BASE_URL` | API 基础 URL（会覆盖地域设置） | 否 | 根据提供商和地域自动设置 |
| `MODEL_TEMPERATURE` | 温度参数 | 否 | 0.7 |
| `MODEL_MAX_TOKENS` | 最大 token 数 | 否 | - |
| `MODEL_TIMEOUT` | 超时时间（秒） | 否 | 60 |

\* 至少需要设置一个 API 密钥环境变量：
- 阿里云：优先使用 `DASHSCOPE_API_KEY`，也可使用 `MODEL_STUDIO_KEY`
- OpenAI：优先使用 `MODEL_STUDIO_KEY`，也可使用 `OPENAI_API_KEY`

## 使用方法

### 基础使用

```python
from backend.utils.llm import get_llm_client

# 获取客户端
client = get_llm_client()

# 方式1: 简单生成
response = await client.generate("你好")
print(response.content)

# 方式2: 带系统消息的聊天
text = await client.chat_simple(
    user_message="分析这个合同",
    system_message="你是一个专业的合同分析助手"
)
print(text)

# 方式3: 完整控制
from backend.utils.llm.providers import ChatMessage

messages = [
    ChatMessage(role="system", content="你是助手"),
    ChatMessage(role="user", content="你好"),
]
response = await client.chat(messages, temperature=0.5)
print(response.content)
print(response.usage)  # token 使用量
```

### 多轮对话

```python
messages = [
    ChatMessage(role="system", content="你是助手"),
    ChatMessage(role="user", content="我的名字是张三"),
]

# 第一轮
response = await client.chat(messages)
print(response.content)

# 第二轮（添加历史消息）
messages.append(ChatMessage(role="assistant", content=response.content))
messages.append(ChatMessage(role="user", content="你还记得我的名字吗？"))
response = await client.chat(messages)
print(response.content)
```

### 自定义参数

```python
# 使用自定义温度
response = await client.generate(
    "写一首诗",
    temperature=0.9,  # 更高的创造性
    max_tokens=500
)
```

## 在其他模块中使用

```python
# 在 langdock 工具中使用
from backend.utils.llm import get_llm_client

class MyTool(BaseTool):
    async def execute(self, **kwargs):
        client = get_llm_client()
        response = await client.generate("分析合同风险")
        return ToolResult(success=True, data=response.content)
```

## 注意事项

1. **API 密钥安全**: 确保 `.env` 文件已添加到 `.gitignore`，不要提交到版本控制
2. **依赖安装**: 使用 OpenAI 提供商需要安装 `openai` 库（已在 requirements.txt 中）
3. **阿里云配置**: 阿里云使用 OpenAI 兼容的 API，确保 API 密钥有效且有权限访问对应模型
4. **错误处理**: 建议在使用时添加 try-except 处理网络错误和 API 错误

## 示例

查看 `backend/utils/llm/example.py` 获取更多使用示例。

