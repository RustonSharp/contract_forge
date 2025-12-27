from typing import TypedDict, List, Optional

class RiskItem(TypedDict):
    clause_content: str  # 合同原文
    risk_level: str      # High/Medium/Low
    risk_desc: str       # 风险描述
    suggestion: str      # 修改建议
    reference: str       # 法律依据标题

class ContractState(TypedDict):
    # 基础信息
    file_path: str
    raw_text: Optional[str]
    
    # 提取出的关键特征（用于检索）
    contract_type: str         # 采购/劳动/租赁
    key_clauses: List[dict]    # 提取出的含风险嫌疑的条款
    
    # 检索结果
    referenced_laws: List[dict]
    
    # 最终报告
    risks: List[RiskItem]
    overall_score: int         # 合规分数 0-100
    
    # 流程控制
    current_step: str          # parsing/retrieving/evaluating/completed
    error: Optional[str]