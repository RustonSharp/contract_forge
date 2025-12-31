"""
工作流状态管理服务
用于管理 N8N 工作流的执行状态
"""

import uuid
import time
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class WorkflowStatus(str, Enum):
    """工作流状态枚举"""
    PENDING = "pending"  # 等待中
    RUNNING = "running"  # 运行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败


class WorkflowStatusService:
    """工作流状态管理服务"""
    
    def __init__(self):
        # 使用内存字典存储工作流状态
        # 格式: {workflow_id: {status, file_path, result, created_at, updated_at}}
        self._status_store: Dict[str, Dict[str, Any]] = {}
        logger.info("工作流状态管理服务初始化")
    
    def create_workflow_status(self, file_path: str, initial_status: WorkflowStatus = WorkflowStatus.PENDING) -> str:
        """
        创建工作流状态记录
        
        Args:
            file_path: 文件相对路径
            initial_status: 初始状态，默认为 PENDING
        
        Returns:
            workflow_id: 工作流 ID
        """
        workflow_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        self._status_store[workflow_id] = {
            "workflow_id": workflow_id,
            "status": initial_status.value,
            "file_path": file_path,
            "result": None,
            "message": None,
            "error": None,
            "created_at": now,
            "updated_at": now
        }
        
        logger.info(f"创建工作流状态记录: {workflow_id}, 文件: {file_path}, 状态: {initial_status.value}")
        return workflow_id
    
    def update_workflow_status(
        self,
        workflow_id: str,
        status: WorkflowStatus,
        result: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None,
        error: Optional[str] = None
    ) -> bool:
        """
        更新工作流状态
        
        Args:
            workflow_id: 工作流 ID
            status: 新状态
            result: 结果数据（可选）
            message: 消息（可选）
            error: 错误信息（可选）
        
        Returns:
            是否更新成功
        """
        if workflow_id not in self._status_store:
            logger.warning(f"工作流状态记录不存在: {workflow_id}")
            return False
        
        self._status_store[workflow_id].update({
            "status": status.value,
            "updated_at": datetime.now().isoformat()
        })
        
        if result is not None:
            self._status_store[workflow_id]["result"] = result
        
        if message is not None:
            self._status_store[workflow_id]["message"] = message
        
        if error is not None:
            self._status_store[workflow_id]["error"] = error
        
        logger.info(f"更新工作流状态: {workflow_id}, 状态: {status.value}")
        return True
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        获取工作流状态
        
        Args:
            workflow_id: 工作流 ID
        
        Returns:
            工作流状态信息，如果不存在返回 None
        """
        return self._status_store.get(workflow_id)
    
    def delete_workflow_status(self, workflow_id: str) -> bool:
        """
        删除工作流状态记录
        
        Args:
            workflow_id: 工作流 ID
        
        Returns:
            是否删除成功
        """
        if workflow_id in self._status_store:
            del self._status_store[workflow_id]
            logger.info(f"删除工作流状态记录: {workflow_id}")
            return True
        return False
    
    def list_workflow_statuses(self, limit: int = 100) -> list:
        """
        列出所有工作流状态（按更新时间倒序）
        
        Args:
            limit: 返回数量限制
        
        Returns:
            工作流状态列表
        """
        statuses = list(self._status_store.values())
        # 按更新时间倒序排序
        statuses.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return statuses[:limit]


# 全局单例实例
_workflow_status_service: Optional[WorkflowStatusService] = None


def get_workflow_status_service() -> WorkflowStatusService:
    """获取工作流状态管理服务单例"""
    global _workflow_status_service
    if _workflow_status_service is None:
        _workflow_status_service = WorkflowStatusService()
    return _workflow_status_service

