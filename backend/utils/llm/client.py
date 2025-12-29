"""
LLM 客户端 - 统一的模型调用接口
"""

from typing import List, Optional, Dict, Any
from backend.utils.llm.config import get_llm_config, LLMConfig
from backend.utils.llm.providers import (
    LLMProvider,
    ChatMessage,
    LLMResponse,
    create_provider,
)


class LLMClient:
    """LLM 客户端，提供统一的模型调用接口"""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """
        初始化 LLM 客户端
        
        Args:
            config: LLM 配置，如果为 None 则从环境变量加载
        """
        self.config = config or get_llm_config()
        self._provider: Optional[LLMProvider] = None
    
    @property
    def provider(self) -> LLMProvider:
        """获取提供商实例（懒加载）"""
        if self._provider is None:
            self._provider = create_provider(self.config)
        return self._provider
    
    async def chat(
        self,
        messages: List[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        发送聊天请求
        
        Args:
            messages: 消息列表
            temperature: 温度参数，覆盖配置中的值
            max_tokens: 最大 token 数，覆盖配置中的值
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: LLM 响应
        """
        params = {}
        if temperature is not None:
            params["temperature"] = temperature
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
        params.update(kwargs)
        
        return await self.provider.chat(messages, **params)
    
    async def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        生成文本（简化接口）
        
        Args:
            prompt: 提示词
            temperature: 温度参数，覆盖配置中的值
            max_tokens: 最大 token 数，覆盖配置中的值
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: LLM 响应
        """
        params = {}
        if temperature is not None:
            params["temperature"] = temperature
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
        params.update(kwargs)
        
        return await self.provider.generate(prompt, **params)
    
    async def chat_simple(
        self,
        user_message: str,
        system_message: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        简化的聊天接口，直接返回文本内容
        
        Args:
            user_message: 用户消息
            system_message: 系统消息（可选）
            **kwargs: 其他参数
            
        Returns:
            str: 模型返回的文本内容
        """
        messages = []
        if system_message:
            messages.append(ChatMessage(role="system", content=system_message))
        messages.append(ChatMessage(role="user", content=user_message))
        
        response = await self.chat(messages, **kwargs)
        return response.content


# 全局客户端实例
_client: Optional[LLMClient] = None


def get_llm_client(config: Optional[LLMConfig] = None) -> LLMClient:
    """
    获取 LLM 客户端实例（单例模式）
    
    Args:
        config: LLM 配置，如果为 None 则从环境变量加载
        
    Returns:
        LLMClient: LLM 客户端实例
    """
    global _client
    if _client is None:
        _client = LLMClient(config)
    return _client

