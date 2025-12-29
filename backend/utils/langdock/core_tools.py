"""
核心工具实现
包括：文档解析、OCR、法规检索、风险评估
"""

import time
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

from backend.utils.langdock.tools import BaseTool
from backend.utils.langdock.models import ToolInfo, ToolParameter, ToolResult


class DocumentParserTool(BaseTool):
    """文档解析工具 - 支持 docx/pdf 文本提取"""
    
    def get_info(self) -> ToolInfo:
        return ToolInfo(
            name="document_parser",
            display_name="文档解析工具",
            description="解析合同文档（支持 docx/pdf 格式），提取结构化文本内容",
            parameters=[
                ToolParameter(
                    name="file_path",
                    type="string",
                    description="文档文件路径（支持 .docx 和 .pdf 格式）",
                    required=True
                ),
                ToolParameter(
                    name="extract_structure",
                    type="boolean",
                    description="是否提取结构化信息（章节、段落等）",
                    required=False,
                    default=True
                )
            ],
            category="document",
            version="1.0.0"
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行文档解析"""
        start_time = time.time()
        
        try:
            # 验证参数
            is_valid, error_msg = self.validate_parameters(**kwargs)
            if not is_valid:
                return ToolResult(
                    success=False,
                    error=error_msg,
                    execution_time=time.time() - start_time
                )
            
            file_path = kwargs.get("file_path")
            extract_structure = kwargs.get("extract_structure", True)
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return ToolResult(
                    success=False,
                    error=f"文件不存在: {file_path}",
                    execution_time=time.time() - start_time
                )
            
            # 获取文件扩展名
            file_ext = Path(file_path).suffix.lower()
            
            # 解析文档
            text_content = ""
            structure = {}
            
            if file_ext == ".pdf":
                # 解析 PDF
                try:
                    import fitz  # PyMuPDF
                    doc = fitz.open(file_path)
                    pages = []
                    for page_num in range(len(doc)):
                        page = doc[page_num]
                        text = page.get_text()
                        pages.append({
                            "page": page_num + 1,
                            "text": text
                        })
                        text_content += f"\n\n--- 第 {page_num + 1} 页 ---\n\n{text}"
                    doc.close()
                    
                    if extract_structure:
                        structure = {
                            "total_pages": len(doc),
                            "pages": pages
                        }
                except ImportError:
                    return ToolResult(
                        success=False,
                        error="PDF 解析需要安装 PyMuPDF: pip install pymupdf",
                        execution_time=time.time() - start_time
                    )
                except Exception as e:
                    return ToolResult(
                        success=False,
                        error=f"PDF 解析失败: {str(e)}",
                        execution_time=time.time() - start_time
                    )
            
            elif file_ext == ".docx":
                # 解析 DOCX
                try:
                    from docx import Document
                    doc = Document(file_path)
                    
                    paragraphs = []
                    for para in doc.paragraphs:
                        if para.text.strip():
                            paragraphs.append(para.text)
                            text_content += para.text + "\n"
                    
                    if extract_structure:
                        structure = {
                            "total_paragraphs": len(paragraphs),
                            "paragraphs": paragraphs
                        }
                except ImportError:
                    return ToolResult(
                        success=False,
                        error="DOCX 解析需要安装 python-docx: pip install python-docx",
                        execution_time=time.time() - start_time
                    )
                except Exception as e:
                    return ToolResult(
                        success=False,
                        error=f"DOCX 解析失败: {str(e)}",
                        execution_time=time.time() - start_time
                    )
            else:
                return ToolResult(
                    success=False,
                    error=f"不支持的文件格式: {file_ext}。支持格式: .pdf, .docx",
                    execution_time=time.time() - start_time
                )
            
            result_data = {
                "file_path": file_path,
                "file_type": file_ext,
                "text_content": text_content.strip(),
                "structure": structure if extract_structure else None,
                "text_length": len(text_content),
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
                error=f"执行文档解析时发生错误: {str(e)}",
                execution_time=time.time() - start_time
            )


class OCRParserTool(BaseTool):
    """OCR 解析工具 - 支持图片类合同识别"""
    
    def get_info(self) -> ToolInfo:
        return ToolInfo(
            name="ocr_parser",
            display_name="OCR 解析工具",
            description="识别图片类合同，提取文本内容（支持常见图片格式）",
            parameters=[
                ToolParameter(
                    name="image_path",
                    type="string",
                    description="图片文件路径（支持 .jpg, .png, .jpeg, .bmp 等格式）",
                    required=True
                ),
                ToolParameter(
                    name="language",
                    type="string",
                    description="识别语言（zh: 中文, en: 英文, zh+en: 中英文）",
                    required=False,
                    default="zh+en"
                )
            ],
            category="document",
            version="1.0.0"
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行 OCR 解析"""
        start_time = time.time()
        
        try:
            # 验证参数
            is_valid, error_msg = self.validate_parameters(**kwargs)
            if not is_valid:
                return ToolResult(
                    success=False,
                    error=error_msg,
                    execution_time=time.time() - start_time
                )
            
            image_path = kwargs.get("image_path")
            language = kwargs.get("language", "zh+en")
            
            # 检查文件是否存在
            if not os.path.exists(image_path):
                return ToolResult(
                    success=False,
                    error=f"图片文件不存在: {image_path}",
                    execution_time=time.time() - start_time
                )
            
            # 检查文件格式
            file_ext = Path(image_path).suffix.lower()
            supported_formats = [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"]
            if file_ext not in supported_formats:
                return ToolResult(
                    success=False,
                    error=f"不支持的图片格式: {file_ext}。支持格式: {', '.join(supported_formats)}",
                    execution_time=time.time() - start_time
                )
            
            # 尝试使用 PaddleOCR（如果可用）
            ocr_text = ""
            try:
                from paddleocr import PaddleOCR
                ocr = PaddleOCR(use_angle_cls=True, lang='ch')
                result = ocr.ocr(image_path, cls=True)
                
                # 解析 OCR 结果
                texts = []
                for line in result[0] if result else []:
                    if line and len(line) >= 2:
                        text = line[1][0] if isinstance(line[1], (list, tuple)) else line[1]
                        texts.append(text)
                        ocr_text += text + "\n"
                
            except ImportError:
                # 如果没有安装 PaddleOCR，使用简单的模拟实现
                # 实际项目中应该安装: pip install paddleocr
                ocr_text = f"[模拟 OCR 结果] 从图片 {image_path} 识别出的文本内容。\n" \
                          f"提示: 安装 PaddleOCR 以获得真实的 OCR 功能: pip install paddleocr"
            except Exception as e:
                return ToolResult(
                    success=False,
                    error=f"OCR 识别失败: {str(e)}",
                    execution_time=time.time() - start_time
                )
            
            result_data = {
                "image_path": image_path,
                "language": language,
                "recognized_text": ocr_text.strip(),
                "text_length": len(ocr_text),
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
                error=f"执行 OCR 解析时发生错误: {str(e)}",
                execution_time=time.time() - start_time
            )


class RegulationSearchTool(BaseTool):
    """法规检索工具 - 接入公开法规数据库（Mock）"""
    
    def __init__(self):
        super().__init__()
        # Mock 法规数据库
        self.mock_regulations = {
            "合同": [
                {
                    "title": "《中华人民共和国民法典》第四百六十四条",
                    "content": "合同是民事主体之间设立、变更、终止民事法律关系的协议。",
                    "category": "合同法"
                },
                {
                    "title": "《中华人民共和国民法典》第四百六十五条",
                    "content": "依法成立的合同，受法律保护。依法成立的合同，仅对当事人具有法律约束力，但是法律另有规定的除外。",
                    "category": "合同法"
                }
            ],
            "违约责任": [
                {
                    "title": "《中华人民共和国民法典》第五百七十七条",
                    "content": "当事人一方不履行合同义务或者履行合同义务不符合约定的，应当承担继续履行、采取补救措施或者赔偿损失等违约责任。",
                    "category": "合同法"
                }
            ],
            "解除": [
                {
                    "title": "《中华人民共和国民法典》第五百六十三条",
                    "content": "有下列情形之一的，当事人可以解除合同：（一）因不可抗力致使不能实现合同目的；（二）在履行期限届满前，当事人一方明确表示或者以自己的行为表明不履行主要债务；",
                    "category": "合同法"
                }
            ],
            "保密": [
                {
                    "title": "《中华人民共和国反不正当竞争法》第九条",
                    "content": "经营者不得实施下列侵犯商业秘密的行为：（一）以盗窃、贿赂、欺诈、胁迫、电子侵入或者其他不正当手段获取权利人的商业秘密；",
                    "category": "反不正当竞争法"
                }
            ]
        }
    
    def get_info(self) -> ToolInfo:
        return ToolInfo(
            name="regulation_search",
            display_name="法规检索工具",
            description="检索相关法规条文，输入合同条款关键词，返回匹配的法规条文",
            parameters=[
                ToolParameter(
                    name="keywords",
                    type="string",
                    description="检索关键词（合同条款关键词，多个关键词用逗号分隔）",
                    required=True
                ),
                ToolParameter(
                    name="max_results",
                    type="integer",
                    description="最大返回结果数量",
                    required=False,
                    default=5
                )
            ],
            category="search",
            version="1.0.0"
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行法规检索"""
        start_time = time.time()
        
        try:
            # 验证参数
            is_valid, error_msg = self.validate_parameters(**kwargs)
            if not is_valid:
                return ToolResult(
                    success=False,
                    error=error_msg,
                    execution_time=time.time() - start_time
                )
            
            keywords_str = kwargs.get("keywords", "")
            max_results = kwargs.get("max_results", 5)
            
            # 解析关键词
            keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]
            
            if not keywords:
                return ToolResult(
                    success=False,
                    error="关键词不能为空",
                    execution_time=time.time() - start_time
                )
            
            # 检索法规
            results = []
            for keyword in keywords:
                # 简单的关键词匹配（实际应该使用更复杂的检索算法）
                for reg_key, regulations in self.mock_regulations.items():
                    if keyword in reg_key or any(keyword in reg.get("title", "") or keyword in reg.get("content", "") for reg in regulations):
                        results.extend(regulations)
            
            # 去重
            seen = set()
            unique_results = []
            for reg in results:
                reg_id = reg.get("title", "")
                if reg_id not in seen:
                    seen.add(reg_id)
                    unique_results.append(reg)
            
            # 限制结果数量
            unique_results = unique_results[:max_results]
            
            result_data = {
                "keywords": keywords,
                "total_results": len(unique_results),
                "regulations": unique_results,
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
                error=f"执行法规检索时发生错误: {str(e)}",
                execution_time=time.time() - start_time
            )


class RiskAssessmentTool(BaseTool):
    """风险评估工具 - 输入合同文本+法规条文，输出风险等级+冲突条款说明"""
    
    def get_info(self) -> ToolInfo:
        return ToolInfo(
            name="risk_assessment",
            display_name="风险评估工具",
            description="分析合同文本和法规条文，识别风险等级和冲突条款",
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
                ),
                ToolParameter(
                    name="risk_types",
                    type="array",
                    description="要评估的风险类型列表，如 ['legal', 'financial', 'operational']",
                    required=False,
                    default=["legal", "financial"]
                )
            ],
            category="analysis",
            version="1.0.0"
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行风险评估"""
        start_time = time.time()
        
        try:
            # 验证参数
            is_valid, error_msg = self.validate_parameters(**kwargs)
            if not is_valid:
                return ToolResult(
                    success=False,
                    error=error_msg,
                    execution_time=time.time() - start_time
                )
            
            contract_text = kwargs.get("contract_text", "")
            regulations = kwargs.get("regulations")
            risk_types = kwargs.get("risk_types", ["legal", "financial"])
            
            if not contract_text:
                return ToolResult(
                    success=False,
                    error="合同文本不能为空",
                    execution_time=time.time() - start_time
                )
            
            # 如果没有提供法规条文，尝试自动检索
            if not regulations:
                # 调用法规检索工具
                try:
                    from backend.utils.langdock.registry import get_registry
                    registry = get_registry()
                    regulation_tool = registry.get("regulation_search")
                    if regulation_tool:
                        keywords = self._extract_keywords(contract_text)
                        if keywords:
                            keywords_str = ", ".join(keywords)
                            search_result = await regulation_tool.execute(keywords=keywords_str, max_results=5)
                            if search_result.success and search_result.data:
                                regulations = search_result.data.get("regulations", [])
                except Exception as e:
                    print(f"自动检索法规失败: {str(e)}")
                    regulations = []
            
            # 分析风险（这里使用 LLM 进行实际分析）
            risks = await self._analyze_risks(contract_text, regulations, risk_types)
            
            # 计算总体风险等级
            overall_risk_level = self._calculate_risk_level(risks)
            
            result_data = {
                "contract_text_length": len(contract_text),
                "regulations_count": len(regulations) if regulations else 0,
                "risk_types_analyzed": risk_types,
                "overall_risk_level": overall_risk_level,
                "risks": risks,
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
                error=f"执行风险评估时发生错误: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _extract_keywords(self, text: str) -> List[str]:
        """从文本中提取关键词"""
        # 简化的关键词提取（实际应该使用 NLP 技术）
        keywords = []
        common_terms = ["合同", "违约", "解除", "保密", "责任", "赔偿", "期限"]
        for term in common_terms:
            if term in text:
                keywords.append(term)
        return keywords[:5]  # 返回前5个关键词
    
    async def _analyze_risks(self, contract_text: str, regulations: List[Dict], risk_types: List[str]) -> List[Dict]:
        """分析风险（使用 LLM）"""
        risks = []
        
        try:
            # 使用 LLM 进行风险分析
            from backend.utils.llm import get_llm_client, ChatMessage
            
            # 构建提示词
            regulations_text = ""
            if regulations:
                regulations_text = "\n\n相关法规条文：\n"
                for reg in regulations:
                    regulations_text += f"- {reg.get('title', '')}: {reg.get('content', '')}\n"
            
            prompt = f"""请分析以下合同文本，识别潜在风险。

合同文本：
{contract_text[:2000]}  # 限制长度避免超出 token 限制
{regulations_text}

请从以下风险类型进行分析：{', '.join(risk_types)}

请以 JSON 格式返回分析结果，包含：
1. 风险类型
2. 风险严重程度（high/medium/low）
3. 风险描述
4. 冲突条款说明（如果有）
5. 建议措施

格式示例：
{{
    "risks": [
        {{
            "type": "legal",
            "severity": "high",
            "description": "风险描述",
            "conflicting_clauses": ["冲突条款1", "冲突条款2"],
            "recommendation": "建议措施"
        }}
    ]
}}
"""
            
            client = get_llm_client()
            messages = [
                ChatMessage(
                    role="system",
                    content="你是一个专业的合同风险分析专家，擅长识别合同中的法律、财务和运营风险。"
                ),
                ChatMessage(role="user", content=prompt)
            ]
            
            response = await client.chat(messages, temperature=0.3)
            
            # 解析 LLM 响应
            import json
            import re
            response_text = response.content
            
            # 尝试提取 JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    risks = result.get("risks", [])
                except json.JSONDecodeError:
                    # 如果 JSON 解析失败，使用简化的风险分析
                    risks = self._fallback_risk_analysis(contract_text, regulations, risk_types)
            else:
                # 如果没有找到 JSON，使用简化的风险分析
                risks = self._fallback_risk_analysis(contract_text, regulations, risk_types)
                
        except Exception as e:
            # 如果 LLM 调用失败，使用简化的风险分析
            print(f"LLM 分析失败，使用简化分析: {str(e)}")
            risks = self._fallback_risk_analysis(contract_text, regulations, risk_types)
        
        return risks
    
    def _fallback_risk_analysis(self, contract_text: str, regulations: List[Dict], risk_types: List[str]) -> List[Dict]:
        """简化的风险分析（当 LLM 不可用时使用）"""
        risks = []
        
        # 简化的风险分析逻辑
        if "legal" in risk_types:
            risks.append({
                "type": "legal",
                "severity": "medium",
                "description": "合同条款可能存在法律风险，建议咨询法律顾问",
                "conflicting_clauses": [],
                "recommendation": "建议审查相关法规条文，确保合同条款符合法律规定"
            })
        
        if "financial" in risk_types:
            risks.append({
                "type": "financial",
                "severity": "low",
                "description": "财务风险较低，但需注意付款条款",
                "conflicting_clauses": [],
                "recommendation": "建议明确付款方式和时间"
            })
        
        return risks
    
    def _calculate_risk_level(self, risks: List[Dict]) -> str:
        """计算总体风险等级"""
        if not risks:
            return "low"
        
        severities = [r.get("severity", "low") for r in risks]
        if "high" in severities:
            return "high"
        elif "medium" in severities:
            return "medium"
        else:
            return "low"

