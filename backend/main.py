from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
# 修改为全路径导入
from backend.api import main_router
from backend.utils.logger import get_logger, setup_logging
import uvicorn
import os
import traceback

# 初始化日志
setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="Contract Forge API",
    description="智能合同审计系统后端",
    version="1.0.0"
)

# 1. CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

# 2. 确保上传目录在服务启动前就存在
UPLOAD_DIR = "./uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)
    logger.info(f"创建上传目录: {UPLOAD_DIR}")

# 3. 包含 API 路由
app.include_router(main_router)

# 4. 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器，捕获所有未处理的异常"""
    error_trace = traceback.format_exc()
    logger.error(f"未处理的异常: {str(exc)}\n请求路径: {request.url.path}\n{error_trace}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": f"内部服务器错误: {str(exc)}",
            "detail": "详细信息请查看服务器日志"
        }
    )

@app.get("/", tags=["Health Check"])
async def health_check():
    logger.info("健康检查请求")
    return {"status": "running", "api_docs": "/docs"}

if __name__ == "__main__":
    logger.info("🚀 Contract Forge 后端启动中...")
    logger.info("📖 接口文档地址: http://localhost:8000/docs")
    # 这里必须写 "backend.main:app" 而不是 "main:app"
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)