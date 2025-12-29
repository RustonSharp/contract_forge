
from .state import ContractState


def check_compliance(state: ContractState):
    text = state["raw_text"]
    # 简化逻辑：匹配“违约金”和“百分比”
    # 实际开发中此处应调用 LLM 并配合《民法典》第585条数据
    if "30%" in text or "超过" in text:
        risk = {"level": "High", "desc": "违约金比例可能超过法定上限"}
    else:
        risk = {"level": "Low", "desc": "未发现明显合规风险"}
    
    return {"risk_report": risk, "current_step": "compliance_completed"}