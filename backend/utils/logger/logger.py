"""
日志记录器实现
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler

from backend.utils.logger.config import LoggerConfig, get_logger_config, LogLevel


# 全局日志配置
_logger_config: Optional[LoggerConfig] = None
_loggers: dict[str, logging.Logger] = {}


def setup_logging(config: Optional[LoggerConfig] = None) -> None:
    """
    设置日志配置
    
    Args:
        config: 日志配置，如果为 None 则从环境变量加载
    """
    global _logger_config
    _logger_config = config or get_logger_config()
    
    # 确保日志目录存在
    if _logger_config.enable_file_logging:
        log_dir = Path(_logger_config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(_logger_config.level.value)
    
    # 清除现有的处理器
    root_logger.handlers.clear()
    
    # 添加控制台处理器
    if _logger_config.enable_console_logging:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(_logger_config.level.value)
        
        if _logger_config.enable_colored_output:
            from backend.utils.logger.formatter import ColoredFormatter
            formatter = ColoredFormatter(
                fmt=_logger_config.format_string,
                datefmt=_logger_config.date_format,
                use_colors=True
            )
        else:
            formatter = logging.Formatter(
                fmt=_logger_config.format_string,
                datefmt=_logger_config.date_format
            )
        
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # 添加文件处理器
    if _logger_config.enable_file_logging:
        log_dir = Path(_logger_config.log_dir)
        log_file = _logger_config.log_file or "app.log"
        log_path = log_dir / log_file
        
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=_logger_config.max_bytes,
            backupCount=_logger_config.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(_logger_config.level.value)
        
        # 文件日志不使用颜色
        formatter = logging.Formatter(
            fmt=_logger_config.format_string,
            datefmt=_logger_config.date_format
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称，如果为 None 则使用调用模块的名称
    
    Returns:
        logging.Logger: 日志记录器实例
    """
    # 如果没有设置日志配置，先设置
    global _logger_config
    if _logger_config is None:
        setup_logging()
    
    # 确定日志记录器名称
    if name is None:
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            frame = frame.f_back
            module = frame.f_globals.get('__name__', 'root')
            name = module
    
    # 如果已存在，直接返回
    if name in _loggers:
        return _loggers[name]
    
    # 创建新的日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(_logger_config.level.value)
    
    # 避免重复添加处理器（处理器已添加到根日志记录器）
    logger.propagate = True
    
    _loggers[name] = logger
    return logger


# 初始化日志配置（如果环境变量已设置）
def _auto_setup():
    """自动设置日志配置"""
    try:
        setup_logging()
    except Exception:
        # 如果自动设置失败，使用默认配置
        pass


# 延迟初始化（在首次导入时自动设置）
_auto_setup()

