from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatRequest(BaseModel):
    message: str = Field(..., example="请帮我分析这份合同的违约金条款")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息（task_id, user_id, session_id）")

class SuggestedAction(BaseModel):
    action: str
    endpoint: str

class ChatResponse(BaseModel):
    status: str = "success"
    data: Dict[str, Any] = Field(..., description="包含 response, suggested_actions, confidence")
    error_msg: str = ""

class ProcessState(BaseModel):
    process_id: str
    status: str

class ProcessStateResponse(BaseModel):
    process_id: int
    q: Optional[str] = None

class StepInfo(BaseModel):
    id: str
    name: str
    status: str  # pending/running/completed/failed
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration: Optional[int] = None  # 秒
    progress: Optional[int] = None  # 0-100
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class FlowStateResponse(BaseModel):
    task_id: str
    status: str  # running/completed/failed
    current_step: str
    steps: List[StepInfo]
    graph_data: Optional[Dict[str, Any]] = None

class ReportGenerateRequest(BaseModel):
    task_id: str
    template: str = "detailed"  # simple/detailed
    format: str = "markdown"  # markdown/pdf/word

class ReportGenerateResponse(BaseModel):
    status: str = "success"
    data: Dict[str, Any] = Field(..., description="包含 report, summary, generated_at")
    error_msg: str = ""


class RiskItem(BaseModel):
    """单项风险详情"""
    clause_content: str = Field(..., description="合同原文条款")
    risk_level: str = Field(..., description="风险等级: High/Medium/Low")
    risk_desc: str = Field(..., description="详细的风险描述")
    suggestion: str = Field(..., description="法务修改建议")
    reference: str = Field(..., description="法律法规依据")

class AuditReport(BaseModel):
    """完整审计报告模型"""
    risks: List[RiskItem]
    overall_score: int = Field(100, ge=0, le=100, description="合规评分")
    step: str = Field("completed", description="当前流程状态")

class AuditResponse(BaseModel):
    """审计接口统一返回格式"""
    status: str = Field("success", example="success")
    task_id: str
    report: AuditReport


# ---- Step API DTOs (Langdock-style) ----
class StepRunRequest(BaseModel):
    """
    统一步骤调用入参：
    - input：步骤执行必需参数
    - context：固定包含 task_id/step_id/history_results（由编排层维护）
    """
    input: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)


class StepRunResponse(BaseModel):
    """统一步骤调用出参"""
    status: str = Field(..., description="success/failed")
    data: Dict[str, Any] = Field(default_factory=dict)
    error_msg: str = ""
    error_code: str = ""


class UploadPrepareResponse(BaseModel):
    """仅上传并准备任务（给 N8N 编排使用）"""
    status: str = "success"
    task_id: str
    file_path: str