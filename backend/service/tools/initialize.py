"""
工具初始化模块 - 注册默认工具
"""

from backend.service.tools.registry import get_registry
from backend.service.tools.core_tools import (
    DocumentParserTool,
    OCRParserTool,
    ImageToPdfTool,
    RegulationSearchTool,
    RiskAssessmentTool,
    EnterpriseInfoQueryTool,
    SigningSubjectComplianceTool,
    CoreClausesCompletenessTool,
    LegalConflictComplianceTool,
)
from backend.service.tools.n8n_tools import N8NWorkflowTriggerTool
from backend.service.tools.base import ContractAnalysisTool


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
    
    # 3. 图片转 PDF 工具
    image_to_pdf = ImageToPdfTool()
    registry.register(image_to_pdf)
    
    # 4. 法规检索工具
    regulation_search = RegulationSearchTool()
    registry.register(regulation_search)
    
    # 5. 风险评估工具
    risk_assessment = RiskAssessmentTool()
    registry.register(risk_assessment)
    
    # 6. 合同分析工具（可选）
    contract_analysis = ContractAnalysisTool()
    registry.register(contract_analysis)
    
    # 注册合规工具
    # 7. 企业信息查询工具
    enterprise_query = EnterpriseInfoQueryTool()
    registry.register(enterprise_query)
    
    # 8. 签署主体合规校验工具
    signing_subject = SigningSubjectComplianceTool()
    registry.register(signing_subject)
    
    # 9. 核心条款完整性校验工具
    core_clauses = CoreClausesCompletenessTool()
    registry.register(core_clauses)
    
    # 10. 法规冲突校验工具
    legal_conflict = LegalConflictComplianceTool()
    registry.register(legal_conflict)
    
    # 11. N8N 工作流触发工具
    n8n_trigger = N8NWorkflowTriggerTool()
    registry.register(n8n_trigger)
    
    print(f"✓ 已注册 {registry.count()} 个工具:")
    for tool_name in registry.list_tool_names():
        tool = registry.get(tool_name)
        print(f"  - {tool.info.display_name} ({tool_name})")
    
    return registry


# 自动初始化（可选）
# initialize_default_tools()

