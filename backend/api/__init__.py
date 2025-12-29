"""
API 模块主入口
统一注册所有模块的路由
"""

from fastapi import APIRouter
from backend.api.tools.router import router as tools_router

# 创建主路由
main_router = APIRouter(prefix="/api", tags=["API"])

# 注册各个模块的路由
main_router.include_router(tools_router)

__all__ = ["main_router"]

