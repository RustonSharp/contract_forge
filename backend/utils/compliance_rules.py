"""
合规规则检查模块
实现需求文档中的 3 类合规规则
"""
import re
from typing import Dict, Any, List, Optional


class ComplianceRuleChecker:
    """合规规则检查器"""
    
    def __init__(self):
        self.rules = [
            self._check_penalty_ratio,      # 规则1：违约金比例
            self._check_statute_limitation, # 规则2：诉讼时效
            self._check_dispute_resolution  # 规则3：争议解决方式冲突
        ]
    
    def check_all(self, contract_text: str, structured_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        检查所有合规规则
        
        Args:
            contract_text: 合同文本
            structured_data: 结构化数据（可选）
            
        Returns:
            风险列表
        """
        risks = []
        
        for rule_func in self.rules:
            risk = rule_func(contract_text, structured_data)
            if risk:
                risks.append(risk)
        
        return risks
    
    def _check_penalty_ratio(self, text: str, structured_data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        规则1：违约金比例合规性检查
        
        规则：违约金比例不得超过合同总金额的 30%（依据《民法典》第 585 条）
        """
        # 从文本中提取违约金比例
        penalty_patterns = [
            r'违约金.*?(\d+(?:\.\d+)?)%',  # 违约金XX%
            r'按.*?(\d+(?:\.\d+)?)%.*?支付.*?违约金',  # 按XX%支付违约金
            r'违约金.*?合同.*?(\d+(?:\.\d+)?)%',  # 违约金为合同XX%
        ]
        
        penalty_ratio = None
        for pattern in penalty_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    penalty_ratio = float(match.group(1))
                    break
                except ValueError:
                    continue
        
        # 如果从结构化数据中获取
        if not penalty_ratio and structured_data:
            breach_resp = structured_data.get("breach_responsibility", [])
            for item in breach_resp:
                match = re.search(r'(\d+(?:\.\d+)?)%', str(item))
                if match:
                    penalty_ratio = float(match.group(1))
                    break
        
        if penalty_ratio is None:
            return None
        
        # 判断是否合规
        if penalty_ratio > 30:
            return {
                "rule_name": "违约金比例合规性",
                "rule_id": "rule_penalty_ratio",
                "clause_content": f"违约金比例为 {penalty_ratio}%",
                "risk_level": "High",
                "risk_desc": f"约定的违约金比例（{penalty_ratio}%）超过法定上限 30%，违反《民法典》第 585 条。",
                "suggestion": "建议将违约金比例调整为不超过合同总金额的 30%。",
                "reference": "《民法典》第 585 条",
                "law_article": "当事人可以约定一方违约时应当根据违约情况向对方支付一定数额的违约金。约定的违约金过分高于造成的损失的，人民法院或者仲裁机构可以根据当事人的请求予以适当减少。"
            }
        
        return None
    
    def _check_statute_limitation(self, text: str, structured_data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        规则2：诉讼时效合规性检查
        
        规则：诉讼时效不得短于法定诉讼时效（一般合同纠纷为 3 年，依据《民法典》第 188 条）
        """
        # 从文本中提取诉讼时效
        limitation_patterns = [
            r'诉讼时效.*?(\d+)\s*年',
            r'时效.*?(\d+)\s*年',
            r'(\d+)\s*年.*?诉讼时效',
        ]
        
        limitation_years = None
        for pattern in limitation_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    limitation_years = int(match.group(1))
                    break
                except ValueError:
                    continue
        
        # 如果从结构化数据中获取
        if not limitation_years and structured_data:
            validity = structured_data.get("validity_period", [])
            for item in validity:
                match = re.search(r'(\d+)\s*年', str(item))
                if match:
                    limitation_years = int(match.group(1))
                    break
        
        if limitation_years is None:
            return None
        
        # 判断是否合规（一般合同纠纷为 3 年）
        if limitation_years < 3:
            return {
                "rule_name": "诉讼时效合规性",
                "rule_id": "rule_statute_limitation",
                "clause_content": f"诉讼时效约定为 {limitation_years} 年",
                "risk_level": "High",
                "risk_desc": f"合同约定的诉讼时效（{limitation_years} 年）短于法定诉讼时效（3 年），违反《民法典》第 188 条。",
                "suggestion": "建议按照法律规定将诉讼时效调整为 3 年。",
                "reference": "《民法典》第 188 条",
                "law_article": "向人民法院请求保护民事权利的诉讼时效期间为三年。法律另有规定的，依照其规定。"
            }
        
        return None
    
    def _check_dispute_resolution(self, text: str, structured_data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        规则3：争议解决方式冲突检查
        
        规则：合同不得同时约定"仲裁"和"诉讼"（依据《仲裁法》第 5 条）
        """
        # 检查是否同时包含"仲裁"和"诉讼"
        has_arbitration = bool(re.search(r'仲裁|仲裁委|仲裁委员会', text, re.IGNORECASE))
        has_litigation = bool(re.search(r'诉讼|法院|人民法院|起诉', text, re.IGNORECASE))
        
        # 如果从结构化数据中获取
        if structured_data:
            dispute_resolution = structured_data.get("dispute_resolution", [])
            dispute_text = " ".join(str(item) for item in dispute_resolution)
            if dispute_text:
                has_arbitration = has_arbitration or bool(re.search(r'仲裁', dispute_text, re.IGNORECASE))
                has_litigation = has_litigation or bool(re.search(r'诉讼|法院', dispute_text, re.IGNORECASE))
        
        # 判断是否冲突
        if has_arbitration and has_litigation:
            # 检查是否是"或"的关系（允许）还是同时约定（不允许）
            # 如果同时出现"仲裁"和"诉讼"，且没有明确的"或"、"选择"等词，则视为冲突
            conflict_patterns = [
                r'仲裁.*?诉讼|诉讼.*?仲裁',  # 直接并列
                r'可.*?仲裁.*?可.*?诉讼',    # 可仲裁可诉讼
                r'仲裁.*?或.*?诉讼.*?均可',  # 仲裁或诉讼均可
            ]
            
            for pattern in conflict_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return {
                        "rule_name": "争议解决方式冲突",
                        "rule_id": "rule_dispute_resolution",
                        "clause_content": "同时约定仲裁和诉讼",
                        "risk_level": "High",
                        "risk_desc": "合同同时约定'仲裁'和'诉讼'两种争议解决方式，违反《仲裁法》第 5 条，仲裁约定可能无效。",
                        "suggestion": "建议明确选择仲裁或诉讼，不可同时约定。",
                        "reference": "《仲裁法》第 5 条",
                        "law_article": "当事人达成仲裁协议，一方向人民法院起诉的，人民法院不予受理，但仲裁协议无效的除外。"
                    }
        
        return None
    
    def calculate_overall_score(self, risks: List[Dict[str, Any]]) -> int:
        """
        计算整体合规评分（0-100）
        
        Args:
            risks: 风险列表
            
        Returns:
            合规评分
        """
        if not risks:
            return 100
        
        high_risks = len([r for r in risks if r.get("risk_level") == "High"])
        medium_risks = len([r for r in risks if r.get("risk_level") == "Medium"])
        low_risks = len([r for r in risks if r.get("risk_level") == "Low"])
        
        # 评分规则：高风险扣30分，中风险扣15分，低风险扣5分
        score = 100
        score -= high_risks * 30
        score -= medium_risks * 15
        score -= low_risks * 5
        
        return max(0, min(100, score))


# 全局合规规则检查器实例
compliance_checker = ComplianceRuleChecker()

