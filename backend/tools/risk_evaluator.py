import sys
import os
from typing import Dict, Any, List

# 确保能导入 base
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from base import BaseTool

# 导入合规规则检查器
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.compliance_rules import compliance_checker

class RiskEvaluator(BaseTool):
    name = "RiskEvaluator"
    description = "对比合同条款与法律法规，识别潜在合规风险"

    def run(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        input_data 结构示例:
        {
            "clauses": [{"text": "违约金40%", "type": "违约金"}],
            "referenced_laws": [{"title": "《民法典》第585条", "content": "..."}],
            "raw_text": "合同全文",
            "structured_data": {...}
        }
        """
        raw_text = input_data.get("raw_text", "")
        structured_data = input_data.get("structured_data")
        laws = input_data.get("referenced_laws", [])
        
        if not raw_text:
            return self._format_error("缺少合同文本")

        # 使用合规规则检查器
        compliance_risks = compliance_checker.check_all(raw_text, structured_data)
        
        # 计算合规评分
        overall_score = compliance_checker.calculate_overall_score(compliance_risks)
        
        # 确定整体风险等级
        high_risks = [r for r in compliance_risks if r.get("risk_level") == "High"]
        overall_risk_level = "High" if high_risks else "Medium" if compliance_risks else "Low"
        
        # 转换为标准格式
        detailed_risks = []
        for risk in compliance_risks:
            detailed_risks.append({
                "clause_content": risk.get("clause_content", ""),
                "risk_level": risk.get("risk_level", "Medium"),
                "risk_desc": risk.get("risk_desc", ""),
                "suggestion": risk.get("suggestion", ""),
                "reference": risk.get("reference", "")
            })

        return self._format_success({
            "overall_risk_level": overall_risk_level,
            "detailed_risks": detailed_risks,
            "overall_score": overall_score,
            "audit_summary": f"共检测到 {len(compliance_risks)} 处风险项，其中高风险 {len(high_risks)} 处。合规评分：{overall_score}/100。"
        })

    def _format_success(self, data):
        return {"status": "success", "data": data}

    def _format_error(self, message):
        return {"status": "error", "message": message}

if __name__ == "__main__":
    # 模拟测试
    evaluator = RiskEvaluator()
    test_input = {
        "clauses": [{"text": "违约金为合同总金额的40%", "type": "违约金"}],
        "referenced_laws": [{"title": "《民法典》第585条", "content": "..."}]
    }
    print(evaluator.run(test_input, {}))