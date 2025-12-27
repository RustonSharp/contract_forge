from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
import os
import uuid
import shutil
import json
from datetime import datetime
from typing import Dict, Any
# 1. 导入 Pydantic 模型
from .schemas import (
    ChatRequest, ChatResponse, ProcessStateResponse, AuditResponse,
    FlowStateResponse, ReportGenerateRequest, ReportGenerateResponse
)
# 2. 导入 LangGraph 编译后的图对象
from ..core.graph import app_graph
# 3. 导入大语言模型服务
from ..utils.llm_service import LLMService
# 4. 导入上下文管理器
from ..utils.context_manager import context_manager

router = APIRouter(prefix="/api/v1")

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 初始化大语言模型服务
# 从环境变量读取地域配置，默认为北京
import os
region = os.getenv("DASHSCOPE_REGION", "beijing")
llm_service = LLMService(region=region)

# 任务状态存储（实际应该使用 Redis 或数据库）
task_states: Dict[str, Dict[str, Any]] = {}
task_logs: Dict[str, list] = {}


@router.get("/state/{task_id}", response_model=FlowStateResponse)
def get_flow_state(task_id: str):
    """
    获取流程状态（包含详细步骤信息）
    """
    if task_id not in task_states:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    state = task_states[task_id]
    
    # 构建图数据（简化版）
    graph_data = {
        "nodes": [
            {"id": "parse", "label": "合同解析", "status": "completed"},
            {"id": "retrieve", "label": "法规检索", "status": "completed"},
            {"id": "evaluate", "label": "风险评估", "status": "completed"}
        ],
        "edges": [
            {"from": "parse", "to": "retrieve"},
            {"from": "retrieve", "to": "evaluate"}
        ]
    }
    
    return FlowStateResponse(
        task_id=task_id,
        status=state.get("status", "unknown"),
        current_step=state.get("current_step", ""),
        steps=state.get("steps", []),
        graph_data=graph_data
    )

@router.get("/logs/{task_id}")
def get_task_logs(task_id: str):
    """
    获取任务执行日志
    """
    if task_id not in task_logs:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    return {
        "status": "success",
        "data": {
            "logs": task_logs[task_id],
            "total": len(task_logs[task_id])
        }
    }

@router.post("/report/generate", response_model=ReportGenerateResponse)
async def generate_report(request: ReportGenerateRequest):
    """
    生成智能报告
    """
    if request.task_id not in task_states:
        raise HTTPException(status_code=404, detail=f"Task {request.task_id} not found")
    
    # 获取审计数据
    state = task_states[request.task_id]
    audit_data = {
        "risks": state.get("risks", []),
        "overall_score": state.get("overall_score", 100),
        "generated_at": datetime.now().isoformat()
    }
    
    try:
        result = llm_service.generate_report(
            request.task_id,
            audit_data,
            request.template,
            request.format
        )
        return ReportGenerateResponse(
            status="success",
            data=result,
            error_msg=""
        )
    except Exception as e:
        return ReportGenerateResponse(
            status="failed",
            data={"report": "", "summary": "", "generated_at": ""},
            error_msg=str(e)
        )

@router.post("/chat", response_model=ChatResponse)
async def chat_with_model(request: ChatRequest):
    """
    自然语言交互接口
    调用大语言模型生成智能回复
    """
    try:
        result = llm_service.chat(request.message, request.context)
        return ChatResponse(
            status="success",
            data=result,
            error_msg=""
        )
    except Exception as e:
        return ChatResponse(
            status="failed",
            data={"response": "抱歉，处理您的请求时出现错误。", "suggested_actions": [], "confidence": 0.0},
            error_msg=str(e)
        )


@router.post("/audit", response_model=AuditResponse)
async def start_audit(file: UploadFile = File(...)):
    """
    接收 React 上传的 PDF 文件，并触发 LangGraph 审计流
    """
    # 1. 保存文件到本地
    file_id = str(uuid.uuid4())
    temp_file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 2. 初始化任务状态
        task_states[file_id] = {
            "task_id": file_id,
            "status": "running",
            "current_step": "parsing",
            "steps": [],
            "start_time": datetime.now().isoformat()
        }
        task_logs[file_id] = []
        
        # 3. 初始化 LangGraph 状态机参数
        initial_state = {
            "file_path": temp_file_path,
            "current_step": "parsing",
            "risks": [],
            "overall_score": 100
        }
        
        # 4. 记录步骤开始
        step_parse = {
            "id": "parse",
            "name": "合同解析",
            "status": "running",
            "start_time": datetime.now().isoformat()
        }
        task_states[file_id]["steps"].append(step_parse)
        task_logs[file_id].append({
            "step": "parse",
            "message": "开始解析合同文档",
            "timestamp": datetime.now().isoformat()
        })
        
        # 5. 调用 LangGraph 图
        final_state = app_graph.invoke(initial_state)
        
        # 6. 更新步骤状态
        step_parse["status"] = "completed"
        step_parse["end_time"] = datetime.now().isoformat()
        step_parse["duration"] = 2  # 模拟
        
        step_retrieve = {
            "id": "retrieve",
            "name": "法规检索",
            "status": "completed",
            "start_time": datetime.now().isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration": 1
        }
        task_states[file_id]["steps"].append(step_retrieve)
        
        step_evaluate = {
            "id": "evaluate",
            "name": "风险评估",
            "status": "completed",
            "start_time": datetime.now().isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration": 3
        }
        task_states[file_id]["steps"].append(step_evaluate)
        
        # 7. 更新任务状态
        task_states[file_id]["status"] = "completed"
        task_states[file_id]["current_step"] = "completed"
        task_states[file_id]["risks"] = final_state.get("risks", [])
        task_states[file_id]["overall_score"] = final_state.get("overall_score", 100)
        
        # 8. 保存上下文并标记完成
        context_manager.save_context(file_id, {
            "file_path": temp_file_path,
            "raw_text": final_state.get("raw_text"),
            "structured_data": final_state.get("structured_data"),
            "referenced_laws": final_state.get("referenced_laws", []),
            "risks": final_state.get("risks", []),
            "overall_score": final_state.get("overall_score", 100)
        })
        context_manager.mark_completed(file_id)
        
        # 9. 返回审计结果
        return {
            "status": "success",
            "task_id": file_id,
            "report": {
                "risks": final_state.get("risks", []),
                "step": final_state.get("current_step", "completed"),
                "overall_score": final_state.get("overall_score", 100)
            }
        }
        
    except Exception as e:
        # 发生错误时，确保返回 500
        if file_id in task_states:
            task_states[file_id]["status"] = "failed"
            task_states[file_id]["error"] = str(e)
        raise HTTPException(status_code=500, detail=f"审计流程中断: {str(e)}")