"""
工作流状态管理 API 路由
用于管理 N8N 工作流的执行状态
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from backend.service.workflow.service import get_workflow_status_service, WorkflowStatus
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/workflow", tags=["Workflow Status"])

# 获取工作流状态管理服务
workflow_status_service = get_workflow_status_service()


class UpdateWorkflowStatusRequest(BaseModel):
    """更新工作流状态请求"""
    workflow_id: str
    status: str  # pending, running, completed, failed
    result: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error: Optional[str] = None


class UpdateWorkflowStatusResponse(BaseModel):
    """更新工作流状态响应"""
    success: bool
    workflow_id: str
    message: str


class WorkflowStatusResponse(BaseModel):
    """工作流状态响应"""
    workflow_id: str
    status: str
    file_path: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str


@router.post("/status/update", summary="更新工作流状态")
async def update_workflow_status(request: UpdateWorkflowStatusRequest) -> UpdateWorkflowStatusResponse:
    """
    更新工作流状态
    
    此接口由 N8N 工作流在完成或失败时调用，用于更新工作流的执行状态。
    
    状态值：
    - pending: 等待中
    - running: 运行中
    - completed: 已完成
    - failed: 失败
    """
    try:
        # 验证状态值
        try:
            status_enum = WorkflowStatus(request.status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的状态值: {request.status}。有效值: {', '.join([s.value for s in WorkflowStatus])}"
            )
        
        # 更新状态
        success = workflow_status_service.update_workflow_status(
            workflow_id=request.workflow_id,
            status=status_enum,
            result=request.result,
            message=request.message,
            error=request.error
        )
        
        if not success:
            raise HTTPException(status_code=404, detail=f"工作流状态记录不存在: {request.workflow_id}")
        
        logger.info(f"工作流状态已更新: {request.workflow_id}, 状态: {request.status}")
        
        return UpdateWorkflowStatusResponse(
            success=True,
            workflow_id=request.workflow_id,
            message="工作流状态已更新"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新工作流状态失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新工作流状态失败: {str(e)}")


@router.get("/status/{workflow_id}", summary="查询工作流状态")
async def get_workflow_status(workflow_id: str) -> WorkflowStatusResponse:
    """
    查询工作流状态
    
    前端可以使用此接口轮询工作流状态，确定工作流是否完成。
    
    Args:
        workflow_id: 工作流 ID
    
    Returns:
        工作流状态信息
    """
    try:
        status_data = workflow_status_service.get_workflow_status(workflow_id)
        
        if not status_data:
            raise HTTPException(status_code=404, detail=f"工作流状态记录不存在: {workflow_id}")
        
        return WorkflowStatusResponse(**status_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询工作流状态失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询工作流状态失败: {str(e)}")


@router.post("/status/create", summary="创建工作流状态记录")
async def create_workflow_status(file_path: str, initial_status: str = "pending") -> WorkflowStatusResponse:
    """
    创建工作流状态记录
    
    在启动工作流之前调用此接口创建状态记录，获取 workflow_id。
    
    Args:
        file_path: 文件相对路径（相对于 uploads 目录）
        initial_status: 初始状态，默认为 pending
    
    Returns:
        工作流状态信息（包含 workflow_id）
    """
    try:
        # 验证初始状态值
        try:
            status_enum = WorkflowStatus(initial_status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的初始状态值: {initial_status}。有效值: {', '.join([s.value for s in WorkflowStatus])}"
            )
        
        # 创建工作流状态记录
        workflow_id = workflow_status_service.create_workflow_status(
            file_path=file_path,
            initial_status=status_enum
        )
        
        # 获取创建的状态数据
        status_data = workflow_status_service.get_workflow_status(workflow_id)
        
        logger.info(f"创建工作流状态记录: {workflow_id}, 文件: {file_path}")
        
        return WorkflowStatusResponse(**status_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建工作流状态记录失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建工作流状态记录失败: {str(e)}")

