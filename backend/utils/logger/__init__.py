"""
日志模块

提供统一的日志记录功能，支持文件和控制台输出
"""

from backend.utils.logger.logger import get_logger, setup_logging, LoggerConfig
from backend.utils.logger.formatter import ColoredFormatter

__all__ = [
    "get_logger",
    "setup_logging",
    "LoggerConfig",
    "ColoredFormatter",
]

