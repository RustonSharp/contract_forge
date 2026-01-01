"""
N8N 工作流触发工具
用于调用 N8N 触发器 API，执行自动化流程
"""

import time
import os
import aiohttp
from typing import Any, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv

from backend.service.tools.base import BaseTool
from backend.service.tools.models import ToolInfo, ToolParameter, ToolResult
from backend.service.workflow.service import get_workflow_status_service, WorkflowStatus
from backend.service.tools.core_tools import ImageToPdfTool, find_file_in_uploads
from backend.utils.logger import get_logger

logger = get_logger(__name__)


# 查找项目根目录并加载 .env
def find_project_root() -> Path:
    """查找项目根目录"""
    current = Path(__file__).resolve()
    for _ in range(5):
        if (current / ".env").exists() or (current / ".git").exists() or (current / "requirements.txt").exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return Path.cwd()


project_root = find_project_root()
load_dotenv(dotenv_path=project_root / ".env")


class N8NWorkflowTriggerTool(BaseTool):
    """N8N 工作流触发工具 - 用于触发自动化流程"""
    
    def __init__(self):
        super().__init__()
        # 从环境变量获取 N8N API 地址
        self.n8n_api_url = os.getenv("N8N_API", "").rstrip("/")
        if not self.n8n_api_url:
            # 如果没有配置，使用默认值（需要用户配置）
            self.n8n_api_url = "http://localhost:5678/webhook/contract-process"
    
    def get_info(self) -> ToolInfo:
        return ToolInfo(
            name="n8n_workflow_trigger",
            display_name="N8N 工作流触发工具",
            description="触发 N8N 自动化工作流处理合同文件。当用户没有指定具体工具，只是要求处理文件时，应使用此工具执行完整的自动化流程（包括文档解析、合规校验、风险评估等）",
            parameters=[
                ToolParameter(
                    name="file_path",
                    type="string",
                    description="合同文件相对路径（相对于 uploads 目录，如 '2025-12-29/test_contract.pdf'）或文件名。程序会在 uploads 目录下自动查找",
                    required=False
                ),
                ToolParameter(
                    name="file_name",
                    type="string",
                    description="合同文件名（已弃用，请使用 file_path）。可以是完整文件名或部分文件名，程序会在 uploads 目录下自动查找",
                    required=False
                ),
                ToolParameter(
                    name="workflow_path",
                    type="string",
                    description="N8N Webhook 路径（可选，默认使用 /webhook/contract-process）",
                    required=False
                ),
                ToolParameter(
                    name="http_method",
                    type="string",
                    description="HTTP 请求方法（GET 或 POST，默认 POST）",
                    required=False,
                    default="POST"
                )
            ],
            category="workflow",
            version="1.0.0"
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行 N8N 工作流触发"""
        start_time = time.time()
        
        try:
            # 验证参数
            is_valid, error_msg = self.validate_parameters(**kwargs)
            if not is_valid:
                return ToolResult(
                    success=False,
                    error=error_msg,
                    execution_time=time.time() - start_time
                )
            
            # 优先使用 file_path，如果未提供则使用 file_name（向后兼容）
            file_path = kwargs.get("file_path")
            file_name = kwargs.get("file_name")
            
            # 如果提供了 file_path，使用 file_path；否则使用 file_name
            if not file_path and file_name:
                file_path = file_name
            elif not file_path:
                return ToolResult(
                    success=False,
                    error="file_path 或 file_name 参数必须提供其中一个",
                    execution_time=time.time() - start_time
                )
            
            # 检查文件类型，如果是图片格式，先转换为 PDF
            original_file_path = file_path
            image_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"]
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext in image_extensions:
                logger.info(f"检测到图片文件 {file_path}，先转换为 PDF 格式")
                
                try:
                    # 查找图片文件
                    resolved_image_path = find_file_in_uploads(file_path)
                    if not resolved_image_path:
                        project_root = Path(__file__).resolve().parent.parent.parent.parent
                        uploads_dir = project_root / "uploads"
                        resolved_image_path = find_file_in_uploads(file_path, str(uploads_dir))
                    
                    if not resolved_image_path:
                        return ToolResult(
                            success=False,
                            error=f"图片文件不存在: {file_path}。无法转换为 PDF。",
                            execution_time=time.time() - start_time
                        )
                    
                    # 调用 image_to_pdf 工具进行转换
                    image_to_pdf_tool = ImageToPdfTool()
                    conversion_result = await image_to_pdf_tool.execute(image_path=resolved_image_path)
                    
                    if not conversion_result.success:
                        return ToolResult(
                            success=False,
                            error=f"图片转 PDF 失败: {conversion_result.error}",
                            execution_time=time.time() - start_time
                        )
                    
                    # 使用转换后的 PDF 文件路径
                    pdf_path = conversion_result.data.get("pdf_path")
                    if pdf_path:
                        file_path = pdf_path
                        logger.info(f"图片已转换为 PDF: {original_file_path} -> {file_path}")
                    else:
                        # 如果返回数据中没有 pdf_path，尝试从 pdf_filename 构建
                        pdf_filename = conversion_result.data.get("pdf_filename")
                        if pdf_filename:
                            # 从原始文件路径中提取目录部分
                            original_dir = str(Path(original_file_path).parent)
                            if original_dir == ".":
                                file_path = pdf_filename
                            else:
                                file_path = f"{original_dir}/{pdf_filename}"
                            logger.info(f"使用转换后的 PDF 文件名: {file_path}")
                        else:
                            return ToolResult(
                                success=False,
                                error="图片转 PDF 成功，但无法获取 PDF 文件路径",
                                execution_time=time.time() - start_time
                            )
                    
                except Exception as e:
                    logger.error(f"图片转 PDF 过程中发生错误: {str(e)}", exc_info=True)
                    return ToolResult(
                        success=False,
                        error=f"图片转 PDF 失败: {str(e)}",
                        execution_time=time.time() - start_time
                    )
            
            workflow_path = kwargs.get("workflow_path", "/webhook/contract-process")
            http_method = kwargs.get("http_method", "POST").upper()
            
            # 构建 N8N Webhook URL
            # 如果 N8N_API 环境变量已配置，检查是否包含完整路径
            n8n_api = os.getenv("N8N_API", "").rstrip("/")
            
            if n8n_api:
                # 如果 N8N_API 已经包含完整路径（如 http://localhost:5678/webhook-test/xxx）
                # 直接使用它，不再添加 workflow_path
                if "/webhook" in n8n_api or "/webhook-test" in n8n_api:
                    webhook_url = n8n_api
                else:
                    # 如果只是基础 URL，添加 workflow_path
                    if not workflow_path.startswith("/"):
                        workflow_path = "/" + workflow_path
                    webhook_url = f"{n8n_api}{workflow_path}"
            else:
                # 使用默认值
                n8n_base_url = "http://localhost:5678"
                if not workflow_path.startswith("/"):
                    workflow_path = "/" + workflow_path
                webhook_url = f"{n8n_base_url}{workflow_path}"
            
            # 创建工作流状态记录
            workflow_status_service = get_workflow_status_service()
            workflow_id = workflow_status_service.create_workflow_status(
                file_path=file_path,
                initial_status=WorkflowStatus.RUNNING
            )
            
            # 准备请求数据（传递 file_path 和 workflow_id）
            # 如果原文件是图片，file_path 已经是转换后的 PDF 路径
            request_data = {
                "file_path": file_path,
                "workflow_id": workflow_id
            }
            
            # 如果原文件是图片，在请求数据中记录原始文件路径（可选，用于日志）
            if file_ext in image_extensions and file_path != original_file_path:
                request_data["original_file_path"] = original_file_path
                logger.info(f"N8N 工作流将使用转换后的 PDF 文件: {file_path} (原始文件: {original_file_path})")
            
            # 调用 N8N Webhook
            async with aiohttp.ClientSession() as session:
                try:
                    # 根据 HTTP 方法选择请求方式
                    if http_method == "GET":
                        # GET 请求：将参数作为查询字符串
                        # 增加超时时间以支持长时间运行的工作流（5分钟）
                        async with session.get(
                            webhook_url,
                            params=request_data,
                            timeout=aiohttp.ClientTimeout(total=300)
                        ) as response:
                            try:
                                response_data = await response.json()
                            except:
                                response_data = {"message": await response.text()}
                            
                            # 处理响应
                            if response.status == 200:
                                result_data = {
                                    "workflow_id": workflow_id,
                                    "file_path": file_path,
                                    "webhook_url": webhook_url,
                                    "http_method": http_method,
                                    "n8n_response": response_data,
                                    "status": "triggered",
                                    "message": "N8N 工作流已成功触发"
                                }
                                
                                return ToolResult(
                                    success=True,
                                    data=result_data,
                                    execution_time=time.time() - start_time
                                )
                            else:
                                # 提供更详细的错误信息
                                error_msg = f"N8N Webhook 调用失败: HTTP {response.status}"
                                if isinstance(response_data, dict):
                                    error_msg += f", {response_data.get('message', response_data)}"
                                else:
                                    error_msg += f", {response_data}"
                                
                                # 添加解决建议
                                if response.status == 404:
                                    error_msg += "\n提示: 请检查：\n"
                                    error_msg += "1. N8N 工作流是否已激活（设置为 Active 状态）\n"
                                    error_msg += "2. Webhook 节点的 HTTP 方法是否与请求方法匹配（GET/POST）\n"
                                    error_msg += "3. Webhook URL 是否正确（检查 N8N_API 环境变量）\n"
                                    error_msg += "4. 如果是测试模式，需要在 N8N 界面点击 'Execute workflow' 按钮"
                                
                                return ToolResult(
                                    success=False,
                                    error=error_msg,
                                    execution_time=time.time() - start_time
                                )
                    else:
                        # POST 请求：将参数作为 JSON body
                        # 增加超时时间以支持长时间运行的工作流（5分钟）
                        async with session.post(
                            webhook_url,
                            json=request_data,
                            timeout=aiohttp.ClientTimeout(total=300)
                        ) as response:
                            try:
                                response_data = await response.json()
                            except:
                                response_data = {"message": await response.text()}
                            
                            # 处理响应
                            if response.status == 200:
                                result_data = {
                                    "workflow_id": workflow_id,
                                    "file_path": file_path,
                                    "webhook_url": webhook_url,
                                    "http_method": http_method,
                                    "n8n_response": response_data,
                                    "status": "triggered",
                                    "message": "N8N 工作流已成功触发"
                                }
                                
                                return ToolResult(
                                    success=True,
                                    data=result_data,
                                    execution_time=time.time() - start_time
                                )
                            else:
                                # 提供更详细的错误信息
                                error_msg = f"N8N Webhook 调用失败: HTTP {response.status}"
                                if isinstance(response_data, dict):
                                    error_msg += f", {response_data.get('message', response_data)}"
                                else:
                                    error_msg += f", {response_data}"
                                
                                # 添加解决建议
                                if response.status == 404:
                                    error_msg += "\n提示: 请检查：\n"
                                    error_msg += "1. N8N 工作流是否已激活（设置为 Active 状态）\n"
                                    error_msg += "2. Webhook 节点的 HTTP 方法是否与请求方法匹配（GET/POST）\n"
                                    error_msg += "3. Webhook URL 是否正确（检查 N8N_API 环境变量）\n"
                                    error_msg += "4. 如果是测试模式，需要在 N8N 界面点击 'Execute workflow' 按钮"
                                
                                return ToolResult(
                                    success=False,
                                    error=error_msg,
                                    execution_time=time.time() - start_time
                                )
                
                except aiohttp.ClientError as e:
                    return ToolResult(
                        success=False,
                        error=f"调用 N8N Webhook 时发生网络错误: {str(e)}。请检查 N8N_API 环境变量配置是否正确",
                        execution_time=time.time() - start_time
                    )
                except Exception as e:
                    return ToolResult(
                        success=False,
                        error=f"调用 N8N Webhook 时发生错误: {str(e)}",
                        execution_time=time.time() - start_time
                    )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"执行 N8N 工作流触发时发生错误: {str(e)}",
                execution_time=time.time() - start_time
            )

