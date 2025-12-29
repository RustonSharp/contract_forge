"""
合同文件管理接口路由
支持文件上传和查询
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from backend.service.files.service import FileService, FileInfo as ServiceFileInfo
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/files", tags=["Files"])


class FileInfo(BaseModel):
    """文件信息（API 层）"""
    file_name: str
    file_path: str
    file_size: int
    upload_date: str
    file_type: str


class FileListResponse(BaseModel):
    """文件列表响应"""
    success: bool
    total: int
    files: List[FileInfo]
    date: Optional[str] = None


class FileUploadResponse(BaseModel):
    """文件上传响应"""
    success: bool
    message: str
    file_info: Optional[FileInfo] = None
    error: Optional[str] = None


@router.post("/upload", summary="上传合同文件")
async def upload_file(file: UploadFile = File(...)) -> FileUploadResponse:
    """
    上传合同文件
    
    文件会自动保存到 uploads/YYYY-MM-DD/ 目录下，按日期组织
    """
    try:
        logger.info(f"收到文件上传请求: {file.filename}")
        
        # 验证文件类型
        allowed_extensions = [".pdf", ".docx", ".doc", ".jpg", ".jpeg", ".png"]
        file_ext = None
        if file.filename:
            file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file_ext}。支持的类型: {', '.join(allowed_extensions)}"
            )
        
        # 读取文件内容
        content = await file.read()
        
        # 保存文件
        file_service = FileService()
        file_info = await file_service.save_file(
            filename=file.filename or "unknown",
            content=content
        )
        
        logger.info(f"文件上传成功: {file_info.file_path}")
        
        # 将 Service 层的 FileInfo 转换为 API 层的 FileInfo
        return FileUploadResponse(
            success=True,
            message="文件上传成功",
            file_info=FileInfo(
                file_name=file_info.file_name,
                file_path=file_info.file_path,
                file_size=file_info.file_size,
                upload_date=file_info.upload_date,
                file_type=file_info.file_type
            )
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}", exc_info=True)
        return FileUploadResponse(
            success=False,
            message="文件上传失败",
            error=str(e)
        )


@router.get("/list", summary="查询已上传的文件列表")
async def list_files(
    date: Optional[str] = Query(None, description="日期筛选，格式: YYYY-MM-DD，如 2025-11-12"),
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
) -> FileListResponse:
    """
    查询已上传的文件列表
    
    可以按日期筛选，支持分页
    """
    try:
        logger.info(f"查询文件列表，日期: {date}, 页码: {page}, 每页: {page_size}")
        
        file_service = FileService()
        
        # 如果指定了日期，验证格式
        if date:
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="日期格式错误，应为 YYYY-MM-DD，如 2025-11-12"
                )
        
        service_files = await file_service.list_files(date=date, page=page, page_size=page_size)
        
        # 将 Service 层的 FileInfo 转换为 API 层的 FileInfo
        files = [
            FileInfo(
                file_name=f.file_name,
                file_path=f.file_path,
                file_size=f.file_size,
                upload_date=f.upload_date,
                file_type=f.file_type
            )
            for f in service_files
        ]
        
        return FileListResponse(
            success=True,
            total=len(files),
            files=files,
            date=date
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询文件列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询文件列表失败: {str(e)}")


@router.get("/list/dates", summary="获取所有有文件的日期列表")
async def list_dates() -> JSONResponse:
    """
    获取所有有文件的日期列表（用于筛选）
    """
    try:
        logger.info("查询所有有文件的日期")
        
        file_service = FileService()
        dates = await file_service.list_dates()
        
        return JSONResponse(content={
            "success": True,
            "dates": dates,
            "total": len(dates)
        })
    
    except Exception as e:
        logger.error(f"查询日期列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询日期列表失败: {str(e)}")


@router.get("/info/{file_name:path}", summary="获取文件信息")
async def get_file_info(file_name: str) -> FileInfo:
    """
    获取指定文件的信息
    """
    try:
        logger.info(f"查询文件信息: {file_name}")
        
        file_service = FileService()
        service_file_info = await file_service.get_file_info(file_name)
        
        if not service_file_info:
            raise HTTPException(status_code=404, detail=f"文件不存在: {file_name}")
        
        # 将 Service 层的 FileInfo 转换为 API 层的 FileInfo
        return FileInfo(
            file_name=service_file_info.file_name,
            file_path=service_file_info.file_path,
            file_size=service_file_info.file_size,
            upload_date=service_file_info.upload_date,
            file_type=service_file_info.file_type
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询文件信息失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询文件信息失败: {str(e)}")

