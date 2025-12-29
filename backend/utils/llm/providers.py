"""
LLM 提供商抽象和实现
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from backend.utils.llm.config import LLMConfig, ProviderType


class ChatMessage(BaseModel):
    """聊天消息"""
    role: str  # system, user, assistant
    content: str


class LLMResponse(BaseModel):
    """LLM 响应"""
    content: str
    usage: Optional[Dict[str, Any]] = None
    model: Optional[str] = None
    finish_reason: Optional[str] = None


class LLMProvider(ABC):
    """LLM 提供商抽象基类"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
    
    @abstractmethod
    async def chat(
        self,
        messages: List[ChatMessage],
        **kwargs
    ) -> LLMResponse:
        """
        发送聊天请求
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数（temperature, max_tokens 等）
            
        Returns:
            LLMResponse: LLM 响应
        """
        pass
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        **kwargs
    ) -> LLMResponse:
        """
        生成文本（简化接口）
        
        Args:
            prompt: 提示词
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: LLM 响应
        """
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI 提供商实现"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError(
                "使用 OpenAI 提供商需要安装 openai 库: pip install openai"
            )
        
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
        )
    
    async def chat(
        self,
        messages: List[ChatMessage],
        **kwargs
    ) -> LLMResponse:
        """OpenAI 聊天接口"""
        # 转换消息格式
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        # 合并配置参数
        params = {
            "model": self.config.model_name,
            "messages": openai_messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
        }
        
        if self.config.max_tokens:
            params["max_tokens"] = kwargs.get("max_tokens", self.config.max_tokens)
        
        # 调用 API
        try:
            response = await self.client.chat.completions.create(**params)
        except Exception as e:
            # 提供更友好的错误信息
            error_msg = str(e)
            if "401" in error_msg or "invalid_api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                raise ValueError(
                    f"API 密钥验证失败。请检查：\n"
                    f"1. API 密钥是否正确\n"
                    f"2. 对于 OpenAI，请使用 MODEL_STUDIO_KEY 或 OPENAI_API_KEY 环境变量\n"
                    f"3. 确保 API 密钥有权限访问所选模型\n"
                    f"原始错误: {error_msg}"
                ) from e
            raise
        
        # 解析响应
        choice = response.choices[0]
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        } if response.usage else None
        
        return LLMResponse(
            content=choice.message.content,
            usage=usage,
            model=response.model,
            finish_reason=choice.finish_reason,
        )
    
    async def generate(
        self,
        prompt: str,
        **kwargs
    ) -> LLMResponse:
        """OpenAI 生成接口"""
        messages = [ChatMessage(role="user", content=prompt)]
        return await self.chat(messages, **kwargs)


class AliyunProvider(LLMProvider):
    """阿里云通义千问提供商实现"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError(
                "使用阿里云提供商需要安装 openai 库: pip install openai"
            )
        
        # 阿里云使用 OpenAI 兼容的 API
        # 如果 base_url 未设置，使用默认的兼容端点
        base_url = config.base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=base_url,
            timeout=config.timeout,
        )
    
    async def chat(
        self,
        messages: List[ChatMessage],
        **kwargs
    ) -> LLMResponse:
        """阿里云聊天接口（使用 OpenAI 兼容 API）"""
        # 转换消息格式
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        # 合并配置参数
        params = {
            "model": self.config.model_name,
            "messages": openai_messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
        }
        
        if self.config.max_tokens:
            params["max_tokens"] = kwargs.get("max_tokens", self.config.max_tokens)
        
        # 调用 API
        try:
            response = await self.client.chat.completions.create(**params)
        except Exception as e:
            # 提供更友好的错误信息
            error_msg = str(e)
            if "401" in error_msg or "invalid_api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                raise ValueError(
                    f"API 密钥验证失败。请检查：\n"
                    f"1. API 密钥是否正确（使用 DASHSCOPE_API_KEY 环境变量）\n"
                    f"2. 确保 API 密钥是北京地域的密钥（如果使用北京地域）\n"
                    f"3. 确保 API 密钥有权限访问所选模型\n"
                    f"4. 检查 MODEL_REGION 设置是否正确（beijing/singapore）\n"
                    f"原始错误: {error_msg}"
                ) from e
            raise
        
        # 解析响应
        choice = response.choices[0]
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        } if response.usage else None
        
        return LLMResponse(
            content=choice.message.content,
            usage=usage,
            model=response.model,
            finish_reason=choice.finish_reason,
        )
    
    async def generate(
        self,
        prompt: str,
        **kwargs
    ) -> LLMResponse:
        """阿里云生成接口"""
        messages = [ChatMessage(role="user", content=prompt)]
        return await self.chat(messages, **kwargs)


def create_provider(config: LLMConfig) -> LLMProvider:
    """
    根据配置创建对应的提供商实例
    
    Args:
        config: LLM 配置
        
    Returns:
        LLMProvider: 提供商实例
    """
    if config.provider == ProviderType.OPENAI:
        return OpenAIProvider(config)
    elif config.provider == ProviderType.ALIYUN:
        return AliyunProvider(config)
    else:
        raise ValueError(f"不支持的提供商: {config.provider}")

