"""
LangGraph 流程定义
支持条件分支、重试机制、备用工具切换
"""
from langgraph.graph import StateGraph, END
from typing import Literal
import os

from .state import ContractState
from ..utils.tool_registry import registry
from ..utils.retry_handler import RetryHandler
from ..utils.compliance_rules import compliance_checker
from ..utils.llm_service import LLMService
import os


# 初始化重试处理器
retry_handler = RetryHandler(max_retries=2, retry_interval=30, timeout=30)

# 初始化 LLM 服务（从环境变量读取地域配置，默认为北京）
region = os.getenv("DASHSCOPE_REGION", "beijing")
llm_service = LLMService(region=region)


def should_use_ocr(state: ContractState) -> Literal["parse", "ocr"]:
    """
    格式分支：根据文件格式选择解析工具
    """
    file_path = state.get("file_path", "")
    if not file_path:
        return "parse"
    
    file_ext = os.path.splitext(file_path)[1].lower()
    image_exts = [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]
    
    if file_ext in image_exts:
        return "ocr"
    return "parse"


def parse_node(state: ContractState):
    """解析节点：根据文件格式选择解析工具或 OCR"""
    # 判断文件格式
    file_path = state.get("file_path", "")
    file_ext = os.path.splitext(file_path)[1].lower() if file_path else ""
    image_exts = [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]
    
    # 如果是图片格式，使用 OCR
    if file_ext in image_exts:
        print("--- 检测到图片格式，使用 OCR 工具 ---")
        return _run_ocr(state)
    
    # 否则使用常规文档解析工具
    print("--- 正在解析文档（常规工具）---")
    
    parser = registry.get("ContractParser")
    if not parser:
        return {"error": "文档解析工具未注册", "current_step": "failed"}
    
    # 使用重试机制和备用工具
    result = registry.run_with_fallback(
        "ContractParser",
        {"file_path": state["file_path"]},
        {},
        max_retries=2
    )
    
    if result.get("status") != "success":
        # 如果常规解析失败，尝试 OCR 作为备用
        print("--- 常规解析失败，尝试 OCR 工具 ---")
        return _run_ocr(state)
    
    return {
        "raw_text": result["data"]["raw_text"],
        "structured_data": result["data"].get("structured_data"),
        "parse_tool_used": "ContractParser",
        "current_step": "retrieving",
        "retrieve_attempts": 0
    }


def _run_ocr(state: ContractState):
    """OCR 节点：使用 OCR 工具解析图片"""
    print("--- 正在解析文档（OCR 工具）---")
    
    ocr = registry.get("OCRParser")
    if not ocr:
        return {"error": "OCR 工具未注册", "current_step": "failed"}
    
    # 使用重试机制和备用工具
    result = registry.run_with_fallback(
        "OCRParser",
        {"file_path": state["file_path"]},
        {},
        max_retries=2
    )
    
    if result.get("status") != "success":
        return {"error": result.get("message", "OCR 识别失败"), "current_step": "failed"}
    
    return {
        "raw_text": result["data"]["raw_text"],
        "structured_data": result["data"].get("structured_data"),
        "parse_tool_used": "OCRParser",
        "current_step": "retrieving",
        "retrieve_attempts": 0
    }


