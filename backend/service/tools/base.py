"""
工具基类和工具实现
"""

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from backend.service.tools.models import ToolInfo, ToolParameter, ToolResult


class BaseTool(ABC):
    """工具基类，所有工具都应继承此类"""
    
    def __init__(self):
        self._info = self.get_info()
    
    @abstractmethod
    def get_info(self) -> ToolInfo:
        """
        返回工具信息
        
        Returns:
            ToolInfo: 工具信息对象
        """
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        执行工具
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            ToolResult: 执行结果
        """
        pass
    
    async def run(self, input: Any, context: Optional[Dict[str, Any]] = None) -> ToolResult:
        """
        标准接口：run(input, context)
        
        Args:
            input: 输入数据（可以是字符串、字典等）
            context: 上下文信息（可选）
            
        Returns:
            ToolResult: 执行结果
        """
        # 默认实现：将 input 转换为 kwargs
        if isinstance(input, dict):
            kwargs = input.copy()
        elif isinstance(input, str):
            # 如果是字符串，尝试从 context 获取参数，或使用默认参数名
            kwargs = {"input": input}
            if context:
                kwargs.update(context)
        else:
            kwargs = {"input": input}
            if context:
                kwargs.update(context)
        
        return await self.execute(**kwargs)
    
    def validate_parameters(self, **kwargs) -> Tuple[bool, Optional[str]]:
        """
        验证参数
        
        Args:
            **kwargs: 待验证的参数
            
        Returns:
            tuple[bool, Optional[str]]: (是否有效, 错误信息)
        """
        info = self.get_info()
        provided_params = set(kwargs.keys())
        required_params = {p.name for p in info.parameters if p.required}
        
        # 检查必需参数
        missing_params = required_params - provided_params
        if missing_params:
            return False, f"缺少必需参数: {', '.join(missing_params)}"
        
        # 检查未知参数
        valid_params = {p.name for p in info.parameters}
        unknown_params = provided_params - valid_params
        if unknown_params:
            return False, f"未知参数: {', '.join(unknown_params)}"
        
        return True, None
    
    @property
    def info(self) -> ToolInfo:
        """获取工具信息"""
        return self._info
    
    @property
    def name(self) -> str:
        """获取工具名称"""
        return self._info.name


class ContractAnalysisTool(BaseTool):
    """合同分析工具示例"""
    
    def get_info(self) -> ToolInfo:
        return ToolInfo(
            name="contract_analysis",
            display_name="合同分析工具",
            description="分析合同内容，提取关键信息和条款",
            parameters=[
                ToolParameter(
                    name="contract_id",
                    type="string",
                    description="合同ID或文件路径",
                    required=True
                ),
                ToolParameter(
                    name="analysis_type",
                    type="string",
                    description="分析类型: summary, clauses, parties, terms",
                    required=False,
                    default="summary"
                )
            ],
            category="analysis",
            version="1.0.0"
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行合同分析"""
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
            
            contract_id = kwargs.get("contract_id")
            analysis_type = kwargs.get("analysis_type", "summary")
            
            # TODO: 实现实际的合同分析逻辑
            
            result_data = {
                "contract_id": contract_id,
                "analysis_type": analysis_type,
                "summary": "合同分析结果摘要",
                "key_clauses": [],
                "parties": [],
                "status": "completed"
            }
            
            return ToolResult(
                success=True,
                data=result_data,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"执行合同分析时发生错误: {str(e)}",
                execution_time=time.time() - start_time
            )

