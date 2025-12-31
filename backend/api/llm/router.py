"""
LLM 对话接口路由
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
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
    file_name: Optional[str] = None  # 已弃用，请使用 file_path
    file_path: Optional[str] = None  # 文件路径（相对于 uploads 目录，如 "2025-12-29/test_contract.pdf"）
    messages: List[ChatMessage]
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    enable_tools: bool = True  # 是否启用工具调用


class ChatResponse(BaseModel):
    """对话响应"""
    message: str
    workflow_id: Optional[str] = None  # 工作流 ID（如果调用了 n8n_workflow_trigger）
    tool_calls: Optional[List[Dict[str, Any]]] = None
    usage: Optional[Dict[str, Any]] = None


@router.post("/chat", summary="与 LLM 对话（支持工具调用，智能查找文件）")
async def chat(request: ChatRequest) -> ChatResponse:
    """
    与 LLM 进行对话，支持工具调用
    
    此接口用于前端没有选中合同的情况，会根据用户描述智能查找文件。
    例如："帮我处理一下昨天上传的文件"
    
    当用户请求处理文件时，LLM 会自动调用相应的工具（如 N8N 工作流）
    """
    try:
        logger.info(f"收到对话请求（智能查找模式），消息数量: {len(request.messages)}")
        
        chat_service = LLMChatService()
        response = await chat_service.chat(
            messages=[{"role": msg.role, "content": msg.content} for msg in request.messages],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            enable_tools=request.enable_tools,
            file_name=None  # 不传递 file_name，使用智能查找
        )
        
        return ChatResponse(
            message=response["message"],
            workflow_id=response.get("workflow_id"),
            tool_calls=response.get("tool_calls"),
            usage=response.get("usage")
        )
    
    except Exception as e:
        logger.error(f"对话处理失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"对话处理失败: {str(e)}")

@router.post("/chat_with_file_name", summary="与 LLM 对话（指定文件路径，直接使用文件）")
async def chat_with_file_name(request: ChatRequest) -> ChatResponse:
    """
    与 LLM 进行对话，支持工具调用
    
    此接口用于前端选中了合同的情况，会直接使用指定的文件路径。
    需要传递 file_path 参数（相对于 uploads 目录，如 "2025-12-29/test_contract.pdf"）。
    
    Args:
        request.file_path: 文件路径（必填，优先使用）
        request.file_name: 文件名（已弃用，仅作为向后兼容）
    """
    try:
        # 优先使用 file_path，如果没有则使用 file_name（向后兼容）
        file_path = request.file_path or request.file_name
        if not file_path:
            raise HTTPException(status_code=400, detail="file_path 参数不能为空")
        
        logger.info(f"收到对话请求（指定文件模式），文件路径: {file_path}，消息数量: {len(request.messages)}")
        
        chat_service = LLMChatService()
        response = await chat_service.chat(
            messages=[{"role": msg.role, "content": msg.content} for msg in request.messages],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            enable_tools=request.enable_tools,
            file_path=file_path  # 传递 file_path，直接使用文件
        )
        
        return ChatResponse(
            message=response["message"],
            workflow_id=response.get("workflow_id"),
            tool_calls=response.get("tool_calls"),
            usage=response.get("usage")
        )
    
    except HTTPException:
        raise
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
            workflow_id=response.get("workflow_id"),
            tool_calls=response.get("tool_calls"),
            usage=response.get("usage")
        )
    
    except Exception as e:
        logger.error(f"对话处理失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"对话处理失败: {str(e)}")


@router.post("/convert_risk_to_html", summary="将风险判断结果转换为 HTML 格式")
async def convert_risk_to_html(request: Dict[str, Any]) -> JSONResponse:
    """
    将风险等级判断的结果转换为 HTML 格式，用于邮件发送
    
    此接口接收风险评估工具的返回数据，使用 LLM 将其转换为格式良好、专业的 HTML 邮件正文。
    
    支持多种数据格式：
    1. 直接发送 data 对象: {"success": true, "data": {...}}
    2. 包含 body 的对象: {"body": {"success": true, "data": {...}}}
    3. 数组格式: [{"body": {"success": true, "data": {...}}}]
    
    Returns:
        JSONResponse: 包含 html_content 和 file_path 的 JSON 响应
            - html_content: HTML 格式的邮件正文
            - file_path: 文件的相对路径（相对于 uploads 目录）
    """
    try:
        logger.info(f"收到风险数据转 HTML 请求，数据类型: {type(request).__name__}")
        
        chat_service = LLMChatService()
        result = await chat_service.convert_risk_to_html(request)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        logger.error(f"风险数据转 HTML 失败: {str(e)}", exc_info=True)
        error_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>错误</title>
</head>
<body>
    <p style="color: red;">转换失败: {str(e)}</p>
</body>
</html>"""
        return JSONResponse(
            content={
                "html_content": error_html,
                "file_path": None
            },
            status_code=500
        )

