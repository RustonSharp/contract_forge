"""
Contract Forge - 后端 API 服务
智能合同处理自动化系统 - 主入口

启动命令:
    uvicorn main:app --reload --port 8001
    
或使用:
    python main.py
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
from datetime import datetime

from apis.contract_type import router as contract_type_router
from utils.logger import get_logger
from config import Config

# 创建日志记录器
logger = get_logger(__name__)


# ============================================
# 生命周期事件处理（新版本）
# ============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("=" * 70)
    logger.info("🚀 Contract Forge API 启动中...")
    logger.info("=" * 70)
    logger.info(f"📦 环境: {Config.ENVIRONMENT}")
    logger.info(f"🔧 调试模式: {Config.API_DEBUG}")
    logger.info(f"📡 API 地址: http://{Config.API_HOST}:{Config.API_PORT}")
    logger.info(f"📚 API 文档: http://{Config.API_HOST}:{Config.API_PORT}/docs")
    logger.info("=" * 70)
    
    # TODO: 初始化连接池等资源
    # ConnectionPool.initialize()
    
    yield  # 应用运行中...
    
    # 关闭时执行
    logger.info("=" * 70)
    logger.info("🛑 Contract Forge API 关闭中...")
    logger.info("=" * 70)
    
    # TODO: 清理资源
    # ConnectionPool.close_all()


# 创建 FastAPI 应用
app = FastAPI(
    title="Contract Forge API",
    description="智能合同处理自动化系统 - 后端 API",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI: http://localhost:8001/docs
    redoc_url="/redoc",  # ReDoc: http://localhost:8001/redoc
    lifespan=lifespan,  # 使用新的生命周期管理
)

# ============================================
# CORS 配置（允许前端跨域请求）
# ============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # 前端开发服务器
        "http://127.0.0.1:3000",
        "http://localhost:5173",  # Vite 默认端口
    ],
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有 HTTP 头
)


# ============================================
# 请求日志中间件
# ============================================
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有请求"""
    start_time = datetime.now()
    
    # 记录请求
    logger.info(f"📨 {request.method} {request.url.path}")
    
    # 处理请求
    response = await call_next(request)
    
    # 计算处理时间
    duration = (datetime.now() - start_time).total_seconds()
    
    # 记录响应
    logger.info(
        f"📤 {request.method} {request.url.path} "
        f"- {response.status_code} - {duration:.3f}s"
    )
    
    return response


# ============================================
# 异常处理
# ============================================
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    HTTPException 异常处理
    将 FastAPI 标准格式转换为统一的 API 响应格式
    """
    logger.warning(
        f"⚠️  HTTPException: {exc.status_code} - {exc.detail} "
        f"- {request.method} {request.url.path}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(f"❌ Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc),
            "message": "Internal server error"
        }
    )


# ============================================
# 路由注册
# ============================================

# 根路径
@app.get("/")
async def root():
    """API 根路径"""
    return {
        "message": "Welcome to Contract Forge API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "status": "running"
    }


# 健康检查
@app.get("/health")
async def health_check():
    """健康检查端点"""
    try:
        # 可以添加数据库连接检查等
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "Contract Forge API",
            "database": "connected",  # TODO: 实际检查数据库连接
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


# API 信息
@app.get("/api/info")
async def api_info():
    """API 信息"""
    return {
        "name": "Contract Forge API",
        "version": "1.0.0",
        "environment": Config.ENVIRONMENT,
        "endpoints": {
            "contract_types": "/api/contract-type",
            "contracts": "/api/contracts",
            "workflows": "/api/workflows",
        }
    }


# 注册合同类型路由
app.include_router(
    contract_type_router,
    prefix="/api"
)

# TODO: 注册其他路由
# app.include_router(contract_router, prefix="/api")
# app.include_router(workflow_router, prefix="/api")


# ============================================
# 主程序入口
# ============================================
if __name__ == "__main__":
    """
    直接运行此文件启动服务器
    
    使用方法：
        python main.py
    
    或使用 uvicorn 命令：
        uvicorn main:app --reload --port 8001
    """
    
    # 打印启动信息
    print("\n" + "=" * 70)
    print("🚀 Contract Forge - 后端 API 服务")
    print("=" * 70)
    print(f"📡 服务地址: http://{Config.API_HOST}:{Config.API_PORT}")
    print(f"📚 API 文档: http://{Config.API_HOST}:{Config.API_PORT}/docs")
    print(f"📖 ReDoc: http://{Config.API_HOST}:{Config.API_PORT}/redoc")
    print(f"🔧 环境: {Config.ENVIRONMENT}")
    print("=" * 70)
    print("按 Ctrl+C 停止服务器")
    print("=" * 70 + "\n")
    
    # 启动服务器
    uvicorn.run(
        "main:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=Config.API_DEBUG,  # 开发模式自动重载
        log_level="info"
    )

