"""
日志模块 - 统一的日志配置和管理
使用 Python logging 标准库
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
import sys

# 日志目录
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# 日志格式
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 颜色代码（用于控制台输出）
COLORS = {
    'DEBUG': '\033[36m',    # 青色
    'INFO': '\033[32m',     # 绿色
    'WARNING': '\033[33m',  # 黄色
    'ERROR': '\033[31m',    # 红色
    'CRITICAL': '\033[35m', # 紫色
    'RESET': '\033[0m'      # 重置
}


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器（仅用于控制台）"""
    
    def format(self, record):
        # 添加颜色
        levelname = record.levelname
        if levelname in COLORS:
            record.levelname = f"{COLORS[levelname]}{levelname}{COLORS['RESET']}"
        
        return super().format(record)


def setup_logger(
    name: str,
    level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True
) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志名称（通常使用模块名 __name__）
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: 是否输出到文件
        log_to_console: 是否输出到控制台
    
    Returns:
        配置好的 Logger 对象
    """
    # 创建 logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    # 1. 控制台 Handler（带颜色）
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = ColoredFormatter(LOG_FORMAT, DATE_FORMAT)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # 2. 文件 Handler（所有日志）
    if log_to_file:
        # 按日期命名日志文件
        log_file = LOG_DIR / f"app_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # 3. 错误日志单独记录
    if log_to_file:
        error_log_file = LOG_DIR / f"error_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
            DATE_FORMAT
        )
        error_handler.setFormatter(error_formatter)
        logger.addHandler(error_handler)
    
    return logger


# 预定义的 logger
def get_logger(name: str = "contract_forge") -> logging.Logger:
    """
    获取日志记录器（简化版）
    
    Usage:
        from utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("这是一条日志")
    """
    return setup_logger(name)


# 用于特定模块的 logger
class LoggerManager:
    """日志管理器"""
    
    @staticmethod
    def get_api_logger():
        """API 服务日志"""
        return setup_logger("api", level="DEBUG")
    
    @staticmethod
    def get_db_logger():
        """数据库操作日志"""
        return setup_logger("database", level="INFO")
    
    @staticmethod
    def get_workflow_logger():
        """工作流执行日志"""
        return setup_logger("workflow", level="DEBUG")
    
    @staticmethod
    def get_tool_logger():
        """工具执行日志"""
        return setup_logger("tools", level="INFO")


# ============================================
# 使用示例（测试）
# ============================================
if __name__ == "__main__":
    # 创建日志
    logger = get_logger("test")
    
    print("\n🧪 日志模块测试\n")
    print("=" * 70)
    
    # 测试不同级别的日志
    logger.debug("这是 DEBUG 级别日志 - 调试信息")
    logger.info("这是 INFO 级别日志 - 一般信息")
    logger.warning("这是 WARNING 级别日志 - 警告信息")
    logger.error("这是 ERROR 级别日志 - 错误信息")
    logger.critical("这是 CRITICAL 级别日志 - 严重错误")
    
    print("\n" + "=" * 70)
    print("\n✅ 日志已同时输出到：")
    print(f"  1. 控制台（带颜色）")
    date_str = datetime.now().strftime('%Y%m%d')
    print(f"  2. 文件: {LOG_DIR / f'app_{date_str}.log'}")
    print(f"  3. 错误日志: {LOG_DIR / f'error_{date_str}.log'}")
    
    # 测试不同模块的日志
    print("\n" + "=" * 70)
    print("测试不同模块的日志：")
    print("=" * 70 + "\n")
    
    api_logger = LoggerManager.get_api_logger()
    api_logger.info("API 服务启动")
    
    db_logger = LoggerManager.get_db_logger()
    db_logger.info("数据库连接成功")
    
    workflow_logger = LoggerManager.get_workflow_logger()
    workflow_logger.debug("工作流开始执行")
    
    tool_logger = LoggerManager.get_tool_logger()
    tool_logger.info("工具调用成功")
    
    print("\n✨ 日志模块测试完成！\n")

