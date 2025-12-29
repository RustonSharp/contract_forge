"""
工具数据模型定义
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    """工具参数定义"""
    name: str = Field(..., description="参数名称")
    type: str = Field(..., description="参数类型，如 string, integer, boolean 等")
    description: str = Field(..., description="参数描述")
    required: bool = Field(default=True, description="是否必需")
    default: Optional[Any] = Field(default=None, description="默认值")


class ToolInfo(BaseModel):
    """工具信息"""
    name: str = Field(..., description="工具名称，唯一标识符")
    display_name: str = Field(..., description="工具显示名称")
    description: str = Field(..., description="工具功能描述")
    parameters: List[ToolParameter] = Field(default_factory=list, description="工具参数列表")
    category: Optional[str] = Field(default=None, description="工具分类")
    version: str = Field(default="1.0.0", description="工具版本")


class ToolResult(BaseModel):
    """工具执行结果"""
    success: bool = Field(..., description="是否执行成功")
    data: Optional[Any] = Field(default=None, description="执行结果数据")
    error: Optional[str] = Field(default=None, description="错误信息")
    execution_time: Optional[float] = Field(default=None, description="执行时间（秒）")

