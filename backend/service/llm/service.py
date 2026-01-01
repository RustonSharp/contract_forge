"""
LLM 对话服务层
实现工具调用逻辑，让 LLM 可以根据用户需求调用工具
"""

import json
import re
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from backend.utils.llm import get_llm_client, ChatMessage
from backend.service.tools.registry import get_registry
from backend.service.tools.initialize import initialize_default_tools
from backend.service.files.service import FileService
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def _convert_to_relative_path(file_path: str, uploads_dir: str = "./uploads") -> str:
    """
    将文件路径转换为相对路径（相对于 uploads 目录）
    
    Args:
        file_path: 文件路径（可以是绝对路径、相对路径或文件名）
        uploads_dir: uploads 目录路径，默认为 "./uploads"
    
    Returns:
        相对路径（如 "2025-12-29/test_contract.pdf"），如果无法转换则返回原始路径
    """
    from pathlib import Path
    import os
    
    # 如果是相对路径且包含路径分隔符，直接返回（已经 relative to uploads）
    if "/" in file_path or "\\" in file_path:
        # 检查是否是相对于 uploads 目录的路径
        uploads_path = Path(uploads_dir).resolve()
        file_path_obj = Path(file_path)
        
        # 如果是绝对路径，尝试转换为相对路径
        if file_path_obj.is_absolute():
            try:
                relative = file_path_obj.relative_to(uploads_path)
                return str(relative).replace("\\", "/")
            except ValueError:
                # 不在 uploads 目录下，返回原始路径
                pass
        
        # 如果不是绝对路径，可能是相对于 uploads 的路径，直接返回
        return file_path.replace("\\", "/")
    
    # 如果只是文件名，返回文件名（让调用者处理）
    return file_path


