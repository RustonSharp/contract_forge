"""
工具相关的 API 路由，用于管理工具的注册、执行等操作
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel

from backend.utils.langdock import get_registry
from backend.utils.langdock.models import ToolInfo
from backend.utils.langdock.initialize import initialize_default_tools

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
    data: Any = None
    error: str = None
    execution_time: float = None


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
    registry = get_registry()
    tool = registry.get(request.tool_name)
    
    if not tool:
        raise HTTPException(
            status_code=404,
            detail=f"工具 '{request.tool_name}' 未找到。可用工具: {registry.list_tool_names()}"
        )
    
    # 执行工具
    result = await tool.execute(**request.parameters)
    
    return ToolExecuteResponse(
        success=result.success,
        data=result.data,
        error=result.error,
        execution_time=result.execution_time
    )


@router.get("/names", summary="获取所有工具名称")
async def list_tool_names() -> Dict[str, List[str]]:
    """
    获取所有已注册工具的名称列表
    """
    registry = get_registry()
    return {"tool_names": registry.list_tool_names()}

