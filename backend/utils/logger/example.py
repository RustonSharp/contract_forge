"""
日志模块使用示例
"""

import asyncio
from backend.utils.logger import get_logger, setup_logging, LoggerConfig, LogLevel


def example_basic():
    """基础使用示例"""
    print("=== 基础日志使用示例 ===\n")
    
    # 获取日志记录器
    logger = get_logger(__name__)
    
    # 不同级别的日志
    logger.debug("这是一条 DEBUG 日志")
    logger.info("这是一条 INFO 日志")
    logger.warning("这是一条 WARNING 日志")
    logger.error("这是一条 ERROR 日志")
    logger.critical("这是一条 CRITICAL 日志")
    
    print()


def example_custom_config():
    """自定义配置示例"""
    print("=== 自定义配置示例 ===\n")
    
    # 创建自定义配置
    config = LoggerConfig(
        level=LogLevel.DEBUG,
        log_dir="./logs",
        enable_file_logging=True,
        enable_console_logging=True,
        enable_colored_output=True,
    )
    
    # 应用配置
    setup_logging(config)
    
    # 使用日志
    logger = get_logger(__name__)
    logger.info("使用自定义配置的日志")
    
    print()


def example_different_modules():
    """不同模块使用日志示例"""
    print("=== 不同模块日志示例 ===\n")
    
    # 不同模块的日志记录器
    api_logger = get_logger("backend.api")
    db_logger = get_logger("backend.database")
    service_logger = get_logger("backend.service")
    
    api_logger.info("API 请求处理中...")
    db_logger.info("数据库查询执行中...")
    service_logger.info("业务逻辑处理中...")
    
    print()


def example_exception_logging():
    """异常日志记录示例"""
    print("=== 异常日志记录示例 ===\n")
    
    logger = get_logger(__name__)
    
    try:
        # 模拟一个错误
        result = 1 / 0
    except Exception as e:
        # 记录异常（包含堆栈跟踪）
        logger.exception("发生异常:")
        # 或者使用 error
        logger.error(f"发生错误: {str(e)}", exc_info=True)
    
    print()


async def example_async_logging():
    """异步函数中的日志记录示例"""
    print("=== 异步日志记录示例 ===\n")
    
    logger = get_logger(__name__)
    
    async def async_task():
        logger.info("异步任务开始")
        await asyncio.sleep(0.1)
        logger.info("异步任务完成")
    
    await async_task()
    print()


if __name__ == "__main__":
    print("=" * 50)
    print("日志模块使用示例")
    print("=" * 50)
    print()
    
    # 运行示例
    example_basic()
    example_different_modules()
    example_exception_logging()
    asyncio.run(example_async_logging())
    
    # 自定义配置示例（取消注释以运行）
    # example_custom_config()