class LLMChatService:
    """LLM 对话服务，支持工具调用"""
    
    def __init__(self):
        self.llm_client = get_llm_client()
        self.registry = get_registry()
        self.file_service = FileService()
        
        # 确保工具已初始化
        if self.registry.count() == 0:
            logger.info("工具未初始化，正在初始化...")
            initialize_default_tools()
    
    def _build_tools_description(self) -> str:
        """构建工具描述，用于提示词"""
        tools = []
        for tool_name in self.registry.list_tool_names():
            tool = self.registry.get(tool_name)
            if tool:
                info = tool.info
                params_desc = []
                for param in info.parameters:
                    param_str = f"  - {param.name} ({param.type})"
                    if not param.required:
                        param_str += " [可选]"
                    param_str += f": {param.description}"
                    if param.default is not None:
                        param_str += f" (默认: {param.default})"
                    params_desc.append(param_str)
                
                params_text = "\n".join(params_desc) if params_desc else "  无参数"
                
                tool_desc = f"""
工具名称: {info.name}
显示名称: {info.display_name}
功能描述: {info.description}
参数:
{params_text}
"""
                tools.append(tool_desc)
        
        return "\n".join(tools)
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        tools_description = self._build_tools_description()
        
        # 特别强调 N8N 工作流的使用场景
        n8n_tool = self.registry.get("n8n_workflow_trigger")
        n8n_description = ""
        if n8n_tool:
            n8n_info = n8n_tool.info
            n8n_description = f"""

═══════════════════════════════════════════════════════════════
特别说明 - N8N 工作流触发工具 ({n8n_info.name})
═══════════════════════════════════════════════════════════════

功能描述：{n8n_info.description}

【重要】使用场景（优先使用此工具）：
1. ✅ 当用户要求"处理文件"、"分析合同"、"审核合同"、"处理合同"等，但没有指定具体工具时
2. ✅ 当用户只提供了文件名（如"test_contract.pdf"），要求进行完整的合同处理流程时
3. ✅ 当用户希望执行自动化流程（包括文档解析、合规校验、风险评估等）时
4. ✅ 当用户说"帮我处理一下这个合同"、"分析这个文件"等通用请求时

参数说明：
"""
            for param in n8n_info.parameters:
                n8n_description += f"  • {param.name} ({param.type}): {param.description}\n"
                if param.default is not None:
                    n8n_description += f"    默认值: {param.default}\n"
        
        return f"""你是一个专业的合同分析助手，可以帮助用户处理合同文件、进行合规校验、风险评估等任务。

你可以使用以下工具来完成用户的需求：

{tools_description}

{n8n_description}

═══════════════════════════════════════════════════════════════
工具调用规则（请严格遵守）
═══════════════════════════════════════════════════════════════

【规则 1 - 优先使用 N8N 工作流】
当用户要求处理文件但没有指定具体工具时，必须优先使用 n8n_workflow_trigger 工具。
例如：
- 用户说："处理 test_contract.pdf" → 使用 n8n_workflow_trigger
- 用户说："分析这个合同" → 使用 n8n_workflow_trigger
- 用户说："帮我审核一下合同" → 使用 n8n_workflow_trigger

**例外情况**：如果用户明确提到以下关键词，不要使用 n8n_workflow_trigger，而应使用对应的专用工具：
- "电子签名"、"签名"、"数字签名" → 使用 digital_signature（电子签名工具）
- "转pdf"、"转换为pdf"、"转为pdf" → 使用 image_to_pdf（图片转PDF工具）

【规则 2 - 明确指定任务时根据文件类型选择工具】
如果用户明确要求执行特定任务，必须根据文件类型和任务类型选择正确的工具：

**解析任务（包括"提取内容"、"解析"、"提取文本"、"识别"等）**：
- 如果文件是图片格式（.jpg, .jpeg, .png, .bmp, .tiff, .tif）→ 使用 ocr_parser（OCR解析工具）
- 如果文件是文档格式（.pdf, .docx, .doc）→ 使用 document_parser（文档解析工具）
- 如果用户只说"提取内容"、"解析"等但没有指定文件，需要从上下文或对话中提取文件名
- **重要**：当用户说"提取内容"时，必须根据文件类型自动选择合适的解析工具

**格式转换任务（包括"转为pdf"、"转pdf"、"转换为pdf"、"转换成pdf"等）**：
- 如果文件是图片格式（.jpg, .jpeg, .png, .bmp, .tiff, .tif）→ 使用 image_to_pdf（图片转PDF工具）
- 用户说："把这个图片转为pdf"、"转pdf"、"转换为pdf" → 使用 image_to_pdf
- **重要**：格式转换任务必须使用对应的转换工具，不要使用 n8n_workflow_trigger

**电子签名任务（包括"电子签名"、"签名"、"数字签名"、"验证签名"等）**：
- 用户说："使用电子签名工具"、"给文件签名"、"对文件进行数字签名" → 使用 digital_signature（电子签名工具）
- 用户说："验证签名"、"验证文件签名" → 使用 digital_signature，参数 action="verify"
- 用户说："签名文件"、"签署文件" → 使用 digital_signature，参数 action="sign"（默认）
- **重要**：电子签名任务必须使用 digital_signature 工具，不要使用 n8n_workflow_trigger

**其他明确任务**：
- 用户说："进行风险评估" → 使用 risk_assessment（需要先有合同文本）
- 用户说："查询法规" → 使用 regulation_search
- 用户说："合规校验" → 使用对应的合规工具（signing_subject_compliance, core_clauses_completeness, legal_conflict_compliance）
- 用户说："企业信息查询" → 使用 enterprise_info_query

**文件类型判断**：
- 图片格式：.jpg, .jpeg, .png, .bmp, .tiff, .tif
- 文档格式：.pdf, .docx, .doc

【规则 3 - 工具调用格式】
必须使用 JSON 格式，包含 tool_name 和 parameters 字段。
格式示例：
```json
{{
    "tool_name": "n8n_workflow_trigger",
    "parameters": {{
        "file_name": "test_contract.pdf"
    }}
}}
```

【规则 4 - 工具执行后直接回答】
当工具执行成功后，必须直接使用工具返回的结果回答用户的问题，**不要再调用工具**。
- 如果工具返回了文本内容（如 OCR 或文档解析），直接使用这些内容回答用户
- 如果工具执行失败，向用户说明错误情况，不要重复调用同一个工具
- **重要**：工具执行一次即可，不要重复调用同一个工具

【规则 5 - 仅提问时直接回答】
如果用户只是询问问题（如"什么是合同？"），不需要调用工具，直接回答即可。

═══════════════════════════════════════════════════════════════
工具调用示例
═══════════════════════════════════════════════════════════════

示例 1 - 处理文件（使用 N8N 工作流）：
用户："帮我处理一下 test_contract.pdf"
你的响应：
```json
{{
    "tool_name": "n8n_workflow_trigger",
    "parameters": {{
        "file_name": "test_contract.pdf"
    }}
}}
```

示例 2 - 解析图片文件（使用 OCR）：
用户："解析这个合同图片" 或 "解析 test_contract.jpg" 或 "提取内容 test_contract.jpg"
你的响应：
```json
{{
    "tool_name": "ocr_parser",
    "parameters": {{
        "image_path": "test_contract.jpg"
    }}
}}
```

示例 3 - 解析文档文件（使用文档解析）：
用户："解析文档 test.pdf" 或 "解析这个PDF合同" 或 "提取内容 test.pdf"
你的响应：
```json
{{
    "tool_name": "document_parser",
    "parameters": {{
        "file_path": "test.pdf"
    }}
}}
```

示例 3.1 - 提取内容（根据文件类型自动选择工具）：
用户："提取内容"（已指定文件）
- 如果文件是图片（.jpg, .png等）→ 使用 ocr_parser
- 如果文件是文档（.pdf, .docx等）→ 使用 document_parser

示例 3.2 - 图片转PDF：
用户："把这个图片转为pdf" 或 "转pdf test_contract.jpg" 或 "转换为pdf"
你的响应：
```json
{{
    "tool_name": "image_to_pdf",
    "parameters": {{
        "image_path": "test_contract.jpg"
    }}
}}
```

示例 4 - 电子签名任务：
用户："使用电子签名工具" 或 "给 test_contract.pdf 签名" 或 "对文件进行数字签名"
你的响应：
```json
{{
    "tool_name": "digital_signature",
    "parameters": {{
        "action": "sign",
        "file_path": "test_contract.pdf",
        "signer_name": "默认签名者"
    }}
}}
```

用户："验证签名" 或 "验证 test_contract.pdf 的签名"
你的响应：
```json
{{
    "tool_name": "digital_signature",
    "parameters": {{
        "action": "verify",
        "file_path": "test_contract.pdf"
    }}
}}
```

示例 5 - 其他明确任务：
用户："进行风险评估"
你的响应：
```json
{{
    "tool_name": "risk_assessment",
    "parameters": {{
        "contract_text": "合同文本内容..."
    }}
}}
```

示例 6 - 仅提问：
用户："什么是合同？"
你的响应：直接回答，不调用工具。

═══════════════════════════════════════════════════════════════
重要提示 - 文件类型识别
═══════════════════════════════════════════════════════════════

当用户要求"提取内容"、"解析"、"提取文本"、"识别"文件时，必须根据文件扩展名选择工具：
- 图片文件（.jpg, .jpeg, .png, .bmp, .tiff, .tif）→ ocr_parser（OCR解析工具）
- 文档文件（.pdf, .docx, .doc）→ document_parser（文档解析工具）

**特别说明**：
- "提取内容"等同于"解析"，必须根据文件类型自动选择合适的解析工具
- 如果用户没有提供文件名，尝试从对话历史中提取最近提到的文件名
- 如果已指定文件路径，优先使用指定的文件路径

═══════════════════════════════════════════════════════════════

请根据用户的需求，智能地选择和使用合适的工具。记住：当用户要求处理文件但没有指定具体工具时，优先使用 n8n_workflow_trigger！
"""
    
    def _extract_file_name_from_messages(self, messages: Union[List[Dict[str, str]], List[ChatMessage]]) -> Optional[str]:
        """从消息历史中提取文件名"""
        # 从最近的用户消息中查找文件名
        for msg in reversed(messages):
            # 处理 ChatMessage 对象或字典
            if isinstance(msg, ChatMessage):
                role = msg.role
                content = msg.content
            else:
                role = msg.get("role")
                content = msg.get("content", "")
            
            if role == "user":
                # 匹配文件名模式（包含扩展名）
                file_patterns = [
                    r'([^\s，,。\n]+\.(?:pdf|docx?|jpg|jpeg|png|bmp|tiff?))',
                ]
                for pattern in file_patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        return match.group(1).strip()
        return None
    
    def _parse_date_reference(self, text: str) -> Optional[str]:
        """解析日期引用（如"昨天"、"今天"、"前天"等）"""
        today = datetime.now()
        text_lower = text.lower()
        
        # 匹配日期关键词
        if "今天" in text or "今日" in text or "now" in text_lower or "today" in text_lower:
            return today.strftime("%Y-%m-%d")
        elif "昨天" in text or "昨日" in text or "yesterday" in text_lower:
            yesterday = today - timedelta(days=1)
            return yesterday.strftime("%Y-%m-%d")
        elif "前天" in text or "day before yesterday" in text_lower:
            day_before = today - timedelta(days=2)
            return day_before.strftime("%Y-%m-%d")
        elif "明天" in text or "明日" in text or "tomorrow" in text_lower:
            tomorrow = today + timedelta(days=1)
            return tomorrow.strftime("%Y-%m-%d")
        
        # 尝试匹配日期格式 YYYY-MM-DD
        date_match = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', text)
        if date_match:
            date_str = date_match.group(1).replace('/', '-')
            try:
                # 验证日期格式
                parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
                return parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                pass
        
        return None
    
    async def _find_files_by_description(self, text: str) -> Dict[str, Any]:
        """
        根据用户描述查找文件
        
        Returns:
            Dict with keys: files (List[FileInfo]), date (Optional[str]), message (str)
        """
        try:
            # 解析日期引用
            date = self._parse_date_reference(text)
            
            # 提取文件名（如果有）
            file_name_pattern = r'([^\s，,。\n]+\.(?:pdf|docx?|jpg|jpeg|png|bmp|tiff?))'
            file_name_match = re.search(file_name_pattern, text, re.IGNORECASE)
            file_name = file_name_match.group(1).strip() if file_name_match else None
            
            files = []
            
            if file_name:
                # 如果指定了文件名，精确查找
                if date:
                    # 在指定日期的目录中查找
                    date_files = await self.file_service.list_files(date=date, page=1, page_size=100)
                    files = [f for f in date_files if file_name.lower() in f.file_name.lower()]
                else:
                    # 在所有文件中查找
                    all_files = await self.file_service.list_files(page=1, page_size=100)
                    files = [f for f in all_files if file_name.lower() in f.file_name.lower()]
            elif date:
                # 如果只指定了日期，查找该日期的所有文件
                files = await self.file_service.list_files(date=date, page=1, page_size=100)
            else:
                # 如果都没有指定，查找最近的文件
                files = await self.file_service.list_files(page=1, page_size=10)
            
            if len(files) == 0:
                date_desc = f"（日期: {date}）" if date else ""
                return {
                    "files": [],
                    "date": date,
                    "message": f"未找到符合条件的文件{date_desc}。请检查文件名或日期是否正确。"
                }
            elif len(files) == 1:
                return {
                    "files": files,
                    "date": date,
                    "message": f"找到 1 个文件: {files[0].file_name}"
                }
            else:
                file_list = "\n".join([f"- {f.file_name} ({f.upload_date})" for f in files[:10]])
                if len(files) > 10:
                    file_list += f"\n... 还有 {len(files) - 10} 个文件"
                
                return {
                    "files": files,
                    "date": date,
                    "message": f"找到 {len(files)} 个文件：\n{file_list}\n\n是否全部处理？请回复'是'或'全部处理'来确认，或指定要处理的文件名。"
                }
        
        except Exception as e:
            logger.error(f"查找文件失败: {str(e)}", exc_info=True)
            return {
                "files": [],
                "date": None,
                "message": f"查找文件时发生错误: {str(e)}"
            }
    
    def _get_file_type(self, filename: str) -> str:
        """根据文件名判断文件类型"""
        if not filename:
            return "unknown"
        
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        image_exts = ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif']
        doc_exts = ['pdf', 'docx', 'doc']
        
        if ext in image_exts:
            return "image"
        elif ext in doc_exts:
            return "document"
        else:
            return "unknown"
    
    def _extract_tool_call(self, text: str, messages: Union[List[Dict[str, str]], List[ChatMessage], None] = None, file_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """从 LLM 响应中提取工具调用
        
        Args:
            text: LLM 响应文本
            messages: 消息历史
            file_path: 指定的文件路径（如果提供，优先使用）
        """
        # 首先检查是否是通用处理请求，如果是且提供了文件路径，强制使用 n8n_workflow_trigger
        if file_path and messages:
            # 获取最后一条用户消息
            last_user_message = None
            for msg in reversed(messages):
                if isinstance(msg, ChatMessage):
                    if msg.role == "user":
                        last_user_message = msg.content
                        break
                elif isinstance(msg, dict):
                    if msg.get("role") == "user":
                        last_user_message = msg.get("content", "")
                        break
            
            if last_user_message:
                # 检测通用处理请求的关键词
                generic_processing_keywords = [
                    "处理一下", "处理", "处理文件", "处理合同",
                    "分析一下", "分析", "分析合同", "分析文件",
                    "审核一下", "审核", "审核合同", "审核文件",
                    "帮我处理", "帮我分析", "帮我审核",
                    "处理这个", "分析这个", "审核这个"
                ]
                
                # 检查是否包含通用处理关键词
                is_generic_request = any(keyword in last_user_message for keyword in generic_processing_keywords)
                
                # 如果没有明确指定具体任务（如"风险评估"、"合规校验"、"解析"、"提取内容"、"转为pdf"、"电子签名"等），则认为是通用请求
                specific_task_keywords = [
                    "风险评估", "合规校验", "合规检查", "解析", "提取文本", "提取内容", "OCR", "识别", "查询", "搜索",
                    "转为pdf", "转pdf", "转换为pdf", "转换成pdf", "转为", "转换", "转格式",
                    "电子签名", "数字签名", "签名", "签署", "验证签名", "签名工具"
                ]
                has_specific_task = any(keyword in last_user_message for keyword in specific_task_keywords)
                
                if is_generic_request and not has_specific_task:
                    # 强制使用 n8n_workflow_trigger
                    # 将 file_path 转换为相对路径（相对于 uploads 目录）
                    relative_path = _convert_to_relative_path(file_path)
                    logger.info(f"检测到通用处理请求，强制使用 n8n_workflow_trigger，文件: {relative_path}")
                    return {
                        "tool_name": "n8n_workflow_trigger",
                        "parameters": {
                            "file_path": relative_path
                        }
                    }
        
        # 尝试提取 JSON 格式的工具调用
        json_patterns = [
            r'```json\s*(\{.*?\})\s*```',  # ```json {...} ```
            r'```\s*(\{.*?\})\s*```',       # ``` {...} ```
            r'(\{\s*"tool_name".*?\})',     # 直接 JSON 对象
        ]
        
        for pattern in json_patterns:
            matches = re.finditer(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    tool_call = json.loads(match.group(1))
                    if "tool_name" in tool_call:
                        # 如果工具调用中缺少文件路径，尝试从提供的 file_path 或消息中提取
                        params = tool_call.get("parameters", {})
                        if not params.get("file_path") and not params.get("image_path") and not params.get("file_name"):
                            # 优先使用提供的 file_path
                            file_path_to_use = file_path
                            if file_path_to_use:
                                # 从 file_path 中提取文件名（用于 n8n_workflow_trigger）
                                file_name_from_path = file_path_to_use.split('/')[-1]
                                file_type = self._get_file_type(file_name_from_path)
                                
                                tool_name = tool_call.get("tool_name")
                                if tool_name == "ocr_parser" or (tool_name == "document_parser" and file_type == "image"):
                                    # 如果应该是OCR但工具名不对，或者文件是图片但用了文档解析工具，需要修正
                                    if file_type == "image":
                                        tool_call["tool_name"] = "ocr_parser"
                                        params["image_path"] = file_path_to_use
                                    elif file_type == "document":
                                        tool_call["tool_name"] = "document_parser"
                                        params["file_path"] = file_path_to_use
                                elif tool_name == "document_parser":
                                    params["file_path"] = file_path_to_use
                                elif tool_name == "ocr_parser":
                                    params["image_path"] = file_path_to_use
                                elif tool_name == "image_to_pdf":
                                    params["image_path"] = file_path_to_use
                                elif tool_name == "n8n_workflow_trigger":
                                    # n8n_workflow_trigger 使用 file_path 参数（相对路径）
                                    relative_path = _convert_to_relative_path(file_path_to_use)
                                    params["file_path"] = relative_path
                                tool_call["parameters"] = params
                            elif messages:
                                # 如果没有提供 file_path，尝试从消息中提取
                                file_name = self._extract_file_name_from_messages(messages)
                                if file_name:
                                    # 根据文件类型设置正确的参数名
                                    file_type = self._get_file_type(file_name)
                                    tool_name = tool_call.get("tool_name")
                                    if tool_name == "ocr_parser" or (tool_name == "document_parser" and file_type == "image"):
                                        # 如果应该是OCR但工具名不对，或者文件是图片但用了文档解析工具，需要修正
                                        if file_type == "image":
                                            tool_call["tool_name"] = "ocr_parser"
                                            params["image_path"] = file_name
                                        elif file_type == "document":
                                            tool_call["tool_name"] = "document_parser"
                                            params["file_path"] = file_name
                                    elif tool_name == "document_parser":
                                        params["file_path"] = file_name
                                    elif tool_name == "ocr_parser":
                                        params["image_path"] = file_name
                                    elif tool_name == "image_to_pdf":
                                        params["image_path"] = file_name
                                    elif tool_name == "n8n_workflow_trigger":
                                        # 向后兼容：如果只是文件名，尝试转换为相对路径
                                        relative_path = _convert_to_relative_path(file_name)
                                        params["file_path"] = relative_path
                                    tool_call["parameters"] = params
                        return tool_call
                except json.JSONDecodeError:
                    continue
        
        # 尝试从文本中提取工具名称和参数
        # 特别处理"转为pdf"、"转pdf"等格式转换任务
        if "转为pdf" in text or "转pdf" in text or "转换为pdf" in text or "转换成pdf" in text or ("转为" in text and "pdf" in text) or ("转换" in text and "pdf" in text):
            # 优先使用提供的 file_path，否则从文本或消息中提取
            file_path_to_use = file_path
            if not file_path_to_use:
                # 提取文件名
                file_name = None
                file_match = re.search(r'([^\s，,。\n]+\.(?:jpg|jpeg|png|bmp|tiff?))', text, re.IGNORECASE)
                if file_match:
                    file_name = file_match.group(1).strip()
                elif messages:
                    file_name = self._extract_file_name_from_messages(messages)
                
                if file_name:
                    file_type = self._get_file_type(file_name)
                    if file_type == "image":
                        return {
                            "tool_name": "image_to_pdf",
                            "parameters": {"image_path": file_name}
                        }
            else:
                # 从 file_path 中提取文件名用于判断类型
                file_name_from_path = file_path_to_use.split('/')[-1]
                file_type = self._get_file_type(file_name_from_path)
                if file_type == "image":
                    return {
                        "tool_name": "image_to_pdf",
                        "parameters": {"image_path": file_path_to_use}
                    }
        
        # 特别处理"解析"和"提取内容"任务 - 根据文件类型自动选择工具
        if "解析" in text or "提取文本" in text or "提取内容" in text or "识别" in text:
            # 优先使用提供的 file_path，否则从文本或消息中提取
            file_path_to_use = file_path
            if file_path_to_use:
                # 从 file_path 中提取文件名用于判断类型
                file_name_from_path = file_path_to_use.split('/')[-1]
                file_type = self._get_file_type(file_name_from_path)
                if file_type == "image":
                    return {
                        "tool_name": "ocr_parser",
                        "parameters": {"image_path": file_path_to_use}
                    }
                elif file_type == "document":
                    return {
                        "tool_name": "document_parser",
                        "parameters": {"file_path": file_path_to_use}
                    }
            else:
                # 提取文件名
                file_name = None
                file_match = re.search(r'([^\s，,。\n]+\.(?:pdf|docx?|jpg|jpeg|png|bmp|tiff?))', text, re.IGNORECASE)
                if file_match:
                    file_name = file_match.group(1).strip()
                elif messages:
                    file_name = self._extract_file_name_from_messages(messages)
                
                if file_name:
                    file_type = self._get_file_type(file_name)
                    if file_type == "image":
                        return {
                            "tool_name": "ocr_parser",
                            "parameters": {"image_path": file_name}
                        }
                    elif file_type == "document":
                        return {
                            "tool_name": "document_parser",
                            "parameters": {"file_path": file_name}
                        }
        
        # 检查是否提到了工具名称
        for tool_name in self.registry.list_tool_names():
            tool = self.registry.get(tool_name)
            if tool and (tool.info.display_name in text or tool_name in text):
                # 尝试提取参数
                params = {}
                # 优先使用提供的 file_path
                if file_path:
                    file_name_from_path = file_path.split('/')[-1]
                    file_type = self._get_file_type(file_name_from_path)
                    # 根据文件类型和工具类型设置参数
                    if tool_name == "ocr_parser":
                        params["image_path"] = file_path
                    elif tool_name == "image_to_pdf":
                        params["image_path"] = file_path
                    elif tool_name == "document_parser":
                        # 如果文件是图片但用户要求文档解析，应该用OCR
                        if file_type == "image":
                            return {
                                "tool_name": "ocr_parser",
                                "parameters": {"image_path": file_path}
                            }
                        params["file_path"] = file_path
                    elif tool_name == "n8n_workflow_trigger":
                        # n8n_workflow_trigger 使用 file_path 参数（相对路径）
                        relative_path = _convert_to_relative_path(file_path)
                        params["file_path"] = relative_path
                else:
                    # 提取文件名（常见参数）
                    file_match = re.search(r'(?:文件|合同|图片)[名名]*[：:]\s*([^\s，,。\n]+\.(?:pdf|docx?|jpg|jpeg|png|bmp|tiff?))', text, re.IGNORECASE)
                    if not file_match:
                        # 尝试从消息中提取
                        if messages:
                            file_name = self._extract_file_name_from_messages(messages)
                            if file_name:
                                file_type = self._get_file_type(file_name)
                                # 根据文件类型和工具类型设置参数
                                if tool_name == "ocr_parser":
                                    params["image_path"] = file_name
                                elif tool_name == "image_to_pdf":
                                    params["image_path"] = file_name
                                elif tool_name == "document_parser":
                                    # 如果文件是图片但用户要求文档解析，应该用OCR
                                    if file_type == "image":
                                        return {
                                            "tool_name": "ocr_parser",
                                            "parameters": {"image_path": file_name}
                                        }
                                    params["file_path"] = file_name
                                elif tool_name == "n8n_workflow_trigger":
                                    # 向后兼容：如果只是文件名，尝试转换为相对路径
                                    relative_path = _convert_to_relative_path(file_name)
                                    params["file_path"] = relative_path
                    else:
                        file_name = file_match.group(1).strip()
                        file_type = self._get_file_type(file_name)
                        # 根据文件类型和工具类型设置参数
                        if tool_name == "ocr_parser":
                            params["image_path"] = file_name
                        elif tool_name == "image_to_pdf":
                            params["image_path"] = file_name
                        elif tool_name == "document_parser":
                            # 如果文件是图片但用户要求文档解析，应该用OCR
                            if file_type == "image":
                                return {
                                    "tool_name": "ocr_parser",
                                    "parameters": {"image_path": file_name}
                                }
                            params["file_path"] = file_name
                        elif tool_name == "n8n_workflow_trigger":
                            # 向后兼容：如果只是文件名，尝试转换为相对路径
                            relative_path = _convert_to_relative_path(file_name)
                            params["file_path"] = relative_path
                
                if params or tool_name == "n8n_workflow_trigger":
                    return {
                        "tool_name": tool_name,
                        "parameters": params
                    }
        
        return None
    
    async def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具调用"""
        tool = self.registry.get(tool_name)
        if not tool:
            return {
                "success": False,
                "error": f"工具 '{tool_name}' 未找到"
            }
        
        try:
            logger.info(f"执行工具: {tool_name}, 参数: {parameters}")
            result = await tool.execute(**parameters)
            
            return {
                "success": result.success,
                "data": result.data,
                "error": result.error,
                "execution_time": result.execution_time
            }
        except Exception as e:
            logger.error(f"工具执行失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"工具执行失败: {str(e)}"
            }
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        enable_tools: bool = True,
        max_iterations: int = 3,
        file_name: Optional[str] = None,
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        与 LLM 对话，支持工具调用
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大 token 数
            enable_tools: 是否启用工具调用
            max_iterations: 最大迭代次数（工具调用链）
            file_name: 指定的文件名（已弃用，请使用 file_path，如果提供，直接查找该文件，不进行智能查找）
            file_path: 指定的文件路径（相对于 uploads 目录，如 "2025-12-29/test_contract.pdf"，优先使用）
        
        Returns:
            包含 message, tool_calls, usage 的字典
        """
        # 如果提供了 file_path，直接使用（不需要查找）
        # 如果只提供了 file_name（向后兼容），则查找文件获取 file_path
        file_path_to_use = file_path
        file_name_for_display = None
        
        if file_path_to_use:
            # 直接使用提供的 file_path，从路径中提取文件名用于显示
            file_name_for_display = file_path_to_use.split('/')[-1]
        elif file_name:
            # 向后兼容：如果只提供了 file_name，查找文件获取 file_path
            try:
                file_info = await self.file_service.get_file_info(file_name)
                if not file_info:
                    return {
                        "message": f"未找到文件 '{file_name}'。请检查文件名是否正确。",
                        "tool_calls": None,
                        "usage": None
                    }
                file_path_to_use = file_info.file_path
                file_name_for_display = file_info.file_name
            except Exception as e:
                logger.error(f"查找文件失败: {str(e)}", exc_info=True)
                return {
                    "message": f"查找文件时发生错误: {str(e)}",
                    "tool_calls": None,
                    "usage": None
                }
        
        # 如果提供了文件路径，在最后一条用户消息中添加文件信息
        if file_path_to_use and file_name_for_display:
            try:
                # 在最后一条用户消息中添加文件信息
                last_user_message = None
                for msg in reversed(messages):
                    if msg.get("role") == "user":
                        last_user_message = msg.get("content", "")
                        break
                
                if last_user_message:
                    # 修改最后一条消息，添加文件信息
                    messages = messages.copy()
                    for i in range(len(messages) - 1, -1, -1):
                        if messages[i].get("role") == "user":
                            messages[i] = {
                                "role": "user",
                                "content": f"{last_user_message}\n\n[系统提示：已指定文件 {file_name_for_display}，将使用此文件进行处理]"
                            }
                            break
            except Exception as e:
                logger.error(f"添加文件信息到消息失败: {str(e)}", exc_info=True)
        
        # 检查用户消息中是否提到文件但没有明确文件名（仅在未提供 file_name 时）
        last_user_message = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_message = msg.get("content", "")
                break
        
        # 检查是否是确认处理多个文件的回复（仅在未提供文件路径时）
        if last_user_message and enable_tools and not file_path_to_use:
            confirmation_keywords = ["是", "全部处理", "全部", "都处理", "yes", "all", "全部执行"]
            is_confirmation = any(keyword in last_user_message for keyword in confirmation_keywords)
            
            # 如果用户确认处理多个文件，查找之前的文件列表
            if is_confirmation:
                # 从之前的消息中查找文件列表提示
                for msg in reversed(messages):
                    if msg.get("role") == "assistant" and "找到" in msg.get("content", "") and "个文件" in msg.get("content", ""):
                        # 重新查找文件（使用之前的查询条件）
                        prev_user_msg = None
                        for prev_msg in reversed(messages):
                            if prev_msg.get("role") == "user" and prev_msg != msg:
                                prev_user_msg = prev_msg.get("content", "")
                                break
                        
                        if prev_user_msg:
                            file_search_result = await self._find_files_by_description(prev_user_msg)
                            if file_search_result["files"]:
                                # 处理所有文件（使用 N8N 工作流）
                                file_names = [f.file_name for f in file_search_result["files"]]
                                # 暂时只处理第一个文件，或者可以循环处理
                                # 这里先处理第一个，后续可以扩展为批量处理
                                file_name = file_names[0] if file_names else None
                                if file_name:
                                    last_user_message = f"处理文件 {file_name}"
                                    if len(file_names) > 1:
                                        last_user_message += f"\n\n[系统提示：将处理 {len(file_names)} 个文件，当前处理第一个：{file_name}]"
                                break
        
        # 如果用户提到处理文件但没有明确文件名，尝试查找文件（仅在未提供文件路径时）
        if last_user_message and enable_tools and not file_path_to_use:
            file_keywords = ["处理", "分析", "解析", "审核", "文件", "合同"]
            has_file_keyword = any(keyword in last_user_message for keyword in file_keywords)
            has_explicit_filename = bool(re.search(r'[^\s，,。\n]+\.(?:pdf|docx?|jpg|jpeg|png|bmp|tiff?)', last_user_message, re.IGNORECASE))
            
            # 排除确认回复
            confirmation_keywords = ["是", "全部处理", "全部", "都处理", "yes", "all"]
            is_confirmation_only = any(keyword in last_user_message for keyword in confirmation_keywords) and not has_file_keyword
            
            if has_file_keyword and not has_explicit_filename and not is_confirmation_only:
                # 查找文件
                file_search_result = await self._find_files_by_description(last_user_message)
                
                if file_search_result["files"]:
                    if len(file_search_result["files"]) == 1:
                        # 只有一个文件，自动使用
                        file_name = file_search_result["files"][0].file_name
                        # 在消息中添加文件信息
                        last_user_message = f"{last_user_message}\n\n[系统提示：已找到文件 {file_name}，将使用此文件进行处理]"
                    else:
                        # 多个文件，询问用户
                        return {
                            "message": file_search_result["message"],
                            "tool_calls": None,
                            "usage": None,
                            "requires_confirmation": True,
                            "files": [
                                {
                                    "file_name": f.file_name,
                                    "file_path": f.file_path,
                                    "upload_date": f.upload_date
                                }
                                for f in file_search_result["files"]
                            ]
                        }
                else:
                    # 未找到文件，直接返回提示
                    return {
                        "message": file_search_result["message"],
                        "tool_calls": None,
                        "usage": None
                    }
        
        # 构建消息列表
        chat_messages: List[ChatMessage] = []
        
        # 添加系统提示词（如果启用工具）
        if enable_tools:
            system_prompt = self._build_system_prompt()
            chat_messages.append(ChatMessage(role="system", content=system_prompt))
        
        # 添加用户消息（如果修改了最后一条消息，需要更新）
        for i, msg in enumerate(messages):
            if msg["role"] != "system" or not enable_tools:  # 如果启用工具，系统消息已在上面添加
                content = msg["content"]
                # 如果是最后一条用户消息且被修改过，使用修改后的内容
                if i == len(messages) - 1 and msg.get("role") == "user" and last_user_message and last_user_message != msg.get("content", ""):
                    content = last_user_message
                chat_messages.append(ChatMessage(role=msg["role"], content=content))
        
        tool_calls = []
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"第 {iteration} 轮对话")
            
            # 调用 LLM
            response = await self.llm_client.chat(
                chat_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            assistant_message = response.content
            chat_messages.append(ChatMessage(role="assistant", content=assistant_message))
            
            # 如果未启用工具，直接返回
            if not enable_tools:
                return {
                    "message": assistant_message,
                    "tool_calls": None,
                    "usage": {
                        "prompt_tokens": getattr(response, "prompt_tokens", None),
                        "completion_tokens": getattr(response, "completion_tokens", None),
                        "total_tokens": getattr(response, "total_tokens", None)
                    }
                }
            
            # 尝试提取工具调用（传入消息历史和文件路径）
            tool_call = self._extract_tool_call(assistant_message, chat_messages, file_path=file_path_to_use)
            
            if not tool_call:
                # 没有工具调用，返回最终答案
                return {
                    "message": assistant_message,
                    "tool_calls": tool_calls if tool_calls else None,
                    "usage": {
                        "prompt_tokens": getattr(response, "prompt_tokens", None),
                        "completion_tokens": getattr(response, "completion_tokens", None),
                        "total_tokens": getattr(response, "total_tokens", None)
                    }
                }
            
            # 执行工具调用
            tool_name = tool_call.get("tool_name")
            parameters = tool_call.get("parameters", {})
            
            logger.info(f"检测到工具调用: {tool_name}, 参数: {parameters}")
            
            tool_result = await self._execute_tool(tool_name, parameters)
            
            # 记录工具调用
            tool_calls.append({
                "tool_name": tool_name,
                "parameters": parameters,
                "result": tool_result
            })
            
            # 如果执行的是 n8n_workflow_trigger，返回 workflow_id 供前端轮询
            if tool_name == "n8n_workflow_trigger":
                if tool_result["success"]:
                    # 提取 workflow_id
                    result_data = tool_result.get("data", {})
                    workflow_id = result_data.get("workflow_id")
                    
                    # 返回 workflow_id，让前端可以轮询状态
                    if workflow_id:
                        final_message = f"工作流已启动，正在处理中。工作流 ID: {workflow_id}。前端将自动轮询状态。"
                    else:
                        final_message = "工作流已启动，正在处理中。"
                else:
                    # 生成错误消息
                    error_msg = tool_result.get('error', '未知错误')
                    final_message = f"触发工作流失败：{error_msg}"
                    workflow_id = None
                
                # 直接返回，包含 workflow_id
                return {
                    "message": final_message,
                    "workflow_id": workflow_id,
                    "tool_calls": tool_calls if tool_calls else None,
                    "usage": {
                        "prompt_tokens": getattr(response, "prompt_tokens", None),
                        "completion_tokens": getattr(response, "completion_tokens", None),
                        "total_tokens": getattr(response, "total_tokens", None)
                    }
                }
            
            # 将工具结果添加到消息中，让 LLM 继续处理（非 n8n_workflow_trigger 工具）
            if tool_result["success"]:
                result_data = tool_result.get('data', {})
                # 对于 OCR 和文档解析工具，提取文本内容以便 LLM 直接使用
                if tool_name == "ocr_parser":
                    recognized_text = result_data.get('recognized_text', '')
                    result_text = f"工具 '{tool_name}' 执行成功。\n识别出的文本内容：\n{recognized_text}\n\n请直接使用上述文本内容回答用户的问题，不要再调用工具。"
                elif tool_name == "document_parser":
                    text_content = result_data.get('text_content', '')
                    result_text = f"工具 '{tool_name}' 执行成功。\n提取的文档内容：\n{text_content}\n\n请直接使用上述文档内容回答用户的问题，不要再调用工具。"
                else:
                    result_text = f"工具 '{tool_name}' 执行成功。结果：\n{json.dumps(result_data, ensure_ascii=False, indent=2)}\n\n请根据工具执行结果，直接回答用户的问题，不要再调用工具。"
            else:
                result_text = f"工具 '{tool_name}' 执行失败。错误：{tool_result.get('error', '未知错误')}\n\n请向用户说明错误情况，不要再重复调用同一个工具。"
            
            # 添加工具调用和结果到消息中
            chat_messages.append(ChatMessage(
                role="user",
                content=f"工具执行结果：{result_text}"
            ))
            
            # 检查是否重复调用同一个工具（防止循环）
            recent_tool_calls = [tc.get("tool_name") for tc in tool_calls[-3:]]  # 检查最近3次调用
            if len(recent_tool_calls) >= 2 and recent_tool_calls[-1] == recent_tool_calls[-2] == tool_name:
                # 如果同一个工具被连续调用2次，强制返回结果
                logger.warning(f"检测到工具 '{tool_name}' 被重复调用，强制返回结果以避免循环")
                if tool_result["success"]:
                    if tool_name == "ocr_parser":
                        recognized_text = tool_result.get('data', {}).get('recognized_text', '')
                        final_message = f"已成功识别图片内容：\n\n{recognized_text}"
                    elif tool_name == "document_parser":
                        text_content = tool_result.get('data', {}).get('text_content', '')
                        final_message = f"已成功提取文档内容：\n\n{text_content}"
                    else:
                        final_message = f"工具 '{tool_name}' 执行成功。结果：\n{json.dumps(tool_result.get('data'), ensure_ascii=False, indent=2)}"
                else:
                    final_message = f"工具 '{tool_name}' 执行失败：{tool_result.get('error', '未知错误')}"
                
                return {
                    "message": final_message,
                    "tool_calls": tool_calls if tool_calls else None,
                    "usage": {
                        "prompt_tokens": getattr(response, "prompt_tokens", None),
                        "completion_tokens": getattr(response, "completion_tokens", None),
                        "total_tokens": getattr(response, "total_tokens", None)
                    }
                }
        
        # 达到最大迭代次数，返回最后的消息
        # 如果最后的消息是 JSON 格式的工具调用（说明工具调用链未完成），生成友好消息
        final_message = assistant_message
        if tool_calls and len(tool_calls) > 0:
            # 检查最后一条消息是否是 JSON 格式的工具调用
            is_json_tool_call = False
            try:
                parsed_json = json.loads(assistant_message.strip())
                if isinstance(parsed_json, dict) and "tool_name" in parsed_json:
                    is_json_tool_call = True
            except (json.JSONDecodeError, ValueError):
                # 检查是否包含工具调用的 JSON 代码块或模式
                if ("```json" in assistant_message and "tool_name" in assistant_message) or \
                   (assistant_message.strip().startswith("{") and "tool_name" in assistant_message and "parameters" in assistant_message):
                    is_json_tool_call = True
            
            if is_json_tool_call:
                # 获取最后一个工具调用的显示名称
                last_tool_name = tool_calls[-1].get("tool_name")
                tool = self.registry.get(last_tool_name)
                tool_display_name = tool.info.display_name if tool else last_tool_name
                final_message = f"正在使用 {tool_display_name} 处理您的请求..."
        
        return {
            "message": final_message,
            "tool_calls": tool_calls if tool_calls else None,
            "usage": {
                "prompt_tokens": getattr(response, "prompt_tokens", None),
                "completion_tokens": getattr(response, "completion_tokens", None),
                "total_tokens": getattr(response, "total_tokens", None)
            }
        }
    
    async def convert_risk_to_html(self, risk_data: Union[List[Dict[str, Any]], Dict[str, Any]]) -> Dict[str, Any]:
        """
        将风险判断结果转换为 HTML 格式，用于邮件发送
        
        Args:
            risk_data: 风险判断结果数据，支持多种格式：
                1. 直接发送 data 对象: {"success": true, "data": {...}}
                2. 包含 body 的对象: {"body": {"success": true, "data": {...}}}
                3. 数组格式: [{"body": {"success": true, "data": {...}}}]
        
        Returns:
            Dict[str, Any]: 包含 html_content 和 file_path 的字典
                - html_content: HTML 格式的邮件正文
                - file_path: 文件的相对路径（相对于 uploads 目录）
        """
        try:
            # 提取实际的风险数据，支持多种数据格式
            actual_data = None
            file_path = None  # 提取文件路径
            
            # 如果是列表格式
            if isinstance(risk_data, list):
                if len(risk_data) > 0:
                    first_item = risk_data[0]
                    # 检查是否包含 body 键
                    if "body" in first_item:
                        body = first_item["body"]
                        if isinstance(body, dict) and body.get("success") and body.get("data"):
                            actual_data = body["data"]
                            file_path = actual_data.get("file_path") if isinstance(actual_data, dict) else None
                    # 如果没有 body，直接检查是否有 data
                    elif "data" in first_item:
                        actual_data = first_item["data"]
                        file_path = actual_data.get("file_path") if isinstance(actual_data, dict) else None
                    # 如果第一个元素本身就是数据对象
                    elif "risks" in first_item or "overall_risk_level" in first_item:
                        actual_data = first_item
                        file_path = actual_data.get("file_path") if isinstance(actual_data, dict) else None
            # 如果是字典格式
            elif isinstance(risk_data, dict):
                # 格式1: 直接包含 data: {"success": true, "data": {...}}
                if "data" in risk_data and "success" in risk_data:
                    if risk_data.get("success") and risk_data.get("data"):
                        actual_data = risk_data["data"]
                        file_path = actual_data.get("file_path") if isinstance(actual_data, dict) else None
                # 格式2: 包含 body: {"body": {"success": true, "data": {...}}}
                elif "body" in risk_data:
                    body = risk_data["body"]
                    if isinstance(body, dict) and body.get("success") and body.get("data"):
                        actual_data = body["data"]
                        file_path = actual_data.get("file_path") if isinstance(actual_data, dict) else None
                # 格式3: 直接就是数据对象: {"overall_risk_level": "high", "risks": [...]}
                elif "risks" in risk_data or "overall_risk_level" in risk_data:
                    actual_data = risk_data
                    file_path = actual_data.get("file_path") if isinstance(actual_data, dict) else None
            
            if not actual_data:
                logger.warning(f"未能从输入数据中提取风险数据，输入数据类型: {type(risk_data)}, 内容: {str(risk_data)[:200]}")
                error_html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>错误</title>
</head>
<body>
    <p>未找到有效的风险数据。请检查数据格式是否正确。</p>
</body>
</html>"""
                return {
                    "html_content": error_html,
                    "file_path": file_path
                }
            
            # 构建系统提示词
            system_prompt = """你是一个专业的合同风险分析报告生成助手。你的任务是将风险评估的 JSON 数据转换为格式良好、专业的 HTML 邮件正文。

要求：
1. 生成完整的 HTML 文档结构（包含 <!DOCTYPE html>, <html>, <head>, <body> 标签）
2. 使用内联 CSS 样式，确保邮件客户端能够正确显示
3. 样式要专业、简洁、易读，适合商务邮件
4. 风险等级要用不同颜色标识（高风险-红色，中风险-橙色，低风险-黄色）
5. 结构清晰，包含：
   - 标题：合同风险评估报告
   - 总体风险等级（高/中/低）
   - 风险分析统计
   - 详细风险列表（按风险类型分组）
   - 每个风险包含：风险类型、严重程度、描述、问题条款、建议
6. 使用表格或列表展示，排版整齐
7. 颜色使用十六进制代码（如 #FF0000 表示红色）
8. 字体大小适中，适合邮件阅读
9. 不要包含任何 JavaScript 代码
10. HTML 代码要完整，可以直接作为邮件正文使用

请直接返回 HTML 代码，不要添加任何其他说明文字。"""
            
            # 构建用户提示词
            user_prompt = f"""请将以下风险评估数据转换为 HTML 格式的邮件正文：

{json.dumps(actual_data, ensure_ascii=False, indent=2)}

请生成完整的 HTML 代码。"""
            
            # 调用 LLM 生成 HTML
            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_prompt)
            ]
            
            response = await self.llm_client.chat(
                messages=messages,
                temperature=0.3,  # 使用较低的温度以获得更稳定的输出
                max_tokens=4000  # 设置较大的 token 限制以容纳完整的 HTML
            )
            
            html_content = response.content.strip()
            
            # 如果 LLM 返回的内容包含代码块标记，尝试提取 HTML
            if "```html" in html_content:
                # 提取 ```html 和 ``` 之间的内容
                match = re.search(r'```html\s*(.*?)\s*```', html_content, re.DOTALL)
                if match:
                    html_content = match.group(1).strip()
            elif "```" in html_content:
                # 如果没有 html 标记，尝试提取第一个代码块
                match = re.search(r'```\s*(.*?)\s*```', html_content, re.DOTALL)
                if match:
                    html_content = match.group(1).strip()
            
            # 验证是否是有效的 HTML（至少包含 <html> 或 <body> 标签）
            if "<html" not in html_content and "<body" not in html_content:
                # 如果没有完整的 HTML 结构，包装在基本结构中
                html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>合同风险评估报告</title>
</head>
<body>
{html_content}
</body>
</html>"""
            
            logger.info(f"风险数据已成功转换为 HTML 格式，文件路径: {file_path}")
            return {
                "html_content": html_content,
                "file_path": file_path
            }
        
        except Exception as e:
            logger.error(f"转换风险数据为 HTML 失败: {str(e)}", exc_info=True)
            # 返回一个简单的错误 HTML
            error_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>错误</title>
</head>
<body>
    <p style="color: red;">转换失败: {str(e)}</p>
</body>
</html>"""
            return {
                "html_content": error_html,
                "file_path": None
            }