def retrieve_node(state: ContractState):
    """检索节点：检索相关法律法规"""
    print("--- 正在检索法律依据 ---")
    
    retriever = registry.get("LawRetriever")
    if not retriever:
        return {"error": "法规检索工具未注册", "current_step": "failed"}
    
    raw_text = state.get("raw_text", "")
    if not raw_text:
        return {"error": "缺少合同文本", "current_step": "failed"}
    
    # 使用 LLM 提取关键词
    attempts = state.get("retrieve_attempts", 0)
    query = ""
    
    try:
        # 构建提示词，让 LLM 提取与法律检索相关的关键词
        prompt = f"""请从以下合同文本中提取用于法律检索的关键词。这些关键词应该与合同中的法律条款、风险点、合规要求相关。

合同文本（前1000字）:
{raw_text[:1000]}

请提取5-10个最重要的关键词，用逗号分隔，用于检索相关的法律法规。只返回关键词，不要其他内容。

关键词:"""
        
        # 构建 messages 格式
        messages = [
            {'role': 'user', 'content': prompt}
        ]
        
        # 调用 LLM 提取关键词
        keywords_text = llm_service._call_dashscope_api(messages, max_tokens=200, temperature=0.3)
        # 清理关键词文本（去除可能的换行和多余空格）
        query = keywords_text.strip().replace('\n', ' ').replace('，', ',').replace('、', ',')
        print(f"--- LLM 提取的关键词: {query} ---")
    except Exception as e:
        print(f"⚠️ LLM 提取关键词失败: {str(e)}，使用备用方案（文本前100字）")
        # 如果 LLM 调用失败，使用备用方案
        query = raw_text[:100] if raw_text else ""
    
    # 使用重试机制
    def _retrieve():
        return retriever.run({"keywords": query}, {})
    
    result = retry_handler.execute_with_retry(_retrieve)
    
    if result.get("status") != "success":
        return {"error": result.get("message", "检索失败"), "current_step": "failed"}
    
    laws = result["data"].get("laws", [])
    total = result["data"].get("total", 0)
    
    # 检索分支：如果结果不足，重试
    attempts = attempts + 1
    
    if total < 3 and attempts < 3:
        print(f"⚠️ 检索结果不足（{total} 条），尝试使用 LLM 重新提取关键词后重试（第 {attempts} 次）...")
        try:
            # 使用更长的文本重新提取关键词
            extended_prompt = f"""请从以下合同文本中提取用于法律检索的关键词。这些关键词应该与合同中的法律条款、风险点、合规要求相关。

合同文本（前2000字）:
{raw_text[:2000]}

请提取10-15个最重要的关键词，用逗号分隔，用于检索相关的法律法规。只返回关键词，不要其他内容。

关键词:"""
            # 构建 messages 格式
            extended_messages = [
                {'role': 'user', 'content': extended_prompt}
            ]
            extended_keywords = llm_service._call_dashscope_api(extended_messages, max_tokens=300, temperature=0.3)
            extended_query = extended_keywords.strip().replace('\n', ' ').replace('，', ',').replace('、', ',')
            print(f"--- LLM 重新提取的关键词: {extended_query} ---")
            result = retriever.run({"keywords": extended_query}, {})
            laws = result.get("data", {}).get("laws", [])
            total = result.get("data", {}).get("total", 0)
            attempts += 1
        except Exception as e:
            print(f"⚠️ LLM 重新提取关键词失败: {str(e)}")
            # 使用更长的原始文本作为备用
            extended_query = raw_text[:200] if len(raw_text) > 200 else raw_text
            result = retriever.run({"keywords": extended_query}, {})
            laws = result.get("data", {}).get("laws", [])
            total = result.get("data", {}).get("total", 0)
            attempts += 1
    
    if total < 3 and attempts >= 3:
        print("⚠️ 检索结果仍然不足，将通过前端提示人工补充法规")
        # 继续流程，但标记需要人工介入
    
    return {
        "referenced_laws": laws,
        "retrieve_attempts": attempts,
        "current_step": "evaluating"
    }


def evaluate_node(state: ContractState):
    """评估节点：进行风险评估和合规检查"""
    print("--- 正在进行风险评估 ---")
    
    evaluator = registry.get("RiskEvaluator")
    if not evaluator:
        return {"error": "风险评估工具未注册", "current_step": "failed"}
    
    raw_text = state.get("raw_text", "")
    structured_data = state.get("structured_data", {})
    referenced_laws = state.get("referenced_laws", [])
    
    # 使用合规规则检查器
    compliance_risks = compliance_checker.check_all(raw_text, structured_data)
    
    # 计算合规评分
    overall_score = compliance_checker.calculate_overall_score(compliance_risks)
    
    # 确定整体风险等级
    high_risks = [r for r in compliance_risks if r.get("risk_level") == "High"]
    overall_risk_level = "High" if high_risks else "Medium" if compliance_risks else "Low"
    
    # 转换为 RiskItem 格式
    risks = []
    for risk in compliance_risks:
        risks.append({
            "clause_content": risk.get("clause_content", ""),
            "risk_level": risk.get("risk_level", "Medium"),
            "risk_desc": risk.get("risk_desc", ""),
            "suggestion": risk.get("suggestion", ""),
            "reference": risk.get("reference", "")
        })
    
    return {
        "risks": risks,
        "overall_score": overall_score,
        "overall_risk_level": overall_risk_level,
        "current_step": "approval"
    }


def should_manual_approval(state: ContractState) -> Literal["manual_approval", "auto_approval"]:
    """
    风险分支：根据风险等级选择审批路径
    """
    risk_level = state.get("overall_risk_level", "Low")
    
    if risk_level == "High":
        return "manual_approval"
    return "auto_approval"


def manual_approval_node(state: ContractState):
    """法务人工审批节点"""
    print("--- 高风险合同，进入法务人工审批流程 ---")
    # TODO: 发送邮件通知、创建审批工单等
    return {
        "current_step": "completed"
    }


def auto_approval_node(state: ContractState):
    """自动电子审批节点"""
    print("--- 中低风险合同，自动触发电子审批 ---")
    # TODO: 调用电子审批 API
    return {
        "current_step": "completed"
    }


# 编排工作流
workflow = StateGraph(ContractState)

# 添加节点
workflow.add_node("parse", parse_node)
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("evaluate", evaluate_node)
workflow.add_node("manual_approval", manual_approval_node)
workflow.add_node("auto_approval", auto_approval_node)

# 设置入口点
workflow.set_entry_point("parse")

# 解析后进入检索（parse_node 内部会判断是否需要 OCR）
workflow.add_edge("parse", "retrieve")

# 检索后进入评估
workflow.add_edge("retrieve", "evaluate")

# 评估后根据风险等级分支
workflow.add_conditional_edges(
    "evaluate",
    should_manual_approval,
    {
        "manual_approval": "manual_approval",
        "auto_approval": "auto_approval"
    }
)

# 审批完成后结束
workflow.add_edge("manual_approval", END)
workflow.add_edge("auto_approval", END)

# 编译图
app_graph = workflow.compile()
