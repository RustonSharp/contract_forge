"""
工具注册机制（类似 Langdock）
支持动态注册和调用工具，无需修改核心流程代码
"""
from typing import Dict, Any, Optional, List, Type
from ..tools.base import BaseTool
import importlib
import os


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._tool_configs: Dict[str, Dict[str, Any]] = {}
        self._fallback_tools: Dict[str, List[str]] = {}  # 主工具 -> 备用工具列表
    
    def register(self, tool: BaseTool, config: Optional[Dict[str, Any]] = None):
        """
        注册工具
        
        Args:
            tool: 工具实例
            config: 工具配置（如超时时间、重试次数等）
        """
        self._tools[tool.name] = tool
        self._tool_configs[tool.name] = config or {}
        print(f"✅ 工具已注册: {tool.name} - {tool.description}")
    
    def register_fallback(self, primary_tool: str, fallback_tools: List[str]):
        """
        注册备用工具
        
        Args:
            primary_tool: 主工具名称
            fallback_tools: 备用工具名称列表
        """
        self._fallback_tools[primary_tool] = fallback_tools
        print(f"✅ 备用工具已注册: {primary_tool} -> {fallback_tools}")
    
    def get(self, tool_name: str) -> Optional[BaseTool]:
        """获取工具实例"""
        return self._tools.get(tool_name)
    
    def get_config(self, tool_name: str) -> Dict[str, Any]:
        """获取工具配置"""
        return self._tool_configs.get(tool_name, {})
    
    def get_fallbacks(self, tool_name: str) -> List[str]:
        """获取备用工具列表"""
        return self._fallback_tools.get(tool_name, [])
    
    def list_tools(self) -> List[str]:
        """列出所有已注册的工具"""
        return list(self._tools.keys())
    
    def run_with_fallback(self, tool_name: str, input_data: Dict[str, Any], 
                         context: Dict[str, Any], max_retries: int = 2) -> Dict[str, Any]:
        """
        运行工具，失败时自动切换到备用工具
        
        Args:
            tool_name: 主工具名称
            input_data: 输入数据
            context: 上下文
            max_retries: 最大重试次数（包括主工具和备用工具）
            
        Returns:
            工具执行结果
        """
        tools_to_try = [tool_name] + self.get_fallbacks(tool_name)
        
        for i, tool_name_to_try in enumerate(tools_to_try):
            if i >= max_retries:
                break
                
            tool = self.get(tool_name_to_try)
            if not tool:
                continue
            
            try:
                result = tool.run(input_data, context)
                if result.get("status") == "success":
                    if i > 0:  # 使用了备用工具
                        print(f"⚠️ 主工具 {tool_name} 失败，已切换到备用工具 {tool_name_to_try}")
                    return result
            except Exception as e:
                print(f"❌ 工具 {tool_name_to_try} 执行失败: {str(e)}")
                continue
        
        # 所有工具都失败
        return {
            "status": "error",
            "message": f"所有工具（{', '.join(tools_to_try)}）执行失败",
            "error_code": "ALL_TOOLS_FAILED"
        }


# 全局工具注册表实例
registry = ToolRegistry()


def register_default_tools():
    """注册默认工具"""
    from ..tools.doc_parser import ContractParser
    from ..tools.ocr_parser import OCRParser
    from ..tools.law_retriever import LawRetriever
    from ..tools.risk_evaluator import RiskEvaluator
    
    # 注册文档解析工具
    parser = ContractParser()
    registry.register(parser, {"timeout": 30, "retry_count": 2})
    
    # 注册 OCR 工具
    ocr = OCRParser()
    registry.register(ocr, {"timeout": 60, "retry_count": 2})
    
    # 注册法规检索工具
    retriever = LawRetriever()
    registry.register(retriever, {"timeout": 30, "retry_count": 2})
    
    # 注册风险评估工具
    evaluator = RiskEvaluator()
    registry.register(evaluator, {"timeout": 60, "retry_count": 1})
    
    # 配置备用工具：文档解析失败时使用 OCR
    registry.register_fallback("ContractParser", ["OCRParser"])
    registry.register_fallback("OCRParser", ["ContractParser"])


# 初始化时注册默认工具
register_default_tools()

