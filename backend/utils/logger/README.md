# 日志模块使用说明

## 概述

`backend/utils/logger` 模块提供了统一的日志记录功能，支持文件和控制台输出，支持日志轮转和彩色输出。

## 主要特性

- ✅ 支持文件日志和控制台日志
- ✅ 日志轮转（按文件大小）
- ✅ 彩色输出（控制台）
- ✅ 可配置的日志级别
- ✅ 支持从环境变量配置
- ✅ 自动创建日志目录
- ✅ 统一的日志格式

## 快速开始

### 基础使用

```python
from backend.utils.logger import get_logger

# 获取日志记录器
logger = get_logger(__name__)

# 记录日志
logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误")
```

### 在模块中使用

```python
# 在任何模块中
from backend.utils.logger import get_logger

logger = get_logger(__name__)

def my_function():
    logger.info("函数执行中...")
    try:
        # 业务逻辑
        pass
    except Exception as e:
        logger.exception("发生异常:")
```

## 配置

### 环境变量配置

在 `.env` 文件中配置：

```env
# 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
LOG_LEVEL=INFO

# 日志文件目录
LOG_DIR=./logs

# 日志文件名（可选，默认 app.log）
LOG_FILE=app.log

# 是否启用文件日志 (true/false)
LOG_ENABLE_FILE=true

# 是否启用控制台日志 (true/false)
LOG_ENABLE_CONSOLE=true

# 是否启用彩色输出 (true/false)
LOG_ENABLE_COLORED=true

# 单个日志文件最大大小（字节，默认 10MB）
LOG_MAX_BYTES=10485760

# 保留的备份文件数量（默认 5）
LOG_BACKUP_COUNT=5
```

### 代码配置

```python
from backend.utils.logger import setup_logging, LoggerConfig, LogLevel

# 创建自定义配置
config = LoggerConfig(
    level=LogLevel.DEBUG,
    log_dir="./logs",
    enable_file_logging=True,
    enable_console_logging=True,
    enable_colored_output=True,
    max_bytes=10 * 1024 * 1024,  # 10MB
    backup_count=5,
)

# 应用配置
setup_logging(config)
```

## 日志级别

- **DEBUG**: 详细的调试信息
- **INFO**: 一般信息（默认）
- **WARNING**: 警告信息
- **ERROR**: 错误信息
- **CRITICAL**: 严重错误

## 日志格式

默认格式：
```
2024-01-01 12:00:00 - backend.api - INFO - 请求处理完成
```

格式包含：
- 时间戳
- 模块名称
- 日志级别
- 日志消息

## 日志文件

- 日志文件保存在 `./logs/` 目录（可通过 `LOG_DIR` 配置）
- 默认文件名：`app.log`
- 当日志文件达到最大大小时，会自动轮转
- 保留指定数量的备份文件（默认 5 个）

## 异常记录

```python
logger = get_logger(__name__)

try:
    # 可能出错的代码
    result = 1 / 0
except Exception as e:
    # 方式1: 使用 exception（自动包含堆栈跟踪）
    logger.exception("发生异常:")
    
    # 方式2: 使用 error + exc_info
    logger.error(f"发生错误: {str(e)}", exc_info=True)
```

## 在 FastAPI 中使用

```python
from fastapi import FastAPI
from backend.utils.logger import get_logger, setup_logging

# 初始化日志
setup_logging()
logger = get_logger(__name__)

app = FastAPI()

@app.get("/")
async def root():
    logger.info("处理根路径请求")
    return {"message": "Hello World"}
```

## 示例

查看 `backend/utils/logger/example.py` 获取更多使用示例。

## 注意事项

1. **日志目录**: 如果日志目录不存在，会自动创建
2. **日志轮转**: 当日志文件达到 `max_bytes` 时，会自动创建新文件
3. **彩色输出**: 仅在控制台输出时使用，文件日志不使用颜色
4. **性能**: 日志记录是异步安全的，可以在异步函数中使用
5. **日志文件位置**: 日志文件默认保存在项目根目录的 `logs/` 文件夹中

