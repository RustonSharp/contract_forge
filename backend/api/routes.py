from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
import os
import uuid
import shutil
import json
from datetime import datetime
import logging
from typing import Dict, Any
# 1. 导入 Pydantic 模型
from .schemas import (
    ChatRequest, ChatResponse, ProcessStateResponse, AuditResponse,
    FlowStateResponse, ReportGenerateRequest, ReportGenerateResponse,
    StepRunRequest, StepRunResponse, UploadPrepareResponse
)
# 2. 导入 LangGraph 编译后的图对象
from ..core.graph import app_graph
# 3. 导入大语言模型服务
from ..utils.llm_service import LLMService
# 4. 导入上下文管理器
from ..utils.context_manager import context_manager
from ..utils.logger import get_logger
from ..utils.tool_registry import registry

router = APIRouter(prefix="/api/v1")

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 日志实例
logger = get_logger(__name__)

# 初始化大语言模型服务
# 从环境变量读取地域配置，默认为北京
import os
region = os.getenv("DASHSCOPE_REGION", "beijing")
llm_service = LLMService(region=region)

# 任务状态存储（实际应该使用 Redis 或数据库）
task_states: Dict[str, Dict[str, Any]] = {}
# task_logs: [{step, message, level, timestamp}]
task_logs: Dict[str, list] = {}


def _append_log(task_id: str, step: str, message: str, level: str = "info"):
    entry = {
        "step": step,
        "message": message,
        "level": level,
        "timestamp": datetime.now().isoformat()
    }
    task_logs.setdefault(task_id, []).append(entry)
    lv = (level or "info").lower()
    level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "success": logging.INFO,
        "warning": logging.WARNING,
        "warn": logging.WARNING,
        "error": logging.ERROR,
    }
    logger.log(level_map.get(lv, logging.INFO), f"[log] task={task_id} step={step} level={lv} msg={message}")


def _ensure_task(task_id: str):
    if task_id not in task_states:
        task_states[task_id] = {
            "task_id": task_id,
            "status": "running",
            "current_step": "init",
            "steps": [],
            "start_time": datetime.now().isoformat(),
        }
    task_logs.setdefault(task_id, [])


def _find_step(task_id: str, step_id: str):
    steps = task_states.get(task_id, {}).get("steps", [])
    for s in steps:
        if s.get("id") == step_id:
            return s
    return None


def _start_step(task_id: str, step_id: str, name: str):
    _ensure_task(task_id)
    task_states[task_id]["current_step"] = step_id
    step = _find_step(task_id, step_id)
    if not step:
        step = {"id": step_id, "name": name}
        task_states[task_id]["steps"].append(step)
    step.update({"status": "running", "start_time": datetime.now().isoformat(), "end_time": None, "duration": None, "progress": 0, "error": None, "output": None})
    _append_log(task_id, step_id, f"{name} 开始", "info")


def _finish_step(task_id: str, step_id: str, ok: bool, output: Dict[str, Any] | None = None, error: str | None = None):
    step = _find_step(task_id, step_id)
    if not step:
        return
    step["status"] = "completed" if ok else "failed"
    step["end_time"] = datetime.now().isoformat()
    step["progress"] = 100 if ok else step.get("progress", 0)
    try:
        if step.get("start_time"):
            start_dt = datetime.fromisoformat(step["start_time"])
            end_dt = datetime.fromisoformat(step["end_time"])
            step["duration"] = int((end_dt - start_dt).total_seconds())
    except Exception:
        # 保持 duration 为 None
        pass
    if output is not None:
        step["output"] = output
    if error:
        step["error"] = error
    _append_log(task_id, step_id, "完成" if ok else f"失败: {error}", "success" if ok else "error")


