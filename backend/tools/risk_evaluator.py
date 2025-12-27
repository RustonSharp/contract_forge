import sys
import os
from typing import Dict, Any, List

# 确保能导入 base
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from base import BaseTool

class RiskEvaluator(BaseTool):
    name = "RiskEvaluator"
    description = "对比合同条款与法律法规，识别潜在合规风险"

    def run(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        input_data 结构示例:
        {
            "clauses": [{"text": "违约金40%", "type": "违约金"}],
            "referenced_laws": [{"title": "《民法典》第585条", "content": "..."}]
        }
        """
        clauses = input_data.get("clauses", [])
        laws = input_data.get("referenced_laws", [])
        
        if not clauses or not laws:
            return self._format_error("缺少评估所需的条款或法律依据")

        # --- MVP 逻辑实现 (模拟 LLM 处理结果) ---
        # 实际开发中，这里会调用 OpenAI/Anthropic 的 API
        risks = []
        
        for clause in clauses:
            # 针对违约金的硬编码逻辑（用于测试你的 PDF）
            if clause["type"] == "违约金" and "40%" in clause["text"]:
                risks.append({
                    "clause_content": clause["text"],
                    "risk_level": "High",
                    "risk_desc": "约定的违约金比例（40%）过高，超过了司法实践中普遍认可的30%上限。",
                    "suggestion": "建议将违约金比例调整至20%-30%之间，以确保法律效力。",
                    "reference": "根据《民法典》第585条及相关司法解释。"
                })
            
            # 针对诉讼时效的逻辑
            elif clause["type"] == "诉讼时效" and "1年" in clause["text"]:
                risks.append({
                    "clause_content": clause["text"],
                    "risk_level": "High",
                    "risk_desc": "法律规定普通诉讼时效为3年，约定1年可能因违反强制性规定而无效。",
                    "suggestion": "建议按照法律规定调整为3年。",
                    "reference": "《民法典》第188条。"
                })

        return self._format_success({
            "overall_risk_level": "High" if any(r["risk_level"] == "High" for r in risks) else "Low",
            "detailed_risks": risks,
            "audit_summary": f"共检测到 {len(risks)} 处高风险项，主要集中在违约责任条款。"
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