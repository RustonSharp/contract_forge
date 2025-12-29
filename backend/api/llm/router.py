"""
LLM 对话接口路由
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from backend.service.llm.service import LLMChatService
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/llm", tags=["LLM Chat"])


class ChatMessage(BaseModel):
    """聊天消息"""
    role: str = "user"  # user, assistant, system
    content: str


class ChatRequest(BaseModel):
    """对话请求"""
    messages: List[ChatMessage]
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    enable_tools: bool = True  # 是否启用工具调用


class ChatResponse(BaseModel):
    """对话响应"""
    message: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    usage: Optional[Dict[str, Any]] = None


@router.post("/chat", summary="与 LLM 对话（支持工具调用）")
async def chat(request: ChatRequest) -> ChatResponse:
    """
    与 LLM 进行对话，支持工具调用
    
    当用户请求处理文件时，LLM 会自动调用相应的工具（如 N8N 工作流）
    """
    try:
        logger.info(f"收到对话请求，消息数量: {len(request.messages)}")
        
        chat_service = LLMChatService()
        response = await chat_service.chat(
            messages=[{"role": msg.role, "content": msg.content} for msg in request.messages],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            enable_tools=request.enable_tools
        )
        
        return ChatResponse(
            message=response["message"],
            tool_calls=response.get("tool_calls"),
            usage=response.get("usage")
        )
    
    except Exception as e:
        logger.error(f"对话处理失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"对话处理失败: {str(e)}")


@router.post("/chat/simple", summary="简单对话接口（单条消息）")
async def chat_simple(user_message: str, system_message: Optional[str] = None) -> ChatResponse:
    """
    简化的对话接口，只需提供用户消息
    
    Args:
        user_message: 用户消息
        system_message: 系统消息（可选）
    """
    try:
        logger.info(f"收到简单对话请求: {user_message[:50]}...")
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": user_message})
        
        chat_service = LLMChatService()
        response = await chat_service.chat(
            messages=messages,
            enable_tools=True
        )
        
        return ChatResponse(
            message=response["message"],
            tool_calls=response.get("tool_calls"),
            usage=response.get("usage")
        )
    
    except Exception as e:
        logger.error(f"对话处理失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"对话处理失败: {str(e)}")