def _build_graph_data(state: Dict[str, Any]) -> Dict[str, Any]:
    # 固定节点集合（MVP）：解析->检索->评估->审批->报告
    node_defs = [
        ("parse", "合同解析"),
        ("retrieve", "法规检索"),
        ("evaluate", "风险评估"),
        ("approval", "审批分支"),
        ("report", "报告生成"),
    ]
    step_status = {s.get("id"): s.get("status", "pending") for s in state.get("steps", [])}
    current_step = state.get("current_step", "")
    nodes = []
    for node_id, label in node_defs:
        status = step_status.get(node_id, "pending")
        # 如果当前步正好是该节点，但状态还没写入 completed/failed，就认为 running
        if current_step == node_id and status == "pending":
            status = "running"
        nodes.append({"id": node_id, "label": label, "status": status})
    edges = [
        {"from": "parse", "to": "retrieve"},
        {"from": "retrieve", "to": "evaluate"},
        {"from": "evaluate", "to": "approval"},
        {"from": "approval", "to": "report"},
    ]
    return {"nodes": nodes, "edges": edges}


@router.get("/state/{task_id}", response_model=FlowStateResponse)
def get_flow_state(task_id: str):
    """
    获取流程状态（包含详细步骤信息）
    """
    if task_id not in task_states:
        logger.warning(f"[state] task not found: {task_id}")
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    state = task_states[task_id]
    # 补齐 steps 字段默认值（兼容旧任务数据）
    state.setdefault("steps", [])
    
    graph_data = _build_graph_data(state)
    
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
        logger.warning(f"[logs] task not found: {task_id}")
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
    logger.info(f"[report] generating for task: {request.task_id}")
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
        logger.info(f"[chat] message received. has_context={bool(request.context)}")
        result = llm_service.chat(request.message, request.context)
        return ChatResponse(
            status="success",
            data=result,
            error_msg=""
        )
    except Exception as e:
        logger.exception(f"[chat] failed: {str(e)}")
        return ChatResponse(
            status="failed",
            data={"response": "抱歉，处理您的请求时出现错误。", "suggested_actions": [], "confidence": 0.0},
            error_msg=str(e)
        )


# ---- Step APIs (for N8N full orchestration) ----
@router.post("/steps/parse", response_model=StepRunResponse)
async def step_parse(req: StepRunRequest):
    ctx = req.context or {}
    task_id = ctx.get("task_id")
    if not task_id:
        raise HTTPException(status_code=400, detail="context.task_id is required")

    file_path = (req.input or {}).get("file_path", "")
    if not file_path:
        raise HTTPException(status_code=400, detail="input.file_path is required")

    _start_step(task_id, "parse", "合同解析")
    try:
        ext = os.path.splitext(file_path)[1].lower()
        image_exts = [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]
        tool_name = "OCRParser" if ext in image_exts else "ContractParser"
        tool = registry.get(tool_name)
        if not tool:
            raise ValueError(f"tool not registered: {tool_name}")
        result = tool.run({"file_path": file_path}, ctx)
        if result.get("status") != "success":
            raise ValueError(result.get("message", "parse failed"))

        data = result.get("data", {}) or {}
        task_states[task_id]["raw_text"] = data.get("raw_text")
        task_states[task_id]["structured_data"] = data.get("structured_data")
        _finish_step(task_id, "parse", True, output={"tool": tool_name})
        return StepRunResponse(status="success", data=data, error_msg="", error_code="")
    except Exception as e:
        _finish_step(task_id, "parse", False, error=str(e))
        return StepRunResponse(status="failed", data={}, error_msg=str(e), error_code="PARSE_FAILED")


@router.post("/steps/retrieve", response_model=StepRunResponse)
async def step_retrieve(req: StepRunRequest):
    ctx = req.context or {}
    task_id = ctx.get("task_id")
    if not task_id:
        raise HTTPException(status_code=400, detail="context.task_id is required")
    _ensure_task(task_id)

    keywords = (req.input or {}).get("keywords")
    raw_text = (req.input or {}).get("raw_text") or task_states.get(task_id, {}).get("raw_text") or ""
    if not keywords and not raw_text:
        raise HTTPException(status_code=400, detail="input.keywords or input.raw_text is required")

    _start_step(task_id, "retrieve", "法规检索")
    try:
        if not keywords:
            # 尝试用 LLM 提取关键词；失败则退化为前100字
            try:
                prompt = f"请从以下合同文本中提取用于法律检索的关键词，5-10个，用逗号分隔，只返回关键词：\n\n{raw_text[:1000]}\n\n关键词:"
                keywords = llm_service._call_dashscope_api([{'role': 'user', 'content': prompt}], max_tokens=200, temperature=0.3)
                keywords = keywords.strip().replace("\n", " ").replace("，", ",").replace("、", ",")
            except Exception:
                keywords = raw_text[:100]

        retriever = registry.get("LawRetriever")
        if not retriever:
            raise ValueError("tool not registered: LawRetriever")
        result = retriever.run({"keywords": keywords}, ctx)
        if result.get("status") != "success":
            raise ValueError(result.get("message", "retrieve failed"))
        data = result.get("data", {}) or {}
        task_states[task_id]["referenced_laws"] = data.get("laws", [])
        _finish_step(task_id, "retrieve", True, output={"keywords": keywords, "total": data.get("total", 0)})
        return StepRunResponse(status="success", data=data, error_msg="", error_code="")
    except Exception as e:
        _finish_step(task_id, "retrieve", False, error=str(e))
        return StepRunResponse(status="failed", data={}, error_msg=str(e), error_code="RETRIEVE_FAILED")


