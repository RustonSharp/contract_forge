# 工具模块说明

## 📝 日志模块 (logger.py)

### 快速使用

```python
from utils.logger import get_logger

# 创建 logger
logger = get_logger(__name__)

# 使用日志
logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误")
```

### 日志级别

| 级别 | 用途 | 颜色 |
|------|------|------|
| DEBUG | 详细的调试信息 | 青色 |
| INFO | 一般信息 | 绿色 |
| WARNING | 警告信息 | 黄色 |
| ERROR | 错误信息 | 红色 |
| CRITICAL | 严重错误 | 紫色 |

### 日志输出位置

1. **控制台**：实时查看，带颜色
2. **日志文件**：`logs/app_YYYYMMDD.log`（所有日志）
3. **错误日志**：`logs/error_YYYYMMDD.log`（仅错误）

### 高级用法

#### 1. 不同模块使用不同的 logger

```python
from utils.logger import LoggerManager

# API 服务日志
api_logger = LoggerManager.get_api_logger()
api_logger.info("API 请求处理")

# 数据库操作日志
db_logger = LoggerManager.get_db_logger()
db_logger.info("查询成功")

# 工作流执行日志
workflow_logger = LoggerManager.get_workflow_logger()
workflow_logger.debug("执行节点：文档解析")

# 工具执行日志
tool_logger = LoggerManager.get_tool_logger()
tool_logger.info("工具调用成功")
```

#### 2. 自定义配置

```python
from utils.logger import setup_logger

# 自定义配置
logger = setup_logger(
    name="my_module",
    level="DEBUG",          # 日志级别
    log_to_file=True,       # 输出到文件
    log_to_console=True     # 输出到控制台
)
```

#### 3. 记录异常

```python
try:
    # 一些操作
    result = process_contract(file_path)
except Exception as e:
    logger.error(f"处理失败: {e}", exc_info=True)  # exc_info=True 会记录完整堆栈
    raise
```

#### 4. 结构化日志

```python
logger.info(
    "合同处理完成",
    extra={
        "contract_id": "contract_001",
        "duration": 35,
        "risk_level": "low"
    }
)
```

### 日志文件管理

- **自动轮转**：单个文件超过 10MB 时自动创建新文件
- **保留数量**：最多保留 5 个备份文件
- **按日期分割**：每天一个新日志文件
- **自动清理**：可以定期删除旧日志

### 测试日志模块

```bash
python utils/logger.py
```

会看到带颜色的日志输出，并生成日志文件。

### 在实际项目中使用

```python
# 在 API 服务中
from fastapi import FastAPI
from utils.logger import get_logger

logger = get_logger(__name__)
app = FastAPI()

@app.get("/api/test")
def test():
    logger.info("收到测试请求")
    return {"status": "ok"}

# 在工具中
from utils.logger import LoggerManager

tool_logger = LoggerManager.get_tool_logger()

class DocumentParser:
    def parse(self, file_path):
        tool_logger.info(f"开始解析文件: {file_path}")
        try:
            # 解析逻辑
            tool_logger.info("解析成功")
        except Exception as e:
            tool_logger.error(f"解析失败: {e}", exc_info=True)
            raise
```

### 日志最佳实践

1. ✅ **使用合适的级别**
   - DEBUG: 详细的调试信息
   - INFO: 正常的业务流程
   - WARNING: 可能的问题
   - ERROR: 错误但程序可继续
   - CRITICAL: 严重错误，程序无法继续

2. ✅ **记录关键信息**
   ```python
   logger.info(f"处理合同: {contract_id}, 用户: {user_id}")
   ```

3. ✅ **不要记录敏感信息**
   ```python
   # ❌ 错误
   logger.info(f"密码: {password}")
   
   # ✅ 正确
   logger.info(f"用户登录: {username}")
   ```

4. ✅ **异常时记录完整堆栈**
   ```python
   logger.error("处理失败", exc_info=True)
   ```

