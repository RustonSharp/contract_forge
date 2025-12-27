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
        if self.region == "singapore":
            # 国际（新加坡）地域
            self.base_url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        else:
            # 中国大陆（北京）地域
            self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        
        if not self.api_key:
            print("⚠️ 警告: DASHSCOPE_API_KEY 或 MODEL_STUDIO_KEY 未设置，LLM 功能可能无法正常工作")
            print("💡 提示: 请在 backend/.env 文件中设置 DASHSCOPE_API_KEY 或 MODEL_STUDIO_KEY")
            print("💡 获取 API Key: https://help.aliyun.com/zh/model-studio/get-api-key")
            self.client = None
        else:
            # 清理 API Key（去除可能的空格和换行符）
            self.api_key = self.api_key.strip()
            
            # 初始化 OpenAI 客户端（兼容模式）
            try:
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                )
                # 检查 API Key 格式
                api_key_preview = self.api_key[:8] + "..." + self.api_key[-4:] if len(self.api_key) > 12 else "***"
                print(f"✅ LLM 服务已初始化，使用模型: {self.model}")
                print(f"✅ API Key 预览: {api_key_preview}")
                print(f"✅ API Key 长度: {len(self.api_key)} 字符")
                print(f"✅ 地域: {self.region} ({self.base_url})")
                
                # 检查 API Key 格式
                if not self.api_key.startswith('sk-'):
                    print("⚠️  警告: API Key 通常以 'sk-' 开头，请确认 API Key 格式正确")
                
                # 检查地域和 API Key 是否匹配
                if self.region == "singapore":
                    print("💡 提示: 使用新加坡地域，请确保 API Key 来自新加坡地域页面")
                else:
                    print("💡 提示: 使用北京地域，请确保 API Key 来自北京地域页面")
            except Exception as e:
                print(f"❌ 初始化 OpenAI 客户端失败: {str(e)}")
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
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # 解析响应
            if completion.choices and len(completion.choices) > 0:
                return completion.choices[0].message.content
            else:
                raise ValueError("API 响应中没有返回内容")
        except Exception as e:
            error_msg = f"调用阿里云百炼平台 API 失败: {str(e)}"
            print(f"❌ {error_msg}")
            
            # 如果是 401 错误，提供详细的排查建议
            if "401" in str(e) or "invalid_api_key" in str(e) or "Incorrect API key" in str(e):
                print("\n🔍 401 错误排查指南:")
                print("   1. 确认 API Key 来自阿里云百炼平台（不是 DashScope）")
                print("     获取地址: https://help.aliyun.com/zh/model-studio/get-api-key")
                print("   2. 检查 API Key 是否完整（没有截断）")
                print("   3. 确认 API Key 没有多余的空格、换行符或引号")
                print("   4. 验证 API Key 是否已激活且有足够余额")
                print("   5. 确认 API Key 有调用模型的权限")
                print("   6. 如果使用新加坡地域的 API Key，请设置 region='singapore'")
                print("\n💡 尝试以下解决方案:")
                print("   - 重新生成 API Key")
                print("   - 检查 .env 文件中的 API Key 格式（不要加引号）")
                print("   - 确认使用的是百炼平台的 API Key，不是 DashScope 的")
            
            # 如果是 404 错误（模型不存在），提供建议
            if "404" in str(e) or "model_not_found" in str(e) or "does not exist" in str(e):
                print("\n🔍 404 错误排查指南:")
                print(f"   当前使用的模型: {self.model}")
                print("   可能的原因：")
                print("   1. 模型名称不正确")
                print("   2. 您的账户没有访问该模型的权限")
                print("   3. 该模型在您使用的地域不可用")
                print("\n💡 尝试以下解决方案:")
                print("   1. 在 .env 文件中设置其他模型名称:")
                print("      DASHSCOPE_MODEL=qwen-plus      # 通义千问 Plus")
                print("      DASHSCOPE_MODEL=qwen-max       # 通义千问 Max")
                print("      DASHSCOPE_MODEL=qwen-turbo     # 通义千问 Turbo")
                print("      DASHSCOPE_MODEL=qwen-long      # 通义千问 Long（如果可用）")
                print("   2. 查看可用模型列表:")
                print("      https://help.aliyun.com/zh/model-studio/getting-started/models")
                print("   3. 确认您的账户有访问该模型的权限")
                print("   4. 检查模型是否在您使用的地域可用")
            
            print("\n💡 请参考文档: https://help.aliyun.com/zh/model-studio/developer-reference/error-code")
            raise Exception(error_msg)
        
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
请根据用户的问题提供准确、专业的回答。"""
        
        # 添加上下文信息
        context_info = ""
        if context:
            if context.get('task_id'):
                context_info += f"\n当前任务ID: {context.get('task_id')}"
            if context.get('current_step'):
                context_info += f"\n当前处理步骤: {context.get('current_step')}"
        
        # 构建 messages 格式
        messages = [
            {'role': 'system', 'content': system_prompt}
        ]
        
        # 添加上下文信息到用户消息
        user_content = message
        if context_info:
            user_content = f"{context_info}\n\n用户问题: {message}"
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


if __name__ == "__main__":
    # 测试 LLM 服务
    print("=" * 60)
    print("阿里云百炼平台 API 测试 (OpenAI 兼容接口)")
    print("=" * 60)
    print()
    
    # 从环境变量读取地域配置，默认为北京（与用户成功的配置一致）
    region = os.getenv("DASHSCOPE_REGION", "beijing")
    print(f"🌍 使用地域: {region}")
    print("💡 提示: 可通过设置环境变量 DASHSCOPE_REGION=beijing 或 singapore 来指定地域")
    print()
    
    llm_service = LLMService(region=region)
    
    # 检查 API Key 是否设置
    if not llm_service.api_key or not llm_service.client:
        print("❌ 错误: DASHSCOPE_API_KEY 或 MODEL_STUDIO_KEY 未设置")
        print("请在 backend/.env 文件中设置:")
        print("   DASHSCOPE_API_KEY=your_api_key")
        print("   或")
        print("   MODEL_STUDIO_KEY=your_api_key")
        print()
        print("💡 获取 API Key:")
        print("   https://help.aliyun.com/zh/model-studio/get-api-key")
        print()
        print("📖 参考文档:")
        print("   https://help.aliyun.com/zh/model-studio/developer-reference/error-code")
    else:
        print(f"✅ API Key 已设置")
        print(f"✅ Base URL: {llm_service.base_url}")
        print(f"✅ 模型: {llm_service.model}")
        print()
        
        # 验证 API Key 格式
        print("🔍 验证 API Key 格式...")
        verification = verify_api_key_format(llm_service.api_key)
        print(f"   长度: {verification['length']} 字符")
        print(f"   预览: {verification['preview']}")
        
        if verification['valid']:
            print("   ✅ API Key 格式检查通过")
        else:
            print("   ⚠️  API Key 格式问题:")
            for issue in verification['issues']:
                print(f"      - {issue}")
            if verification['suggestions']:
                print("   💡 建议:")
                for suggestion in verification['suggestions']:
                    print(f"      - {suggestion}")
        print()
        
        print("💡 如果遇到错误，请检查：")
        print("   1. API Key 格式是否正确（没有多余空格、换行符）")
        print("   2. API Key 是否有调用 qwen-long-latest 的权限")
        print("   3. API Key 是否已激活且有足够余额")
        print("   4. 网络连接是否正常")
        print("   5. 确认使用的是百炼平台的 API Key（不是 DashScope 的）")
        print()
        
        print("正在测试 API 调用...")
        print("-" * 60)
        try:
            result = llm_service.chat("你好，我是小明，我想咨询一下合同审批流程。")
            print("\n✅ 测试成功！")
            print("\n测试结果:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"\n❌ 测试失败: {str(e)}")
            print()
            print("🔧 排查建议:")
            print("   1. 检查 backend/.env 文件中的 DASHSCOPE_API_KEY 或 MODEL_STUDIO_KEY 是否正确")
            print("   2. 确认 API Key 来自阿里云百炼平台（不是 DashScope）")
            print("   3. 确认 API Key 和 Base URL 的地域匹配：")
            print(f"      - 当前使用地域: {llm_service.region}")
            print(f"      - 当前 Base URL: {llm_service.base_url}")
            print("      - 如果 API Key 来自新加坡地域页面，请确保使用新加坡地域")
            print("      - 如果 API Key 来自北京地域页面，请设置 DASHSCOPE_REGION=beijing")
            print("   4. 访问 https://help.aliyun.com/zh/model-studio/get-api-key 获取新的 API Key")
            print("   5. 查看错误码文档: https://help.aliyun.com/zh/model-studio/developer-reference/error-code")
    
