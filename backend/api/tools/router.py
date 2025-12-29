"""
工具相关的 API 路由，用于管理工具的注册、执行等操作
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import traceback

from backend.service.tools.service import ToolService
from backend.service.tools.models import ToolInfo
from backend.service.tools.initialize import initialize_default_tools
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# 创建工具模块的路由
router = APIRouter(prefix="/tools", tags=["Tools"])

# 初始化工具服务
tool_service = ToolService()

# 初始化默认工具（只初始化一次）
_initialized = False
if not _initialized:
    initialize_default_tools()
    _initialized = True


class ToolExecuteRequest(BaseModel):
    """工具执行请求"""
    tool_name: str
    parameters: Dict[str, Any] = {}


class ToolExecuteResponse(BaseModel):
    """工具执行响应"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None


@router.get("", summary="获取所有已注册的工具列表")
async def list_tools() -> List[ToolInfo]:
    """
    获取所有已注册的工具列表及其信息
    """
    return tool_service.list_tools()


@router.get("/{tool_name}", summary="获取指定工具的信息")
async def get_tool_info(tool_name: str) -> ToolInfo:
    """
    获取指定工具的详细信息
    """
    tool_info = tool_service.get_tool_info(tool_name)
    if not tool_info:
        raise HTTPException(status_code=404, detail=f"工具 '{tool_name}' 未找到")
    return tool_info


@router.post("/execute", summary="执行工具")
async def execute_tool(request: ToolExecuteRequest) -> ToolExecuteResponse:
    """
    执行指定的工具
    
    - **tool_name**: 工具名称
    - **parameters**: 工具参数（键值对）
    """
    try:
        # 调用Service层执行工具
        result = await tool_service.execute_tool(
            request.tool_name,
            **request.parameters
        )
        
        return ToolExecuteResponse(
            success=result.success,
            data=result.data,
            error=result.error,
            execution_time=result.execution_time
        )
    
    except ValueError as e:
        # 工具不存在等业务错误
        error_msg = str(e)
        logger.warning(error_msg)
        raise HTTPException(
            status_code=404,
            detail=error_msg
        )
    except HTTPException:
        # 重新抛出 HTTP 异常（如 404）
        raise
    except Exception as e:
        # 捕获所有其他异常，记录日志并返回 500 错误
        error_trace = traceback.format_exc()
        logger.error(f"执行工具 {request.tool_name} 时发生未预期的错误: {str(e)}\n{error_trace}")
        
        # 返回错误响应而不是抛出异常，这样 N8N 可以获取到错误信息
        return ToolExecuteResponse(
            success=False,
            data=None,
            error=f"工具执行时发生内部错误: {str(e)}。详细信息请查看服务器日志。",
            execution_time=None
        )


@router.get("/names", summary="获取所有工具名称")
async def list_tool_names() -> Dict[str, List[str]]:
    """
    获取所有已注册工具的名称列表
    """
    return {"tool_names": tool_service.list_tool_names()}

