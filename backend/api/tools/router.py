"""
工具相关的 API 路由，用于管理工具的注册、执行等操作
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import traceback

from backend.utils.langdock import get_registry
from backend.utils.langdock.models import ToolInfo
from backend.utils.langdock.initialize import initialize_default_tools
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# 创建工具模块的路由
router = APIRouter(prefix="/tools", tags=["Tools"])

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
    registry = get_registry()
    return registry.list_tools()


@router.get("/{tool_name}", summary="获取指定工具的信息")
async def get_tool_info(tool_name: str) -> ToolInfo:
    """
    获取指定工具的详细信息
    """
    registry = get_registry()
    tool = registry.get(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"工具 '{tool_name}' 未找到")
    return tool.info


@router.post("/execute", summary="执行工具")
async def execute_tool(request: ToolExecuteRequest) -> ToolExecuteResponse:
    """
    执行指定的工具
    
    - **tool_name**: 工具名称
    - **parameters**: 工具参数（键值对）
    """
    try:
        logger.info(f"执行工具: {request.tool_name}, 参数: {request.parameters}")
        
        registry = get_registry()
        tool = registry.get(request.tool_name)
        
        if not tool:
            error_msg = f"工具 '{request.tool_name}' 未找到。可用工具: {registry.list_tool_names()}"
            logger.warning(error_msg)
            raise HTTPException(
                status_code=404,
                detail=error_msg
            )
        
        # 执行工具
        result = await tool.execute(**request.parameters)
        
        if result.success:
            logger.info(f"工具 {request.tool_name} 执行成功，耗时: {result.execution_time:.3f}秒")
        else:
            logger.warning(f"工具 {request.tool_name} 执行失败: {result.error}")
        
        return ToolExecuteResponse(
            success=result.success,
            data=result.data,
            error=result.error,
            execution_time=result.execution_time
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
    registry = get_registry()
    return {"tool_names": registry.list_tool_names()}

