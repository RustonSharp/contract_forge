"""
文件服务层
处理文件上传、存储、查询等业务逻辑
"""

import os
import re
import uuid
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class FileInfo(BaseModel):
    """文件信息模型"""
    file_name: str
    file_path: str
    file_size: int
    upload_date: str
    file_type: str


class FileService:
    """文件服务类"""
    
    def __init__(self, uploads_dir: str = "./uploads"):
        """
        初始化文件服务
        
        Args:
            uploads_dir: 上传目录路径，默认为 "./uploads"
        """
        self.uploads_dir = Path(uploads_dir)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"文件服务初始化，上传目录: {self.uploads_dir.resolve()}")
    
    def _get_date_dir(self, date: Optional[datetime] = None) -> Path:
        """
        获取指定日期的目录路径
        
        Args:
            date: 日期，如果为 None 则使用当前日期
        
        Returns:
            Path: 日期目录路径
        """
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime("%Y-%m-%d")
        date_dir = self.uploads_dir / date_str
        date_dir.mkdir(parents=True, exist_ok=True)
        
        return date_dir
    
    def _generate_unique_filename(self, original_filename: str, date_dir: Path) -> str:
        """
        生成唯一的文件名（如果文件已存在，添加 UUID 前缀）
        
        Args:
            original_filename: 原始文件名
            date_dir: 日期目录
        
        Returns:
            str: 唯一文件名
        """
        # 如果文件不存在，直接返回原文件名
        file_path = date_dir / original_filename
        if not file_path.exists():
            return original_filename
        
        # 如果文件已存在，添加 UUID 前缀
        file_stem = Path(original_filename).stem
        file_ext = Path(original_filename).suffix
        unique_id = str(uuid.uuid4()).replace("-", "")[:8]
        new_filename = f"{unique_id}_{file_stem}{file_ext}"
        
        return new_filename
    
    async def save_file(self, filename: str, content: bytes) -> FileInfo:
        """
        保存文件到按日期组织的目录
        
        Args:
            filename: 文件名
            content: 文件内容（字节）
        
        Returns:
            FileInfo: 文件信息
        """
        try:
            # 获取当前日期的目录
            date_dir = self._get_date_dir()
            
            # 生成唯一文件名
            unique_filename = self._generate_unique_filename(filename, date_dir)
            
            # 保存文件
            file_path = date_dir / unique_filename
            file_path.write_bytes(content)
            
            # 获取文件信息
            file_size = len(content)
            upload_date = datetime.now().strftime("%Y-%m-%d")
            file_type = Path(filename).suffix.lower()
            
            # 构建相对路径（相对于 uploads 目录）
            relative_path = f"{upload_date}/{unique_filename}"
            
            logger.info(f"文件保存成功: {file_path.resolve()}, 大小: {file_size} 字节")
            
            return FileInfo(
                file_name=unique_filename,
                file_path=relative_path,
                file_size=file_size,
                upload_date=upload_date,
                file_type=file_type
            )
        
        except Exception as e:
            logger.error(f"保存文件失败: {str(e)}", exc_info=True)
            raise
    
    async def list_files(
        self,
        date: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[FileInfo]:
        """
        列出文件
        
        Args:
            date: 日期筛选，格式 YYYY-MM-DD，如果为 None 则列出所有文件
            page: 页码，从1开始
            page_size: 每页数量
        
        Returns:
            List[FileInfo]: 文件信息列表
        """
        files = []
        
        try:
            if date:
                # 只查询指定日期的文件
                date_dir = self.uploads_dir / date
                if date_dir.exists() and date_dir.is_dir():
                    files.extend(self._list_files_in_dir(date_dir, date))
            else:
                # 查询所有日期的文件
                for date_dir in sorted(self.uploads_dir.iterdir(), reverse=True):
                    if date_dir.is_dir() and re.match(r"^\d{4}-\d{2}-\d{2}$", date_dir.name):
                        date_str = date_dir.name
                        files.extend(self._list_files_in_dir(date_dir, date_str))
            
            # 按上传日期倒序排序（最新的在前）
            files.sort(key=lambda x: (x.upload_date, x.file_name), reverse=True)
            
            # 分页
            start = (page - 1) * page_size
            end = start + page_size
            files = files[start:end]
            
            logger.info(f"查询到 {len(files)} 个文件（日期: {date}, 页码: {page}）")
            
            return files
        
        except Exception as e:
            logger.error(f"列出文件失败: {str(e)}", exc_info=True)
            raise
    
    def _list_files_in_dir(self, date_dir: Path, date_str: str) -> List[FileInfo]:
        """
        列出指定目录下的所有文件
        
        Args:
            date_dir: 日期目录
            date_str: 日期字符串
        
        Returns:
            List[FileInfo]: 文件信息列表
        """
        files = []
        
        for file_path in date_dir.iterdir():
            if file_path.is_file() and not file_path.name.startswith("."):
                try:
                    file_size = file_path.stat().st_size
                    file_type = file_path.suffix.lower()
                    
                    # 构建相对路径
                    relative_path = f"{date_str}/{file_path.name}"
                    
                    files.append(FileInfo(
                        file_name=file_path.name,
                        file_path=relative_path,
                        file_size=file_size,
                        upload_date=date_str,
                        file_type=file_type
                    ))
                except Exception as e:
                    logger.warning(f"获取文件信息失败: {file_path}, 错误: {str(e)}")
        
        return files
    
    async def list_dates(self) -> List[str]:
        """
        获取所有有文件的日期列表
        
        Returns:
            List[str]: 日期列表（格式: YYYY-MM-DD），按日期倒序
        """
        dates = []
        
        try:
            for date_dir in self.uploads_dir.iterdir():
                if date_dir.is_dir() and re.match(r"^\d{4}-\d{2}-\d{2}$", date_dir.name):
                    # 检查目录下是否有文件
                    has_files = any(
                        f.is_file() and not f.name.startswith(".")
                        for f in date_dir.iterdir()
                    )
                    if has_files:
                        dates.append(date_dir.name)
            
            # 按日期倒序排序
            dates.sort(reverse=True)
            
            logger.info(f"查询到 {len(dates)} 个有文件的日期")
            
            return dates
        
        except Exception as e:
            logger.error(f"列出日期失败: {str(e)}", exc_info=True)
            raise
    
    async def get_file_info(self, file_name: str) -> Optional[FileInfo]:
        """
        获取文件信息（通过文件名查找，会在所有日期目录中搜索）
        
        Args:
            file_name: 文件名（可以是完整文件名或部分文件名）
        
        Returns:
            Optional[FileInfo]: 文件信息，如果未找到返回 None
        """
        try:
            # 在所有日期目录中搜索
            for date_dir in sorted(self.uploads_dir.iterdir(), reverse=True):
                if date_dir.is_dir() and re.match(r"^\d{4}-\d{2}-\d{2}$", date_dir.name):
                    file_path = date_dir / file_name
                    if file_path.exists() and file_path.is_file():
                        file_size = file_path.stat().st_size
                        file_type = file_path.suffix.lower()
                        date_str = date_dir.name
                        relative_path = f"{date_str}/{file_name}"
                        
                        return FileInfo(
                            file_name=file_name,
                            file_path=relative_path,
                            file_size=file_size,
                            upload_date=date_str,
                            file_type=file_type
                        )
            
            logger.warning(f"文件未找到: {file_name}")
            return None
        
        except Exception as e:
            logger.error(f"获取文件信息失败: {str(e)}", exc_info=True)
            raise

