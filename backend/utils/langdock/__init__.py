"""
Langdock 工具注册模块

用于注册和管理大模型可调用的工具，如风险评估工具等。
"""

from backend.utils.langdock.registry import ToolRegistry, get_registry
from backend.utils.langdock.tools import BaseTool, ToolResult, ContractAnalysisTool
from backend.utils.langdock.core_tools import (
    DocumentParserTool,
    OCRParserTool,
    RegulationSearchTool,
    RiskAssessmentTool,
)
from backend.utils.langdock.models import ToolInfo, ToolParameter

__all__ = [
    "ToolRegistry",
    "get_registry",
    "BaseTool",
    "ToolResult",
    "ToolInfo",
    "ToolParameter",
    "DocumentParserTool",
    "OCRParserTool",
    "RegulationSearchTool",
    "RiskAssessmentTool",
    "ContractAnalysisTool",
]
