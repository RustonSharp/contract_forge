"""
上下文管理器
实现上下文过期清理机制（流程结束后 24 小时自动删除中间数据）
"""
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import threading


class ContextManager:
    """上下文管理器"""
    
    def __init__(self, expiration_hours: int = 24):
        """
        初始化上下文管理器
        
        Args:
            expiration_hours: 过期时间（小时），默认 24 小时
        """
        self.expiration_hours = expiration_hours
        self.contexts: Dict[str, Dict[str, Any]] = {}
        self.context_timestamps: Dict[str, datetime] = {}
        self.lock = threading.Lock()
        
        # 启动清理线程
        self._start_cleanup_thread()
    
    def save_context(self, task_id: str, context: Dict[str, Any]):
        """
        保存上下文
        
        Args:
            task_id: 任务 ID
            context: 上下文数据
        """
        with self.lock:
            self.contexts[task_id] = context
            self.context_timestamps[task_id] = datetime.now()
            print(f"✅ 上下文已保存: {task_id}")
    
    def get_context(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取上下文
        
        Args:
            task_id: 任务 ID
            
        Returns:
            上下文数据，如果不存在或已过期则返回 None
        """
        with self.lock:
            if task_id not in self.contexts:
                return None
            
            # 检查是否过期
            if self._is_expired(task_id):
                self._remove_context(task_id)
                return None
            
            return self.contexts[task_id]
    
    def remove_context(self, task_id: str):
        """
        手动删除上下文
        
        Args:
            task_id: 任务 ID
        """
        with self.lock:
            self._remove_context(task_id)
    
    def _remove_context(self, task_id: str):
        """内部方法：删除上下文"""
        if task_id in self.contexts:
            del self.contexts[task_id]
        if task_id in self.context_timestamps:
            del self.context_timestamps[task_id]
        print(f"🗑️ 上下文已删除: {task_id}")
    
    def _is_expired(self, task_id: str) -> bool:
        """
        检查上下文是否过期
        
        Args:
            task_id: 任务 ID
            
        Returns:
            是否过期
        """
        if task_id not in self.context_timestamps:
            return True
        
        timestamp = self.context_timestamps[task_id]
        expiration_time = timestamp + timedelta(hours=self.expiration_hours)
        
        return datetime.now() > expiration_time
    
    def _start_cleanup_thread(self):
        """启动清理线程"""
        def cleanup_loop():
            while True:
                try:
                    time.sleep(3600)  # 每小时检查一次
                    self._cleanup_expired()
                except Exception as e:
                    print(f"清理线程错误: {str(e)}")
        
        thread = threading.Thread(target=cleanup_loop, daemon=True)
        thread.start()
        print("✅ 上下文清理线程已启动")
    
    def _cleanup_expired(self):
        """清理过期的上下文"""
        with self.lock:
            expired_tasks = [
                task_id for task_id in self.context_timestamps.keys()
                if self._is_expired(task_id)
            ]
            
            for task_id in expired_tasks:
                self._remove_context(task_id)
            
            if expired_tasks:
                print(f"🧹 已清理 {len(expired_tasks)} 个过期上下文")
    
    def mark_completed(self, task_id: str):
        """
        标记任务完成（开始计时过期）
        
        Args:
            task_id: 任务 ID
        """
        with self.lock:
            if task_id in self.contexts:
                # 更新时间戳，开始计时过期
                self.context_timestamps[task_id] = datetime.now()
                print(f"✅ 任务已完成，上下文将在 {self.expiration_hours} 小时后过期: {task_id}")


# 全局上下文管理器实例
context_manager = ContextManager(expiration_hours=24)

