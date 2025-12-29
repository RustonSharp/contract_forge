"""
LLM 对话服务层
实现工具调用逻辑，让 LLM 可以根据用户需求调用工具
"""

import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from backend.utils.llm import get_llm_client, ChatMessage
from backend.service.tools.registry import get_registry
from backend.service.tools.initialize import initialize_default_tools
from backend.service.files.service import FileService
from backend.utils.logger import get_logger

logger = get_logger(__name__)


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

【规则 2 - 明确指定任务时根据文件类型选择工具】
如果用户明确要求执行特定任务，必须根据文件类型和任务类型选择正确的工具：

**解析任务**：
- 如果文件是图片格式（.jpg, .jpeg, .png, .bmp）→ 使用 ocr_parser（OCR解析工具）
- 如果文件是文档格式（.pdf, .docx, .doc）→ 使用 document_parser（文档解析工具）
- 如果用户只说"解析"但没有指定文件，需要从上下文或对话中提取文件名

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

【规则 4 - 仅提问时直接回答】
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
用户："解析这个合同图片" 或 "解析 test_contract.jpg"
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
用户："解析文档 test.pdf" 或 "解析这个PDF合同"
你的响应：
```json
{{
    "tool_name": "document_parser",
    "parameters": {{
        "file_path": "test.pdf"
    }}
}}
```

示例 4 - 其他明确任务：
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

示例 5 - 仅提问：
用户："什么是合同？"
你的响应：直接回答，不调用工具。

═══════════════════════════════════════════════════════════════
重要提示 - 文件类型识别
═══════════════════════════════════════════════════════════════

当用户要求"解析"文件时，必须根据文件扩展名选择工具：
- 图片文件（.jpg, .jpeg, .png, .bmp, .tiff, .tif）→ ocr_parser
- 文档文件（.pdf, .docx, .doc）→ document_parser

如果用户没有提供文件名，尝试从对话历史中提取最近提到的文件名。

═══════════════════════════════════════════════════════════════

请根据用户的需求，智能地选择和使用合适的工具。记住：当用户要求处理文件但没有指定具体工具时，优先使用 n8n_workflow_trigger！
"""
    
    def _extract_file_name_from_messages(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """从消息历史中提取文件名"""
        # 从最近的用户消息中查找文件名
        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content", "")
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
    
    def _extract_tool_call(self, text: str, messages: List[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """从 LLM 响应中提取工具调用"""
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
                        # 如果工具调用中缺少文件名，尝试从消息中提取
                        params = tool_call.get("parameters", {})
                        if messages and not params.get("file_path") and not params.get("image_path") and not params.get("file_name"):
                            file_name = self._extract_file_name_from_messages(messages)
                            if file_name:
                                # 根据文件类型设置正确的参数名
                                file_type = self._get_file_type(file_name)
                                if tool_call.get("tool_name") == "ocr_parser" or (tool_call.get("tool_name") == "document_parser" and file_type == "image"):
                                    # 如果应该是OCR但工具名不对，或者文件是图片但用了文档解析工具，需要修正
                                    if file_type == "image":
                                        tool_call["tool_name"] = "ocr_parser"
                                        params["image_path"] = file_name
                                    elif file_type == "document":
                                        tool_call["tool_name"] = "document_parser"
                                        params["file_path"] = file_name
                                elif tool_call.get("tool_name") == "document_parser":
                                    params["file_path"] = file_name
                                elif tool_call.get("tool_name") == "ocr_parser":
                                    params["image_path"] = file_name
                                elif tool_call.get("tool_name") == "n8n_workflow_trigger":
                                    params["file_name"] = file_name
                                tool_call["parameters"] = params
                        return tool_call
                except json.JSONDecodeError:
                    continue
        
        # 尝试从文本中提取工具名称和参数
        # 特别处理"解析"任务 - 根据文件类型自动选择工具
        if "解析" in text or "提取文本" in text or "识别" in text:
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
                            elif tool_name == "document_parser":
                                # 如果文件是图片但用户要求文档解析，应该用OCR
                                if file_type == "image":
                                    return {
                                        "tool_name": "ocr_parser",
                                        "parameters": {"image_path": file_name}
                                    }
                                params["file_path"] = file_name
                            elif tool_name == "n8n_workflow_trigger":
                                params["file_name"] = file_name
                else:
                    file_name = file_match.group(1).strip()
                    file_type = self._get_file_type(file_name)
                    # 根据文件类型和工具类型设置参数
                    if tool_name == "ocr_parser":
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
                        params["file_name"] = file_name
                
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
        max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        与 LLM 对话，支持工具调用
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大 token 数
            enable_tools: 是否启用工具调用
            max_iterations: 最大迭代次数（工具调用链）
        
        Returns:
            包含 message, tool_calls, usage 的字典
        """
        # 检查用户消息中是否提到文件但没有明确文件名
        last_user_message = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_message = msg.get("content", "")
                break
        
        # 检查是否是确认处理多个文件的回复
        if last_user_message and enable_tools:
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
        
        # 如果用户提到处理文件但没有明确文件名，尝试查找文件
        if last_user_message and enable_tools:
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
            
            # 尝试提取工具调用（传入消息历史以便提取文件名）
            tool_call = self._extract_tool_call(assistant_message, chat_messages)
            
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
            
            # 将工具结果添加到消息中，让 LLM 继续处理
            if tool_result["success"]:
                result_text = f"工具 '{tool_name}' 执行成功。结果：\n{json.dumps(tool_result.get('data'), ensure_ascii=False, indent=2)}"
            else:
                result_text = f"工具 '{tool_name}' 执行失败。错误：{tool_result.get('error', '未知错误')}"
            
            # 添加工具调用和结果到消息中
            chat_messages.append(ChatMessage(
                role="user",
                content=f"工具执行结果：{result_text}\n\n请根据工具执行结果，继续回答用户的问题。"
            ))
        
        # 达到最大迭代次数，返回最后的消息
        return {
            "message": assistant_message,
            "tool_calls": tool_calls if tool_calls else None,
            "usage": {
                "prompt_tokens": getattr(response, "prompt_tokens", None),
                "completion_tokens": getattr(response, "completion_tokens", None),
                "total_tokens": getattr(response, "total_tokens", None)
            }
        }

