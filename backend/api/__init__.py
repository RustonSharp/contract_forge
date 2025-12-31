"""
API 模块主入口
统一注册所有模块的路由
"""

from fastapi import APIRouter
from backend.api.tools.router import router as tools_router
from backend.api.llm.router import router as llm_router
from backend.api.files.router import router as files_router
from backend.api.workflow.router import router as workflow_router

# 创建主路由
main_router = APIRouter(prefix="/api", tags=["API"])

# 注册各个模块的路由
main_router.include_router(tools_router)
main_router.include_router(llm_router)
main_router.include_router(files_router)
main_router.include_router(workflow_router)

__all__ = ["main_router"]

