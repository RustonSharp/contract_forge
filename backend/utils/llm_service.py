"""
大语言模型服务模块
支持阿里云百炼平台（qwen-long-latest 模型）
使用 OpenAI 兼容接口
"""
import os
from typing import Dict, Any, Optional, List
import json
from openai import OpenAI
from dotenv import load_dotenv
from .context_manager import context_manager

# 加载 .env 文件（从 backend 目录）
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path=env_path)


class LLMService:
    """大语言模型服务类 - 使用阿里云百炼平台（OpenAI 兼容接口）"""
    
    def __init__(self, provider: str = "dashscope", region: Optional[str] = None):
        """
        初始化 LLM 服务
        
        Args:
            provider: 服务提供商（默认 dashscope）
            region: 地域，可选 "beijing" 或 "singapore"
                   如果为 None，则从环境变量 DASHSCOPE_REGION 读取，默认为 "beijing"（北京地域）
        """
        self.provider = provider
        # 支持两种环境变量名：DASHSCOPE_API_KEY 或 MODEL_STUDIO_KEY
        self.api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("MODEL_STUDIO_KEY")
        # 支持通过环境变量配置模型名称，默认为 qwen-long-latest
        # 如果该模型不可用，可以尝试：qwen-plus, qwen-max, qwen-turbo 等
        self.model = os.getenv("DASHSCOPE_MODEL", "qwen-long-latest")
        
        # 根据地域设置 base_url
        # 如果未指定 region，从环境变量读取，默认为 "beijing"（北京地域）
        if region is None:
            region = os.getenv("DASHSCOPE_REGION", "beijing")
        
        self.region = region.lower()
        
        # 根据地域设置 base_url（OpenAI 兼容模式）
        # 参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code
        self.base_url = (
            "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
            if self.region == "singapore"
            else "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        if not self.api_key:
            self.client = None
            return
        
        self.api_key = self.api_key.strip()
        
        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        except Exception:
            self.client = None
    
    def _call_dashscope_api(self, messages: List[Dict[str, str]], max_tokens: int = 2000, temperature: float = 0.7) -> str:
        """
        调用阿里云百炼平台 API（使用 OpenAI 兼容接口）
        
        参考文档: https://help.aliyun.com/zh/model-studio/developer-reference/error-code
        
        Args:
            messages: 消息列表，格式为 [{'role': 'system/user/assistant', 'content': '...'}, ...]
            max_tokens: 最大生成 token 数
            temperature: 温度参数
            
        Returns:
            模型生成的文本
        """
        if not self.client:
            raise ValueError("DASHSCOPE_API_KEY 或 MODEL_STUDIO_KEY 未设置，无法调用 API")
        
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        if completion.choices and len(completion.choices) > 0:
            return completion.choices[0].message.content
        
        raise ValueError("API 响应中没有返回内容")
        
    def chat(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        自然语言交互
        
        Args:
            message: 用户消息
            context: 上下文信息（task_id, user_id, session_id 等）
            
        Returns:
            {
                "response": "回复内容",
                "suggested_actions": [...],
                "confidence": 0.95
            }
        """
        # 构建提示词
        system_prompt = """你是一个专业的合同审计助手，能够帮助用户查询合同处理状态、分析风险、生成报告等。
请根据用户的问题提供准确、专业的回答。如果提供了合同内容，请基于合同内容进行详细分析。"""
        
        # 从 context_manager 获取文件内容
        task_context = None
        if context and context.get('task_id'):
            task_context = context_manager.get_context(context.get('task_id'))
        
        # 构建上下文信息
        context_info = ""
        if context:
            if context.get('task_id'):
                context_info += f"\n当前任务ID: {context.get('task_id')}"
            if context.get('current_step'):
                context_info += f"\n当前处理步骤: {context.get('current_step')}"
        
        # 如果有任务上下文，添加合同内容
        contract_content = ""
        if task_context:
            # 添加合同文本（限制长度，避免超出 token 限制）
            raw_text = task_context.get('raw_text', '')
            if raw_text:
                # 如果文本太长，只取前8000字符
                text_preview = raw_text[:8000] if len(raw_text) > 8000 else raw_text
                contract_content += f"\n\n【合同内容】\n{text_preview}"
                if len(raw_text) > 8000:
                    contract_content += f"\n\n（注：合同内容较长，此处仅显示前8000字符，共{len(raw_text)}字符）"
            
            # 添加结构化数据摘要
            structured_data = task_context.get('structured_data')
            if structured_data:
                contract_content += f"\n\n【结构化信息摘要】\n{json.dumps(structured_data, ensure_ascii=False, indent=2)[:2000]}"
            
            # 添加已识别的风险
            risks = task_context.get('risks', [])
            if risks:
                contract_content += f"\n\n【已识别的风险点（共{len(risks)}项）】\n"
                for i, risk in enumerate(risks[:5], 1):  # 只显示前5个风险
                    contract_content += f"{i}. [{risk.get('risk_level', 'Unknown')}] {risk.get('risk_desc', '')}\n"
                if len(risks) > 5:
                    contract_content += f"... 还有 {len(risks) - 5} 个风险点\n"
            
            # 添加法规依据
            referenced_laws = task_context.get('referenced_laws', [])
            if referenced_laws:
                contract_content += f"\n\n【相关法规依据（共{len(referenced_laws)}条）】\n"
                for i, law in enumerate(referenced_laws[:3], 1):  # 只显示前3条
                    title = law.get('title', '未知法规')
                    contract_content += f"{i}. {title}\n"
                if len(referenced_laws) > 3:
                    contract_content += f"... 还有 {len(referenced_laws) - 3} 条法规\n"
        
        # 构建 messages 格式
        messages = [
            {'role': 'system', 'content': system_prompt}
        ]
        
        # 添加上下文信息和合同内容到用户消息
        user_content = message
        if context_info or contract_content:
            user_content = ""
            if context_info:
                user_content += context_info
            if contract_content:
                user_content += contract_content
            user_content += f"\n\n【用户问题】\n{message}"
        
        messages.append({'role': 'user', 'content': user_content})
        
        try:
            # 调用阿里云百炼平台 API
            response_text = self._call_dashscope_api(messages, max_tokens=1000, temperature=0.7)
            
            # 根据消息内容生成建议操作
            suggested_actions = []
            if context and context.get('task_id'):
                if "审批" in message or "状态" in message or "哪一步" in message:
                    suggested_actions.append({
                        "action": "查看详细日志",
                        "endpoint": f"/api/v1/logs/{context.get('task_id', '')}"
                    })
                elif "风险" in message or "问题" in message:
                    suggested_actions.append({
                        "action": "查看风险报告",
                        "endpoint": "/api/v1/report"
                    })
            
            return {
                "response": response_text,
                "suggested_actions": suggested_actions,
                "confidence": 0.95
            }
        except Exception as e:
            # 如果 API 调用失败，返回错误信息
            print(f"LLM API 调用失败: {str(e)}")
            return {
                "response": f"抱歉，处理您的请求时出现错误: {str(e)}",
                "suggested_actions": [],
                "confidence": 0.0
            }
    
    def generate_report(self, task_id: str, audit_data: Dict[str, Any], 
                       template: str = "detailed", format: str = "markdown") -> Dict[str, Any]:
        """
        生成智能报告
        
        Args:
            task_id: 任务 ID
            audit_data: 审计数据（包含 risks, overall_score 等）
            template: 报告模板（simple/detailed）
            format: 输出格式（markdown/pdf/word）
            
        Returns:
            {
                "report": "报告内容",
                "summary": "摘要",
                "generated_at": "时间戳"
            }
        """
        risks = audit_data.get("risks", [])
        overall_score = audit_data.get("overall_score", 100)
        
        # 构建用于 LLM 的提示词
        risks_text = ""
        if risks:
            for i, risk in enumerate(risks, 1):
                risks_text += f"\n风险项 {i}:\n"
                risks_text += f"- 风险等级: {risk.get('risk_level', 'Unknown')}\n"
                risks_text += f"- 条款内容: {risk.get('clause_content', 'N/A')}\n"
                risks_text += f"- 风险描述: {risk.get('risk_desc', 'N/A')}\n"
                risks_text += f"- 修改建议: {risk.get('suggestion', 'N/A')}\n"
                risks_text += f"- 法律依据: {risk.get('reference', 'N/A')}\n"
        else:
            risks_text = "未发现明显的合规风险。"
        
        # 构建提示词
        prompt = f"""请根据以下合同审计数据生成一份专业的合同审计报告（Markdown 格式）。

任务 ID: {task_id}
合规评分: {overall_score}/100
生成时间: {audit_data.get('generated_at', 'N/A')}

风险详情:
{risks_text}

请生成一份结构化的 Markdown 报告，包括：
1. 报告标题和基本信息
2. 概述部分（根据合规评分给出整体评价）
3. 风险详情部分（详细列出所有风险项）
4. 建议部分（根据风险情况给出具体建议）

要求：
- 使用专业的法律术语
- 报告要清晰、准确、专业
- 格式为 Markdown
- 如果合规评分 >= 80，评价为"整体合规性良好，风险较低"
- 如果合规评分 >= 60，评价为"存在中等风险，建议进行部分修改"
- 如果合规评分 < 60，评价为"存在高风险，需要法务人员介入审查"
"""
        
        # 构建 messages 格式
        messages = [
            {'role': 'system', 'content': '你是一个专业的合同审计报告生成助手，擅长生成结构清晰、专业准确的合同审计报告。'},
            {'role': 'user', 'content': prompt}
        ]
        
        try:
            # 调用 LLM 生成报告
            report_content = self._call_dashscope_api(messages, max_tokens=3000, temperature=0.3)
            
            # 生成摘要
            high_risks = [r for r in risks if r.get('risk_level') == 'High']
            summary = f"共检测到 {len(risks)} 处风险项，其中高风险 {len(high_risks)} 处。"
            
            return {
                "report": report_content,
                "summary": summary,
                "generated_at": audit_data.get('generated_at', 'N/A')
            }
        except Exception as e:
            # 如果 API 调用失败，使用备用方案生成报告
            print(f"LLM API 调用失败，使用备用方案: {str(e)}")
            
            # 生成 Markdown 报告（备用方案）
            report_lines = [
                "# 合同审计报告\n",
                f"**任务 ID**: {task_id}\n",
                f"**合规评分**: {overall_score}/100\n",
                f"**生成时间**: {audit_data.get('generated_at', 'N/A')}\n",
                "\n## 概述\n"
            ]
            
            if overall_score >= 80:
                report_lines.append("该合同整体合规性良好，风险较低。\n")
            elif overall_score >= 60:
                report_lines.append("该合同存在中等风险，建议进行部分修改。\n")
            else:
                report_lines.append("该合同存在高风险，需要法务人员介入审查。\n")
            
            if risks:
                report_lines.append("\n## 风险详情\n")
                for i, risk in enumerate(risks, 1):
                    report_lines.append(f"\n### 风险项 {i}\n")
                    report_lines.append(f"- **风险等级**: {risk.get('risk_level', 'Unknown')}\n")
                    report_lines.append(f"- **条款内容**: {risk.get('clause_content', 'N/A')}\n")
                    report_lines.append(f"- **风险描述**: {risk.get('risk_desc', 'N/A')}\n")
                    report_lines.append(f"- **修改建议**: {risk.get('suggestion', 'N/A')}\n")
                    report_lines.append(f"- **法律依据**: {risk.get('reference', 'N/A')}\n")
            else:
                report_lines.append("\n## 风险详情\n")
                report_lines.append("未发现明显的合规风险。\n")
            
            report_lines.append("\n## 建议\n")
            if risks:
                report_lines.append("1. 根据上述风险项进行合同条款修改\n")
                report_lines.append("2. 重新提交审查以确保合规性\n")
            else:
                report_lines.append("合同可以进入下一审批流程。\n")
            
            report_content = "".join(report_lines)
            
            # 生成摘要
            high_risks = [r for r in risks if r.get('risk_level') == 'High']
            summary = f"共检测到 {len(risks)} 处风险项，其中高风险 {len(high_risks)} 处。"
            
            return {
                "report": report_content,
                "summary": summary,
                "generated_at": audit_data.get('generated_at', 'N/A')
            }
    
    def analyze_logs(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析执行日志，生成诊断报告
        
        Args:
            logs: 日志列表
            
        Returns:
            {
                "summary": "执行摘要",
                "issues": ["问题1", "问题2"],
                "suggestions": ["建议1", "建议2"]
            }
        """
        # 分析日志
        total_steps = len(logs)
        completed_steps = len([l for l in logs if l.get('status') == 'completed'])
        failed_steps = len([l for l in logs if l.get('status') == 'failed'])
        
        summary = f"共执行 {total_steps} 个步骤，完成 {completed_steps} 个，失败 {failed_steps} 个。"
        
        issues = []
        suggestions = []
        
        if failed_steps > 0:
            issues.append(f"有 {failed_steps} 个步骤执行失败")
            suggestions.append("检查失败步骤的错误信息，考虑重试或使用备用工具")
        
        slow_steps = [l for l in logs if l.get('duration', 0) > 60]
        if slow_steps:
            issues.append(f"有 {len(slow_steps)} 个步骤执行时间超过 60 秒")
            suggestions.append("优化慢步骤的性能，考虑并行处理")
        
        return {
            "summary": summary,
            "issues": issues,
            "suggestions": suggestions
        }


def verify_api_key_format(api_key: str) -> Dict[str, Any]:
    """验证 API Key 格式"""
    issues = []
    suggestions = []
    
    if not api_key:
        issues.append("API Key 为空")
        return {"valid": False, "issues": issues, "suggestions": suggestions}
    
    # 检查长度
    if len(api_key) < 20:
        issues.append(f"API Key 长度过短 ({len(api_key)} 字符)")
        suggestions.append("API Key 通常至少 20 字符，请检查是否完整")
    
    # 检查是否包含空格
    if ' ' in api_key:
        issues.append("API Key 包含空格")
        suggestions.append("请去除 API Key 中的所有空格")
    
    # 检查是否包含换行符
    if '\n' in api_key or '\r' in api_key:
        issues.append("API Key 包含换行符")
        suggestions.append("请去除 API Key 中的所有换行符")
    
    # 检查是否以 sk- 开头（常见格式）
    if not api_key.startswith('sk-'):
        issues.append("API Key 不以 'sk-' 开头")
        suggestions.append("大多数 API Key 以 'sk-' 开头，请确认格式正确")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "suggestions": suggestions,
        "length": len(api_key),
        "preview": api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
    }


