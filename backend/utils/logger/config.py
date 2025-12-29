"""
日志配置模块
"""

import os
from pathlib import Path
from typing import Optional
from enum import Enum
from dotenv import load_dotenv
from pydantic import BaseModel, Field


def find_project_root() -> Path:
    """查找项目根目录"""
    current = Path(__file__).resolve()
    for _ in range(5):
        if (current / ".env").exists() or (current / ".git").exists() or (current / "requirements.txt").exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return Path.cwd()


# 加载 .env 文件
project_root = find_project_root()
load_dotenv(dotenv_path=project_root / ".env")


class LogLevel(str, Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LoggerConfig(BaseModel):
    """日志配置"""
    level: LogLevel = Field(
        default=LogLevel.INFO,
        description="日志级别"
    )
    log_dir: str = Field(
        default="./logs",
        description="日志文件目录"
    )
    log_file: Optional[str] = Field(
        default=None,
        description="日志文件名（如果为 None，则使用默认命名）"
    )
    enable_file_logging: bool = Field(
        default=True,
        description="是否启用文件日志"
    )
    enable_console_logging: bool = Field(
        default=True,
        description="是否启用控制台日志"
    )
    enable_colored_output: bool = Field(
        default=True,
        description="是否启用彩色输出（仅控制台）"
    )
    max_bytes: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="单个日志文件最大大小（字节）"
    )
    backup_count: int = Field(
        default=5,
        description="保留的备份文件数量"
    )
    format_string: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式字符串"
    )
    date_format: str = Field(
        default="%Y-%m-%d %H:%M:%S",
        description="日期时间格式"
    )

    @classmethod
    def from_env(cls) -> "LoggerConfig":
        """
        从环境变量加载配置
        
        环境变量：
        - LOG_LEVEL: 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)，默认 INFO
        - LOG_DIR: 日志文件目录，默认 ./logs
        - LOG_FILE: 日志文件名（可选）
        - LOG_ENABLE_FILE: 是否启用文件日志 (true/false)，默认 true
        - LOG_ENABLE_CONSOLE: 是否启用控制台日志 (true/false)，默认 true
        - LOG_ENABLE_COLORED: 是否启用彩色输出 (true/false)，默认 true
        - LOG_MAX_BYTES: 单个日志文件最大大小（字节），默认 10485760 (10MB)
        - LOG_BACKUP_COUNT: 保留的备份文件数量，默认 5
        """
        # 解析日志级别
        level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        try:
            level = LogLevel(level_str)
        except ValueError:
            level = LogLevel.INFO
        
        # 解析布尔值
        def parse_bool(value: str, default: bool = True) -> bool:
            if value is None:
                return default
            return value.lower() in ("true", "1", "yes", "on")
        
        log_dir = os.getenv("LOG_DIR", "./logs")
        log_file = os.getenv("LOG_FILE")
        enable_file = parse_bool(os.getenv("LOG_ENABLE_FILE"), True)
        enable_console = parse_bool(os.getenv("LOG_ENABLE_CONSOLE"), True)
        enable_colored = parse_bool(os.getenv("LOG_ENABLE_COLORED"), True)
        
        max_bytes = int(os.getenv("LOG_MAX_BYTES", str(10 * 1024 * 1024)))
        backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))
        
        return cls(
            level=level,
            log_dir=log_dir,
            log_file=log_file,
            enable_file_logging=enable_file,
            enable_console_logging=enable_console,
            enable_colored_output=enable_colored,
            max_bytes=max_bytes,
            backup_count=backup_count,
        )


# 全局配置实例
_config: Optional[LoggerConfig] = None


def get_logger_config() -> LoggerConfig:
    """
    获取日志配置（单例模式）
    
    Returns:
        LoggerConfig: 日志配置对象
    """
    global _config
    if _config is None:
        _config = LoggerConfig.from_env()
    return _config

