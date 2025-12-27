"""
大语言模型服务模块
支持 OpenAI、Anthropic 或本地模型
"""
import os
from typing import Dict, Any, Optional, List
import json


class LLMService:
    """大语言模型服务抽象类"""
    
    def __init__(self, provider: str = "openai"):
        self.provider = provider
        self.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        
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
        # TODO: 接入真实的大语言模型 API
        # 这里先用模拟实现
        
        # 根据消息内容生成智能回复
        if "审批" in message or "状态" in message or "哪一步" in message:
            response = "当前合同正在风险评估阶段，预计 2 分钟后完成。"
            suggested_actions = [
                {
                    "action": "查看详细日志",
                    "endpoint": f"/api/v1/logs/{context.get('task_id', '')}" if context else "/api/v1/logs"
                }
            ]
        elif "风险" in message or "问题" in message:
            response = "已检测到 2 处高风险项：违约金比例超过 30%，诉讼时效约定过短。建议查看详细报告。"
            suggested_actions = [
                {
                    "action": "查看风险报告",
                    "endpoint": "/api/v1/report"
                }
            ]
        elif "解析" in message or "失败" in message:
            response = "解析失败可能的原因：1) 文件格式不支持 2) 文件损坏 3) 网络问题。建议：1) 检查文件格式 2) 重新上传文件 3) 联系技术支持"
            suggested_actions = [
                {
                    "action": "重新上传",
                    "endpoint": "/api/v1/audit"
                }
            ]
        else:
            response = f"我理解您的问题：{message}。我可以帮您查询合同处理状态、分析风险、生成报告等。请告诉我您需要什么帮助？"
            suggested_actions = []
        
        return {
            "response": response,
            "suggested_actions": suggested_actions,
            "confidence": 0.95
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
        
        # 生成 Markdown 报告
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

