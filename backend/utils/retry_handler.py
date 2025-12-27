"""
重试机制处理器
支持工具调用的自动重试和超时处理
"""
import time
import asyncio
from typing import Dict, Any, Callable, Optional
from functools import wraps


class RetryHandler:
    """重试处理器"""
    
    def __init__(self, max_retries: int = 2, retry_interval: int = 30, timeout: int = 30):
        """
        初始化重试处理器
        
        Args:
            max_retries: 最大重试次数
            retry_interval: 重试间隔（秒）
            timeout: 超时时间（秒）
        """
        self.max_retries = max_retries
        self.retry_interval = retry_interval
        self.timeout = timeout
    
    def should_retry(self, result: Dict[str, Any]) -> bool:
        """
        判断是否应该重试
        
        Args:
            result: 工具执行结果
            
        Returns:
            是否应该重试
        """
        # 工具返回失败状态
        if result.get("status") == "failed" or result.get("status") == "error":
            return True
        
        # 输出 data 为空
        if not result.get("data"):
            return True
        
        return False
    
    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """
        执行函数，失败时自动重试
        
        Args:
            func: 要执行的函数
            *args, **kwargs: 函数参数
            
        Returns:
            执行结果
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # 执行函数（带超时）
                start_time = time.time()
                result = func(*args, **kwargs)
                elapsed_time = time.time() - start_time
                
                # 检查超时
                if elapsed_time > self.timeout:
                    result = {
                        "status": "error",
                        "message": f"执行超时（超过 {self.timeout} 秒）",
                        "error_code": "TIMEOUT"
                    }
                
                # 检查是否需要重试
                if not self.should_retry(result):
                    if attempt > 0:
                        print(f"✅ 重试成功（第 {attempt} 次重试）")
                    return result
                
                last_error = result
                
                # 如果不是最后一次尝试，等待后重试
                if attempt < self.max_retries:
                    print(f"⚠️ 执行失败，{self.retry_interval} 秒后重试（第 {attempt + 1}/{self.max_retries} 次）...")
                    time.sleep(self.retry_interval)
                
            except Exception as e:
                last_error = {
                    "status": "error",
                    "message": str(e),
                    "error_code": "EXCEPTION"
                }
                
                if attempt < self.max_retries:
                    print(f"⚠️ 发生异常，{self.retry_interval} 秒后重试（第 {attempt + 1}/{self.max_retries} 次）...")
                    time.sleep(self.retry_interval)
        
        # 所有重试都失败
        print(f"❌ 重试 {self.max_retries} 次后仍然失败")
        return last_error or {
            "status": "error",
            "message": "执行失败且重试次数已用完",
            "error_code": "MAX_RETRIES_EXCEEDED"
        }


def retry_decorator(max_retries: int = 2, retry_interval: int = 30, timeout: int = 30):
    """
    重试装饰器
    
    Usage:
        @retry_decorator(max_retries=2, retry_interval=30)
        def my_function():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            handler = RetryHandler(max_retries, retry_interval, timeout)
            return handler.execute_with_retry(func, *args, **kwargs)
        return wrapper
    return decorator