@router.post("/steps/evaluate", response_model=StepRunResponse)
async def step_evaluate(req: StepRunRequest):
    ctx = req.context or {}
    task_id = ctx.get("task_id")
    if not task_id:
        raise HTTPException(status_code=400, detail="context.task_id is required")
    _ensure_task(task_id)

    raw_text = (req.input or {}).get("raw_text") or task_states.get(task_id, {}).get("raw_text") or ""
    structured_data = (req.input or {}).get("structured_data") or task_states.get(task_id, {}).get("structured_data")
    laws = (req.input or {}).get("referenced_laws") or task_states.get(task_id, {}).get("referenced_laws") or []
    if not raw_text:
        raise HTTPException(status_code=400, detail="raw_text is required (input.raw_text or parsed state)")

    _start_step(task_id, "evaluate", "风险评估")
    try:
        evaluator = registry.get("RiskEvaluator")
        if not evaluator:
            raise ValueError("tool not registered: RiskEvaluator")
        result = evaluator.run({"raw_text": raw_text, "structured_data": structured_data, "referenced_laws": laws}, ctx)
        if result.get("status") != "success":
            raise ValueError(result.get("message", "evaluate failed"))
        data = result.get("data", {}) or {}

        # 同步到任务状态（用于 report/chat）
        task_states[task_id]["risks"] = data.get("detailed_risks", [])
        task_states[task_id]["overall_score"] = data.get("overall_score", 100)
        task_states[task_id]["overall_risk_level"] = data.get("overall_risk_level", "Low")
        _finish_step(task_id, "evaluate", True, output={"overall_risk_level": task_states[task_id]["overall_risk_level"]})
        return StepRunResponse(status="success", data=data, error_msg="", error_code="")
    except Exception as e:
        _finish_step(task_id, "evaluate", False, error=str(e))
        return StepRunResponse(status="failed", data={}, error_msg=str(e), error_code="EVALUATE_FAILED")


@router.post("/steps/approval", response_model=StepRunResponse)
async def step_approval(req: StepRunRequest):
    ctx = req.context or {}
    task_id = ctx.get("task_id")
    if not task_id:
        raise HTTPException(status_code=400, detail="context.task_id is required")
    _ensure_task(task_id)

    risk_level = (req.input or {}).get("overall_risk_level") or task_states.get(task_id, {}).get("overall_risk_level") or "Low"
    _start_step(task_id, "approval", "审批分支")
    try:
        route = "manual_approval" if risk_level == "High" else "auto_approval"
        data = {"overall_risk_level": risk_level, "route": route, "status": "ok"}
        _finish_step(task_id, "approval", True, output=data)
        return StepRunResponse(status="success", data=data, error_msg="", error_code="")
    except Exception as e:
        _finish_step(task_id, "approval", False, error=str(e))
        return StepRunResponse(status="failed", data={}, error_msg=str(e), error_code="APPROVAL_FAILED")


