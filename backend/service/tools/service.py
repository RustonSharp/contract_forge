"""
工具服务封装
提供工具相关的业务逻辑服务
"""

from typing import List, Dict, Any, Optional
from backend.service.tools.registry import get_registry
from backend.service.tools.models import ToolInfo, ToolResult
from backend.service.tools.base import BaseTool
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ToolService:
    """工具服务类，封装工具相关的业务逻辑"""
    
    def __init__(self):
        """初始化工具服务"""
        self.registry = get_registry()
    
    def list_tools(self) -> List[ToolInfo]:
        """
        获取所有已注册的工具列表
        
        Returns:
            List[ToolInfo]: 工具信息列表
        """
        return self.registry.list_tools()
    
    def get_tool_info(self, tool_name: str) -> Optional[ToolInfo]:
        """
        获取指定工具的信息
        
        Args:
            tool_name: 工具名称
            
        Returns:
            Optional[ToolInfo]: 工具信息，如果不存在则返回 None
        """
        tool = self.registry.get(tool_name)
        if tool:
            return tool.info
        return None
    
    def list_tool_names(self) -> List[str]:
        """
        获取所有工具名称列表
        
        Returns:
            List[str]: 工具名称列表
        """
        return self.registry.list_tool_names()
    
    async def execute_tool(self, tool_name: str, **parameters) -> ToolResult:
        """
        执行指定的工具
        
        Args:
            tool_name: 工具名称
            **parameters: 工具参数
            
        Returns:
            ToolResult: 执行结果
            
        Raises:
            ValueError: 如果工具不存在
        """
        tool = self.registry.get(tool_name)
        
        if not tool:
            available_tools = self.registry.list_tool_names()
            raise ValueError(
                f"工具 '{tool_name}' 未找到。可用工具: {available_tools}"
            )
        
        logger.info(f"执行工具: {tool_name}, 参数: {parameters}")
        
        # 执行工具
        result = await tool.execute(**parameters)
        
        if result.success:
            logger.info(
                f"工具 {tool_name} 执行成功，"
                f"耗时: {result.execution_time:.3f}秒" if result.execution_time else ""
            )
        else:
            logger.warning(f"工具 {tool_name} 执行失败: {result.error}")
        
        return result
    
    def register_tool(self, tool: BaseTool) -> bool:
        """
        注册工具
        
        Args:
            tool: 工具实例
            
        Returns:
            bool: 是否注册成功
        """
        return self.registry.register(tool)
    
    def unregister_tool(self, tool_name: str) -> bool:
        """
        注销工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            bool: 是否注销成功
        """
        return self.registry.unregister(tool_name)
    
    def tool_exists(self, tool_name: str) -> bool:
        """
        检查工具是否存在
        
        Args:
            tool_name: 工具名称
            
        Returns:
            bool: 是否存在
        """
        return self.registry.exists(tool_name)

