"""
工具注册表 - 管理所有注册的工具
"""

from typing import Dict, List, Optional
from backend.utils.langdock.tools import BaseTool
from backend.utils.langdock.models import ToolInfo


class ToolRegistry:
    """工具注册表，单例模式"""
    
    _instance: Optional['ToolRegistry'] = None
    _tools: Dict[str, BaseTool] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools = {}
        return cls._instance
    
    def register(self, tool: BaseTool) -> bool:
        """
        注册工具
        
        Args:
            tool: 工具实例
            
        Returns:
            bool: 是否注册成功
        """
        if not isinstance(tool, BaseTool):
            raise ValueError(f"工具必须是 BaseTool 的实例，当前类型: {type(tool)}")
        
        tool_name = tool.name
        if tool_name in self._tools:
            print(f"警告: 工具 '{tool_name}' 已存在，将被覆盖")
        
        self._tools[tool_name] = tool
        print(f"✓ 工具 '{tool_name}' 注册成功")
        return True
    
    def unregister(self, tool_name: str) -> bool:
        """
        注销工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            bool: 是否注销成功
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            print(f"✓ 工具 '{tool_name}' 已注销")
            return True
        return False
    
    def get(self, tool_name: str) -> Optional[BaseTool]:
        """
        获取工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            Optional[BaseTool]: 工具实例，如果不存在则返回 None
        """
        return self._tools.get(tool_name)
    
    def get_all(self) -> Dict[str, BaseTool]:
        """
        获取所有已注册的工具
        
        Returns:
            Dict[str, BaseTool]: 所有工具的字典
        """
        return self._tools.copy()
    
    def list_tools(self) -> List[ToolInfo]:
        """
        列出所有工具的信息
        
        Returns:
            List[ToolInfo]: 工具信息列表
        """
        return [tool.info for tool in self._tools.values()]
    
    def list_tool_names(self) -> List[str]:
        """
        列出所有工具名称
        
        Returns:
            List[str]: 工具名称列表
        """
        return list(self._tools.keys())
    
    def exists(self, tool_name: str) -> bool:
        """
        检查工具是否存在
        
        Args:
            tool_name: 工具名称
            
        Returns:
            bool: 是否存在
        """
        return tool_name in self._tools
    
    def clear(self):
        """清空所有注册的工具"""
        self._tools.clear()
        print("✓ 所有工具已清空")
    
    def count(self) -> int:
        """
        获取已注册工具的数量
        
        Returns:
            int: 工具数量
        """
        return len(self._tools)


# 全局注册表实例
_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """
    获取全局工具注册表实例
    
    Returns:
        ToolRegistry: 工具注册表实例
    """
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


if __name__ == "__main__":
    # 导入并初始化工具
    from backend.utils.langdock.initialize import initialize_default_tools
    
    print("初始化工具...")
    registry = initialize_default_tools()
    
    print(f"\n已注册的工具数量: {registry.count()}")
    print(f"工具列表: {registry.list_tool_names()}")
    
    # 显示工具详情
    print("\n工具详情:")
    for tool_info in registry.list_tools():
        print(f"\n- {tool_info.display_name} ({tool_info.name})")
        print(f"  描述: {tool_info.description}")
        print(f"  分类: {tool_info.category}")
        print(f"  参数: {[p.name for p in tool_info.parameters]}")