@router.post("/steps/report", response_model=StepRunResponse)
async def step_report(req: StepRunRequest):
    ctx = req.context or {}
    task_id = ctx.get("task_id")
    if not task_id:
        raise HTTPException(status_code=400, detail="context.task_id is required")
    _ensure_task(task_id)

    template = (req.input or {}).get("template", "detailed")
    format_ = (req.input or {}).get("format", "markdown")
    _start_step(task_id, "report", "报告生成")
    try:
        state = task_states.get(task_id, {})
        audit_data = {
            "risks": state.get("risks", []),
            "overall_score": state.get("overall_score", 100),
            "generated_at": datetime.now().isoformat(),
        }
        try:
            result = llm_service.generate_report(task_id, audit_data, template, format_)
        except Exception:
            # 无 LLM 或调用失败时生成简单 Markdown
            result = {
                "report": f"## 合同审计报告\n\n- 风险等级: {state.get('overall_risk_level', 'Unknown')}\n- 合规评分: {state.get('overall_score', 100)}\n- 风险项数量: {len(state.get('risks', []))}\n",
                "summary": f"共检测到 {len(state.get('risks', []))} 处风险项。",
                "generated_at": datetime.now().isoformat(),
            }
        _finish_step(task_id, "report", True, output={"template": template, "format": format_})
        return StepRunResponse(status="success", data=result, error_msg="", error_code="")
    except Exception as e:
        _finish_step(task_id, "report", False, error=str(e))
        return StepRunResponse(status="failed", data={}, error_msg=str(e), error_code="REPORT_FAILED")


@router.post("/audit", response_model=AuditResponse)
async def start_audit(file: UploadFile = File(...)):
    """
    接收 React 上传的 PDF 文件，并触发 LangGraph 审计流
    """
    # 1. 保存文件到本地
    file_id = str(uuid.uuid4())
    temp_file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    
    try:
        logger.info(f"[audit] start task: {file_id}, filename={file.filename}")
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
        _append_log(file_id, "init", "任务初始化", "info")
        
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
        _append_log(file_id, "parse", "开始解析合同文档", "info")
        
        # 5. 调用 LangGraph 图
        final_state = app_graph.invoke(initial_state)
        
        # 6. 更新步骤状态
        step_parse["status"] = "completed"
        step_parse["end_time"] = datetime.now().isoformat()
        step_parse["duration"] = 2  # 模拟
        _append_log(file_id, "parse", "解析完成", "info")
        
        step_retrieve = {
            "id": "retrieve",
            "name": "法规检索",
            "status": "completed",
            "start_time": datetime.now().isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration": 1
        }
        task_states[file_id]["steps"].append(step_retrieve)
        _append_log(file_id, "retrieve", "法规检索完成", "info")
        
        step_evaluate = {
            "id": "evaluate",
            "name": "风险评估",
            "status": "completed",
            "start_time": datetime.now().isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration": 3
        }
        task_states[file_id]["steps"].append(step_evaluate)
        _append_log(file_id, "evaluate", "风险评估完成", "info")
        
        # 7. 更新任务状态
        task_states[file_id]["status"] = "completed"
        task_states[file_id]["current_step"] = "completed"
        task_states[file_id]["risks"] = final_state.get("risks", [])
        task_states[file_id]["overall_score"] = final_state.get("overall_score", 100)
        logger.info(f"[audit] completed task: {file_id}")
        _append_log(file_id, "complete", "任务完成", "info")
        
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
        logger.exception(f"[audit] failed task: {file_id}, error={str(e)}")
        _append_log(file_id, "error", f"任务失败: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=f"审计流程中断: {str(e)}")


@router.post("/upload", response_model=UploadPrepareResponse)
async def upload_only(file: UploadFile = File(...)):
    """
    仅上传文件并初始化任务（不执行 LangGraph）。
    供 N8N 全编排模式使用：N8N 根据 task_id 调用 /steps/* 逐步推进。
    """
    task_id = str(uuid.uuid4())
    temp_file_path = os.path.join(UPLOAD_DIR, f"{task_id}_{file.filename}")
    try:
        logger.info(f"[upload] prepare task: {task_id}, filename={file.filename}")
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        _ensure_task(task_id)
        task_states[task_id]["status"] = "running"
        task_states[task_id]["current_step"] = "init"
        task_states[task_id]["file_path"] = temp_file_path
        _append_log(task_id, "init", "文件已上传，等待编排执行", "info")

        return UploadPrepareResponse(status="success", task_id=task_id, file_path=temp_file_path)
    except Exception as e:
        logger.exception(f"[upload] failed task: {task_id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")