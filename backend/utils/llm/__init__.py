"""
大模型模块 - 可配置的 LLM 调用接口

支持多种模型提供商：
- 阿里云通义千问 (qwen-long-latest)
- OpenAI (gpt-4, gpt-3.5-turbo 等)

通过 .env 文件配置模型提供商和 API 密钥
"""

from backend.utils.llm.client import LLMClient, get_llm_client
from backend.utils.llm.config import LLMConfig, get_llm_config
from backend.utils.llm.providers import (
    LLMProvider,
    ProviderType,
    ChatMessage,
    LLMResponse,
)

__all__ = [
    "LLMClient",
    "get_llm_client",
    "LLMConfig",
    "get_llm_config",
    "LLMProvider",
    "ProviderType",
    "ChatMessage",
    "LLMResponse",
]

