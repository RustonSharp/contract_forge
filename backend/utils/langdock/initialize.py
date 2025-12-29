"""
工具初始化模块 - 注册默认工具
"""

from backend.utils.langdock.registry import get_registry
from backend.utils.langdock.core_tools import (
    DocumentParserTool,
    OCRParserTool,
    RegulationSearchTool,
    RiskAssessmentTool,
)
from backend.utils.langdock.tools import ContractAnalysisTool


def initialize_default_tools():
    """
    初始化并注册默认工具
    """
    registry = get_registry()
    
    # 注册核心工具
    # 1. 文档解析工具
    doc_parser = DocumentParserTool()
    registry.register(doc_parser)
    
    # 2. OCR 解析工具
    ocr_parser = OCRParserTool()
    registry.register(ocr_parser)
    
    # 3. 法规检索工具
    regulation_search = RegulationSearchTool()
    registry.register(regulation_search)
    
    # 4. 风险评估工具
    risk_assessment = RiskAssessmentTool()
    registry.register(risk_assessment)
    
    # 5. 合同分析工具（可选）
    contract_analysis = ContractAnalysisTool()
    registry.register(contract_analysis)
    
    print(f"✓ 已注册 {registry.count()} 个工具:")
    for tool_name in registry.list_tool_names():
        tool = registry.get(tool_name)
        print(f"  - {tool.info.display_name} ({tool_name})")
    
    return registry


# 自动初始化（可选）
# initialize_default_tools()

