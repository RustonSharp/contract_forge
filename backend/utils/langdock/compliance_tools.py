"""
合规规则检查工具
实现三个核心合规规则：
1. 合同签署主体合规校验
2. 合同核心条款完整性校验
3. 合同条款与现行法规冲突校验
"""

import time
import re
from typing import Any, Dict, List, Optional
from backend.utils.langdock.tools import BaseTool
from backend.utils.langdock.models import ToolInfo, ToolParameter, ToolResult


class EnterpriseInfoQueryTool(BaseTool):
    """企业信息查询工具（Mock）"""
    
    def get_info(self) -> ToolInfo:
        return ToolInfo(
            name="enterprise_info_query",
            display_name="企业信息查询工具",
            description="查询企业信息（Mock），验证企业主体状态",
            parameters=[
                ToolParameter(
                    name="enterprise_name",
                    type="string",
                    description="企业名称",
                    required=True
                ),
                ToolParameter(
                    name="credit_code",
                    type="string",
                    description="统一社会信用代码（可选，用于精确查询）",
                    required=False
                )
            ],
            category="query",
            version="1.0.0"
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行企业信息查询（Mock）"""
        start_time = time.time()
        
        try:
            is_valid, error_msg = self.validate_parameters(**kwargs)
            if not is_valid:
                return ToolResult(
                    success=False,
                    error=error_msg,
                    execution_time=time.time() - start_time
                )
            
            enterprise_name = kwargs.get("enterprise_name")
            credit_code = kwargs.get("credit_code")
            
            # Mock 企业信息查询
            # 实际应该调用国家企业信用信息公示系统 API
            mock_enterprises = {
                "XX有限公司": {
                    "name": "XX有限公司",
                    "credit_code": "91110000MA01234567",
                    "status": "存续",
                    "legal_representative": "张三",
                    "registered_capital": "1000万元"
                },
                "YY科技公司": {
                    "name": "YY科技公司",
                    "credit_code": "91110000MA09876543",
                    "status": "存续",
                    "legal_representative": "李四",
                    "registered_capital": "500万元"
                }
            }
            
            # 查找企业信息
            enterprise_info = None
            if credit_code:
                # 按信用代码查找
                for ent in mock_enterprises.values():
                    if ent.get("credit_code") == credit_code:
                        enterprise_info = ent
                        break
            else:
                # 按名称查找
                enterprise_info = mock_enterprises.get(enterprise_name)
            
            if not enterprise_info:
                # 模拟查询失败的情况
                enterprise_info = {
                    "name": enterprise_name,
                    "status": "未查询到",
                    "message": "企业信息未找到或已注销"
                }
            
            result_data = {
                "enterprise_name": enterprise_name,
                "enterprise_info": enterprise_info,
                "status": "completed"
            }
            
            return ToolResult(
                success=True,
                data=result_data,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"执行企业信息查询时发生错误: {str(e)}",
                execution_time=time.time() - start_time
            )


class SigningSubjectComplianceTool(BaseTool):
    """规则1：合同签署主体合规校验"""
    
    def get_info(self) -> ToolInfo:
        return ToolInfo(
            name="signing_subject_compliance",
            display_name="签署主体合规校验",
            description="校验合同签署方是否具备合法签约资格，避免无权签署风险",
            parameters=[
                ToolParameter(
                    name="contract_text",
                    type="string",
                    description="合同文本内容",
                    required=True
                )
            ],
            category="compliance",
            version="1.0.0"
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行签署主体合规校验"""
        start_time = time.time()
        
        try:
            is_valid, error_msg = self.validate_parameters(**kwargs)
            if not is_valid:
                return ToolResult(
                    success=False,
                    error=error_msg,
                    execution_time=time.time() - start_time
                )
            
            contract_text = kwargs.get("contract_text", "")
            
            # 提取签署方信息
            parties = self._extract_parties(contract_text)
            
            if not parties:
                # 未提取到任何签署方信息
                return ToolResult(
                    success=True,
                    data={
                        "rule_name": "签署主体合规校验",
                        "compliance_status": "违规",
                        "risk_level": "中风险",
                        "violations": [
                            {
                                "type": "缺失签署方信息",
                                "description": "未从合同文本中提取到任何签署方信息",
                                "suggestion": "请补充签署方合法资质证明（如营业执照复印件、身份证复印件）"
                            }
                        ],
                        "parties": [],
                        "next_action": "法务人工复核",
                        "notification": "需要邮件通知"
                    },
                    execution_time=time.time() - start_time
                )
            
            # 校验每个签署方
            violations = []
            valid_parties = []
            
            for party in parties:
                party_type = party.get("type")  # "enterprise" 或 "individual"
                party_name = party.get("name")
                party_info = party.get("info", {})
                
                if party_type == "enterprise":
                    # 企业主体校验
                    credit_code = party_info.get("credit_code")
                    business_license = party_info.get("business_license")
                    
                    if not credit_code and not business_license:
                        violations.append({
                            "type": "企业主体缺少资质证明",
                            "party": party_name,
                            "description": f"企业主体 '{party_name}' 缺少统一社会信用代码或营业执照注册号",
                            "suggestion": "请补充营业执照复印件，确保包含统一社会信用代码（18位）或营业执照注册号（15位）"
                        })
                        continue
                    
                    # 验证企业状态（调用企业信息查询工具）
                    enterprise_tool = None
                    try:
                        from backend.utils.langdock.registry import get_registry
                        registry = get_registry()
                        enterprise_tool = registry.get("enterprise_info_query")
                    except:
                        pass
                    
                    if enterprise_tool:
                        query_result = await enterprise_tool.execute(
                            enterprise_name=party_name,
                            credit_code=credit_code
                        )
                        
                        if query_result.success:
                            enterprise_info = query_result.data.get("enterprise_info", {})
                            status = enterprise_info.get("status", "")
                            
                            if status not in ["存续", "在营"]:
                                violations.append({
                                    "type": "企业主体状态异常",
                                    "party": party_name,
                                    "description": f"企业主体 '{party_name}' 状态为 '{status}'，不符合签约要求",
                                    "suggestion": "请确认企业主体状态为'存续'或'在营'，否则合同可能无效"
                                })
                                continue
                    
                    valid_parties.append({
                        "name": party_name,
                        "type": "enterprise",
                        "status": "合规",
                        "credit_code": credit_code or business_license
                    })
                
                elif party_type == "individual":
                    # 个人主体校验
                    id_card = party_info.get("id_card")
                    adult_declaration = party_info.get("adult_declaration", False)
                    
                    if not id_card and not adult_declaration:
                        violations.append({
                            "type": "个人主体缺少资质证明",
                            "party": party_name,
                            "description": f"个人主体 '{party_name}' 缺少身份证号且无明确的成年声明",
                            "suggestion": "请补充身份证复印件，或明确声明'本人已年满18周岁'"
                        })
                        continue
                    
                    # 验证身份证号格式（18位）
                    if id_card and len(id_card) != 18:
                        violations.append({
                            "type": "身份证号格式错误",
                            "party": party_name,
                            "description": f"个人主体 '{party_name}' 的身份证号格式不正确（应为18位）",
                            "suggestion": "请确认身份证号为18位有效号码"
                        })
                        continue
                    
                    valid_parties.append({
                        "name": party_name,
                        "type": "individual",
                        "status": "合规",
                        "id_card": id_card or "已声明成年"
                    })
            
            # 判断合规状态
            compliance_status = "合规" if not violations else "违规"
            risk_level = "中风险" if violations else "无风险"
            
            result_data = {
                "rule_name": "签署主体合规校验",
                "compliance_status": compliance_status,
                "risk_level": risk_level,
                "parties": valid_parties,
                "violations": violations,
                "next_action": "法务人工复核" if violations else None,
                "notification": "需要邮件通知" if violations else None
            }
            
            return ToolResult(
                success=True,
                data=result_data,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"执行签署主体合规校验时发生错误: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _extract_parties(self, text: str) -> List[Dict]:
        """从合同文本中提取签署方信息"""
        parties = []
        
        # 提取企业主体（匹配"甲方：XX有限公司"等模式）
        enterprise_patterns = [
            r'(?:甲方|乙方|丙方|签署方)[：:]\s*([^，,。\n]+(?:有限公司|股份公司|公司|企业|集团))',
            r'([^，,。\n]+(?:有限公司|股份公司|公司|企业|集团))[：:]\s*(?:甲方|乙方|丙方)',
        ]
        
        for pattern in enterprise_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                name = match.group(1).strip()
                # 提取统一社会信用代码（18位）
                credit_code_match = re.search(r'统一社会信用代码[：:]\s*([A-Z0-9]{18})', text)
                credit_code = credit_code_match.group(1) if credit_code_match else None
                # 提取营业执照注册号（15位）
                license_match = re.search(r'营业执照[注册号]*[：:]\s*([0-9A-Z]{15})', text)
                business_license = license_match.group(1) if license_match else None
                
                parties.append({
                    "name": name,
                    "type": "enterprise",
                    "info": {
                        "credit_code": credit_code,
                        "business_license": business_license
                    }
                })
        
        # 提取个人主体（匹配"甲方：张三"等模式，排除公司名称）
        individual_patterns = [
            r'(?:甲方|乙方|丙方|签署方)[：:]\s*([^，,。\n]+(?!有限公司|股份公司|公司|企业|集团))',
        ]
        
        for pattern in individual_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                name = match.group(1).strip()
                # 排除明显是企业名称的情况
                if any(keyword in name for keyword in ["有限公司", "公司", "企业"]):
                    continue
                
                # 提取身份证号（18位）
                id_card_match = re.search(r'身份证[号]*[：:]\s*([0-9X]{18})', text)
                id_card = id_card_match.group(1) if id_card_match else None
                # 检查是否有成年声明
                adult_declaration = bool(re.search(r'(?:已年满|年满|已满)\s*18\s*周岁', text))
                
                parties.append({
                    "name": name,
                    "type": "individual",
                    "info": {
                        "id_card": id_card,
                        "adult_declaration": adult_declaration
                    }
                })
        
        # 去重
        seen = set()
        unique_parties = []
        for party in parties:
            key = (party["name"], party["type"])
            if key not in seen:
                seen.add(key)
                unique_parties.append(party)
        
        return unique_parties


class CoreClausesCompletenessTool(BaseTool):
    """规则2：合同核心条款完整性校验"""
    
    def get_info(self) -> ToolInfo:
        return ToolInfo(
            name="core_clauses_completeness",
            display_name="核心条款完整性校验",
            description="校验合同是否包含法定必备条款，避免关键信息缺失风险",
            parameters=[
                ToolParameter(
                    name="contract_text",
                    type="string",
                    description="合同文本内容",
                    required=True
                )
            ],
            category="compliance",
            version="1.0.0"
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行核心条款完整性校验"""
        start_time = time.time()
        
        try:
            is_valid, error_msg = self.validate_parameters(**kwargs)
            if not is_valid:
                return ToolResult(
                    success=False,
                    error=error_msg,
                    execution_time=time.time() - start_time
                )
            
            contract_text = kwargs.get("contract_text", "")
            
            # 检查必备条款
            required_clauses = {
                "标的": self._check_subject_matter(contract_text),
                "价款": self._check_price(contract_text),
                "履行期限": self._check_performance_period(contract_text),
                "违约责任": self._check_breach_of_contract(contract_text),
            }
            
            # 统计缺失的条款
            missing_clauses = [name for name, found in required_clauses.items() if not found]
            core_clauses = ["标的", "价款", "履行期限"]
            missing_core_clauses = [name for name in missing_clauses if name in core_clauses]
            
            # 判断合规状态
            if len(missing_core_clauses) > 0:
                # 缺失核心条款
                compliance_status = "违规"
                risk_level = "高风险"
            elif len(missing_clauses) >= 2:
                # 缺失2个或以上条款
                compliance_status = "违规"
                risk_level = "高风险"
            elif len(missing_clauses) == 1 and missing_clauses[0] == "违约责任":
                # 仅缺失违约责任
                compliance_status = "合规（需补充）"
                risk_level = "低风险"
            else:
                compliance_status = "合规"
                risk_level = "无风险"
            
            result_data = {
                "rule_name": "核心条款完整性校验",
                "compliance_status": compliance_status,
                "risk_level": risk_level,
                "required_clauses": {
                    name: "存在" if found else "缺失"
                    for name, found in required_clauses.items()
                },
                "missing_clauses": missing_clauses,
                "missing_core_clauses": missing_core_clauses,
                "next_action": "法务人工审批" if compliance_status == "违规" else ("建议补充违约责任" if "违约责任" in missing_clauses else None),
                "notification": "需要邮件通知" if compliance_status == "违规" else None
            }
            
            return ToolResult(
                success=True,
                data=result_data,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"执行核心条款完整性校验时发生错误: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _check_subject_matter(self, text: str) -> bool:
        """检查标的"""
        patterns = [
            r'标的[：:]\s*[^。\n]+',
            r'合同标的[：:]\s*[^。\n]+',
            r'货物名称[：:]\s*[^。\n]+',
            r'服务内容[：:]\s*[^。\n]+',
            r'产品名称[：:]\s*[^。\n]+',
        ]
        return any(re.search(pattern, text) for pattern in patterns)
    
    def _check_price(self, text: str) -> bool:
        """检查价款/报酬"""
        patterns = [
            r'(?:价款|价格|金额|报酬|费用|总价)[：:]\s*[^。\n]*(?:元|万元|人民币)',
            r'人民币\s*[0-9]+(?:\.[0-9]+)?\s*(?:元|万元)',
            r'按[^。\n]*(?:市场价|成本价|协议价)',
        ]
        return any(re.search(pattern, text) for pattern in patterns)
    
    def _check_performance_period(self, text: str) -> bool:
        """检查履行期限"""
        patterns = [
            r'(?:履行期限|合同期限|服务期限|交付期限)[：:]\s*[^。\n]+',
            r'\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日[^。\n]*(?:至|到)\s*\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日',
            r'自\s*\d{4}[年/-]\d{1,2}[月/-]\d{1,2}[日]?\s*起[^。\n]*(?:至|到)',
        ]
        return any(re.search(pattern, text) for pattern in patterns)
    
    def _check_breach_of_contract(self, text: str) -> bool:
        """检查违约责任"""
        patterns = [
            r'违约责任[：:]\s*[^。\n]+',
            r'违约[^。\n]*(?:违约金|赔偿|承担)',
            r'(?:逾期|延迟)[^。\n]*(?:支付|交付)[^。\n]*(?:违约金|赔偿)',
        ]
        return any(re.search(pattern, text) for pattern in patterns)


class LegalConflictComplianceTool(BaseTool):
    """规则3：合同条款与现行法规冲突校验"""
    
    def get_info(self) -> ToolInfo:
        return ToolInfo(
            name="legal_conflict_compliance",
            display_name="法规冲突校验",
            description="校验合同条款是否违反国家强制性法规，避免违法无效风险",
            parameters=[
                ToolParameter(
                    name="contract_text",
                    type="string",
                    description="合同文本内容",
                    required=True
                ),
                ToolParameter(
                    name="regulations",
                    type="array",
                    description="相关法规条文列表（可选，如果不提供则自动检索）",
                    required=False,
                    default=None
                )
            ],
            category="compliance",
            version="1.0.0"
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行法规冲突校验"""
        start_time = time.time()
        
        try:
            is_valid, error_msg = self.validate_parameters(**kwargs)
            if not is_valid:
                return ToolResult(
                    success=False,
                    error=error_msg,
                    execution_time=time.time() - start_time
                )
            
            contract_text = kwargs.get("contract_text", "")
            regulations = kwargs.get("regulations")
            
            # 如果没有提供法规，自动检索
            if not regulations:
                try:
                    from backend.utils.langdock.registry import get_registry
                    registry = get_registry()
                    regulation_tool = registry.get("regulation_search")
                    if regulation_tool:
                        keywords = "违约金,诉讼时效,争议解决,仲裁,诉讼"
                        search_result = await regulation_tool.execute(keywords=keywords, max_results=10)
                        if search_result.success:
                            regulations = search_result.data.get("regulations", [])
                except:
                    regulations = []
            
            # 检查三类冲突
            conflicts = []
            
            # 1. 违约金冲突检查
            penalty_conflict = self._check_penalty_conflict(contract_text)
            if penalty_conflict:
                conflicts.append(penalty_conflict)
            
            # 2. 诉讼时效冲突检查
            limitation_conflict = self._check_limitation_conflict(contract_text)
            if limitation_conflict:
                conflicts.append(limitation_conflict)
            
            # 3. 争议解决方式冲突检查
            dispute_resolution_conflict = self._check_dispute_resolution_conflict(contract_text)
            if dispute_resolution_conflict:
                conflicts.append(dispute_resolution_conflict)
            
            # 判断合规状态
            compliance_status = "合规" if not conflicts else "违规"
            risk_level = "高风险" if conflicts else "无风险"
            
            result_data = {
                "rule_name": "法规冲突校验",
                "compliance_status": compliance_status,
                "risk_level": risk_level,
                "conflicts": conflicts,
                "regulations_referenced": regulations[:3] if regulations else [],
                "next_action": "法务人工修改" if conflicts else None,
                "notification": "需要邮件通知" if conflicts else None
            }
            
            return ToolResult(
                success=True,
                data=result_data,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"执行法规冲突校验时发生错误: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _check_penalty_conflict(self, text: str) -> Optional[Dict]:
        """检查违约金冲突（《民法典》第585条）"""
        # 提取违约金比例
        patterns = [
            r'违约金[^。\n]*(?:按|为|比例|标准)[^。\n]*([0-9]+(?:\.[0-9]+)?)\s*%',
            r'违约金[^。\n]*(?:按|为|比例|标准)[^。\n]*([0-9]+(?:\.[0-9]+)?)\s*‰',
            r'违约金[^。\n]*(?:按|为|比例|标准)[^。\n]*([0-9]+(?:\.[0-9]+)?)\s*倍',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                value = float(match.group(1))
                # 检查是否超过30%
                if value > 30:
                    # 检查是否有实际损失举证说明
                    has_loss_proof = bool(re.search(r'(?:实际损失|损失举证|损失证明|损失计算)', text))
                    
                    if not has_loss_proof:
                        return {
                            "type": "违约金冲突",
                            "description": f"约定违约金比例 {value}% 超过法定上限 30%",
                            "law_reference": "《民法典》第585条",
                            "conflict_detail": "约定违约金比例超过合同总金额的30%，且无实际损失举证说明",
                            "suggestion": f"建议将违约金比例调整为不超过合同总金额的30%，或补充实际损失举证说明",
                            "severity": "高风险"
                        }
        
        return None
    
    def _check_limitation_conflict(self, text: str) -> Optional[Dict]:
        """检查诉讼时效冲突（《民法典》第188条）"""
        # 提取诉讼时效
        patterns = [
            r'诉讼时效[^。\n]*(?:为|是|约定)[^。\n]*([0-9]+)\s*年',
            r'时效[^。\n]*(?:为|是|约定)[^。\n]*([0-9]+)\s*年',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                years = int(match.group(1))
                # 普通合同纠纷应为3年，特殊纠纷（如人身损害赔偿）为1年
                if years < 3:
                    # 检查是否是特殊纠纷
                    is_special = bool(re.search(r'(?:人身损害|身体伤害|医疗事故)', text))
                    if is_special and years < 1:
                        return {
                            "type": "诉讼时效冲突",
                            "description": f"约定诉讼时效 {years} 年低于法定最低期限 1 年（特殊纠纷）",
                            "law_reference": "《民法典》第188条",
                            "conflict_detail": "特殊纠纷（如人身损害赔偿）的诉讼时效不得低于1年",
                            "suggestion": "建议将诉讼时效调整为至少1年，或删除该约定使用法定时效",
                            "severity": "高风险"
                        }
                    elif not is_special and years < 3:
                        return {
                            "type": "诉讼时效冲突",
                            "description": f"约定诉讼时效 {years} 年低于法定最低期限 3 年（普通合同纠纷）",
                            "law_reference": "《民法典》第188条",
                            "conflict_detail": "普通合同纠纷的诉讼时效不得低于3年",
                            "suggestion": "建议将诉讼时效调整为至少3年，或删除该约定使用法定时效",
                            "severity": "高风险"
                        }
        
        return None
    
    def _check_dispute_resolution_conflict(self, text: str) -> Optional[Dict]:
        """检查争议解决方式冲突（《仲裁法》第5条）"""
        # 检查是否同时约定仲裁和诉讼
        has_arbitration = bool(re.search(r'(?:仲裁|仲裁委|仲裁委员会|仲裁机构)', text))
        has_litigation = bool(re.search(r'(?:诉讼|法院|人民法院|起诉)', text))
        
        # 检查是否有冲突性表述
        conflict_patterns = [
            r'(?:仲裁|诉讼)[^。\n]*(?:或|或者)[^。\n]*(?:诉讼|仲裁)',
            r'(?:可|可以)[^。\n]*(?:向仲裁委申请仲裁|向法院起诉)[^。\n]*(?:或|或者)[^。\n]*(?:向法院起诉|向仲裁委申请仲裁)',
        ]
        
        has_conflict = any(re.search(pattern, text) for pattern in conflict_patterns)
        
        if has_conflict or (has_arbitration and has_litigation and "或" in text):
            return {
                "type": "争议解决方式冲突",
                "description": "同时约定仲裁和诉讼，违反《仲裁法》第5条",
                "law_reference": "《仲裁法》第5条",
                "conflict_detail": "合同不能同时约定仲裁和诉讼两种争议解决方式，仲裁约定无效",
                "suggestion": "建议明确选择一种争议解决方式：要么选择仲裁（需明确仲裁机构），要么选择诉讼（需明确管辖法院），删除另一种约定",
                "severity": "高风险"
            }
        
        return None

