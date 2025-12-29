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
                    name="file_name",
                    type="string",
                    description="合同文件名（可以是完整文件名或部分文件名，程序会在 uploads 目录下自动查找）",
                    required=True
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
            
            file_name = kwargs.get("file_name")
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
            
            # 准备请求数据（仅传递 file_name）
            request_data = {
                "file_name": file_name
            }
            
            # 调用 N8N Webhook
            async with aiohttp.ClientSession() as session:
                try:
                    # 根据 HTTP 方法选择请求方式
                    if http_method == "GET":
                        # GET 请求：将参数作为查询字符串
                        async with session.get(
                            webhook_url,
                            params=request_data,
                            timeout=aiohttp.ClientTimeout(total=60)
                        ) as response:
                            try:
                                response_data = await response.json()
                            except:
                                response_data = {"message": await response.text()}
                            
                            # 处理响应
                            if response.status == 200:
                                result_data = {
                                    "file_name": file_name,
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
                        async with session.post(
                            webhook_url,
                            json=request_data,
                            timeout=aiohttp.ClientTimeout(total=60)
                        ) as response:
                            try:
                                response_data = await response.json()
                            except:
                                response_data = {"message": await response.text()}
                            
                            # 处理响应
                            if response.status == 200:
                                result_data = {
                                    "file_name": file_name,
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

