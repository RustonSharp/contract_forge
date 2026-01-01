import os
# 解决 Mac 上的库冲突和多进程 fork 问题（必须在导入其他模块之前设置）
os.environ.setdefault('KMP_DUPLICATE_LIB_OK', 'True')
os.environ.setdefault('OBJC_DISABLE_INITIALIZE_FORK_SAFETY', 'YES')

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
# 修改为全路径导入
from backend.api import main_router
from backend.utils.logger import get_logger, setup_logging
import uvicorn
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

# 3. 全局 PaddleOCR 引擎初始化（在服务启动时加载）
global_ocr_engine = None

@app.on_event("startup")
async def load_ocr_engine():
    """在 FastAPI 启动时全局初始化 PaddleOCR 引擎"""
    global global_ocr_engine
    try:
        from paddleocr import PaddleOCR
        import os
        
        logger.info("正在初始化 PaddleOCR 引擎...")
        
        # 设置环境变量，避免 Mac 下的多进程问题
        os.environ.setdefault('KMP_DUPLICATE_LIB_OK', 'TRUE')
        os.environ.setdefault('OBJC_DISABLE_INITIALIZE_FORK_SAFETY', 'YES')
        os.environ.setdefault('DISABLE_MODEL_SOURCE_CHECK', 'True')
        
        # 初始化 PaddleOCR，默认使用中文识别
        # use_angle_cls=True 启用方向分类器，提高识别准确率
        # lang='ch' 使用中文模型
        global_ocr_engine = PaddleOCR(use_angle_cls=True, lang='ch')
        logger.info("✓ PaddleOCR 引擎初始化成功")
        
        # 将全局引擎设置到 OCRParserTool
        from backend.service.tools.core_tools import OCRParserTool
        OCRParserTool._ocr_instance = global_ocr_engine
        OCRParserTool._ocr_initialized = True
    except ImportError as e:
        logger.warning(f"PaddleOCR 未安装: {str(e)}，将在首次使用时尝试初始化")
        global_ocr_engine = None
    except Exception as e:
        logger.warning(f"PaddleOCR 引擎初始化失败: {str(e)}，将在首次使用时尝试初始化")
        global_ocr_engine = None

@app.on_event("shutdown")
async def cleanup_ocr_engine():
    """在服务关闭时清理 PaddleOCR 引擎"""
    global global_ocr_engine
    if global_ocr_engine is not None:
        logger.info("清理 PaddleOCR 引擎...")
        global_ocr_engine = None

# 4. 包含 API 路由
app.include_router(main_router)

# 5. 全局异常处理器
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