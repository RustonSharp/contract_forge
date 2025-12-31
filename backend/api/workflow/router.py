"""
工作流状态管理 API 路由
用于管理 N8N 工作流的执行状态
"""

import json
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from backend.service.workflow.service import get_workflow_status_service, WorkflowStatus
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/workflow", tags=["Workflow Status"])

# 获取工作流状态管理服务
workflow_status_service = get_workflow_status_service()

# N8N 配置文件目录
N8N_CONFIG_DIR = Path(__file__).parent.parent.parent.parent / "n8n_config"


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


class WorkflowNode(BaseModel):
    """工作流节点信息"""
    id: str
    name: str
    type: str
    position: List[float]
    notes: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class WorkflowDefinitionResponse(BaseModel):
    """工作流定义响应"""
    name: str
    nodes: List[WorkflowNode]
    connections: Dict[str, Any]
    active: bool


@router.get("/definition", summary="获取完整工作流程定义")
async def get_workflow_definition(
    config_file: str = Query(default="合同处理自动化流程.json", description="配置文件名称")
) -> WorkflowDefinitionResponse:
    """
    获取完整工作流程定义
    
    从 n8n_config 目录读取工作流配置文件，返回完整的工作流定义。
    
    Args:
        config_file: 配置文件名称，默认为 "合同处理自动化流程.json"
    
    Returns:
        工作流定义信息
    """
    try:
        # 构建配置文件路径
        config_path = N8N_CONFIG_DIR / config_file
        
        # 检查文件是否存在
        if not config_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"工作流配置文件不存在: {config_file}"
            )
        
        # 读取 JSON 文件
        with open(config_path, "r", encoding="utf-8") as f:
            workflow_data = json.load(f)
        
        # 提取节点信息
        nodes = []
        for node_data in workflow_data.get("nodes", []):
            node = WorkflowNode(
                id=node_data.get("id", ""),
                name=node_data.get("name", ""),
                type=node_data.get("type", ""),
                position=node_data.get("position", [0, 0]),
                notes=node_data.get("notes"),
                parameters=node_data.get("parameters")
            )
            nodes.append(node)
        
        logger.info(f"读取工作流定义: {config_file}, 节点数: {len(nodes)}")
        
        return WorkflowDefinitionResponse(
            name=workflow_data.get("name", ""),
            nodes=nodes,
            connections=workflow_data.get("connections", {}),
            active=workflow_data.get("active", False)
        )
    
    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        logger.error(f"解析工作流配置文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"解析工作流配置文件失败: {str(e)}")
    except Exception as e:
        logger.error(f"获取工作流定义失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取工作流定义失败: {str(e)}")


class WorkflowProgressResponse(BaseModel):
    """工作流进度响应"""
    workflow_id: str
    status: str
    current_node: Optional[str] = None
    completed_nodes: List[str] = []
    file_path: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str


@router.get("/progress/{workflow_id}", summary="获取工作流当前进度")
async def get_workflow_progress(workflow_id: str) -> WorkflowProgressResponse:
    """
    获取工作流当前进度
    
    返回工作流的执行进度信息，包括当前执行的节点和已完成的节点。
    前端可以使用此接口轮询获取工作流进度。
    
    Args:
        workflow_id: 工作流 ID
    
    Returns:
        工作流进度信息
    """
    try:
        status_data = workflow_status_service.get_workflow_status(workflow_id)
        
        if not status_data:
            raise HTTPException(status_code=404, detail=f"工作流状态记录不存在: {workflow_id}")
        
        # 从 result 中提取当前节点和已完成节点信息
        result = status_data.get("result") or {}
        current_node = result.get("current_node") if isinstance(result, dict) else None
        completed_nodes = result.get("completed_nodes", []) if isinstance(result, dict) else []
        
        # 如果 result 中没有这些信息，尝试从 message 中推断
        # 这里可以根据实际业务逻辑进行扩展
        if not current_node and not completed_nodes:
            # 根据状态推断进度
            status = status_data.get("status", "")
            if status == "completed":
                # 如果已完成，可以标记所有节点为已完成（需要从定义中获取）
                completed_nodes = []
            elif status == "running":
                # 运行中，可以设置当前节点（需要从实际执行情况获取）
                current_node = None
        
        return WorkflowProgressResponse(
            workflow_id=status_data.get("workflow_id", ""),
            status=status_data.get("status", ""),
            current_node=current_node,
            completed_nodes=completed_nodes,
            file_path=status_data.get("file_path"),
            result=status_data.get("result"),
            message=status_data.get("message"),
            error=status_data.get("error"),
            created_at=status_data.get("created_at", ""),
            updated_at=status_data.get("updated_at", "")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工作流进度失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取工作流进度失败: {str(e)}")

