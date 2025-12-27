from langgraph.graph import StateGraph, END
from .state import ContractState
from ..tools.doc_parser import ContractParser
from ..tools.law_retriever import LawRetriever
from ..tools.risk_evaluator import RiskEvaluator

# 实例化工具
parser = ContractParser()
retriever = LawRetriever()
evaluator = RiskEvaluator()

def parse_node(state: ContractState):
    print("--- 正在解析文档 ---")
    result = parser.run({"file_path": state["file_path"]}, {})
    return {
        "raw_text": result["data"]["raw_text"],
        "current_step": "retrieving"
    }

def retrieve_node(state: ContractState):
    print("--- 正在检索法律依据 ---")
    # 实际开发中，这里会先用 LLM 提取关键词，MVP 暂用全文前 50 字模拟
    query = state["raw_text"][:50] 
    result = retriever.run({"keywords": query}, {})
    return {
        "referenced_laws": result["data"]["laws"],
        "current_step": "evaluating"
    }

def evaluate_node(state: ContractState):
    print("--- 正在进行风险评估 ---")
    # 构造评估器的输入
    test_clauses = [{"text": state["raw_text"][:200], "type": "违约金"}]
    result = evaluator.run({
        "clauses": test_clauses,
        "referenced_laws": state["referenced_laws"]
    }, {})
    return {
        "risks": result["data"]["detailed_risks"],
        "current_step": "completed"
    }

# 编排工作流
workflow = StateGraph(ContractState)

workflow.add_node("parse", parse_node)
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("evaluate", evaluate_node)

workflow.set_entry_point("parse")
workflow.add_edge("parse", "retrieve")
workflow.add_edge("retrieve", "evaluate")
workflow.add_edge("evaluate", END)

app_graph = workflow.compile()