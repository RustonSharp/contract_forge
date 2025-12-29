"""
Langdock 工具使用示例
"""

import asyncio
from backend.utils.langdock import get_registry, RiskAssessmentTool, ContractAnalysisTool
from backend.utils.langdock.initialize import initialize_default_tools


async def example_usage():
    """使用示例"""
    # 1. 初始化默认工具
    registry = initialize_default_tools()
    
    # 2. 列出所有已注册的工具
    print("\n=== 已注册的工具 ===")
    tools = registry.list_tools()
    for tool_info in tools:
        print(f"- {tool_info.display_name} ({tool_info.name})")
        print(f"  描述: {tool_info.description}")
        print(f"  参数: {[p.name for p in tool_info.parameters]}")
    
    # 3. 执行风险评估工具
    print("\n=== 执行风险评估工具 ===")
    risk_tool = registry.get("risk_assessment")
    if risk_tool:
        result = await risk_tool.execute(
            contract_id="test_contract_001",
            risk_types=["legal", "financial"],
            severity_threshold="high"
        )
        print(f"执行结果: {result.success}")
        if result.success:
            print(f"数据: {result.data}")
        else:
            print(f"错误: {result.error}")
    
    # 4. 执行合同分析工具
    print("\n=== 执行合同分析工具 ===")
    analysis_tool = registry.get("contract_analysis")
    if analysis_tool:
        result = await analysis_tool.execute(
            contract_id="test_contract_001",
            analysis_type="summary"
        )
        print(f"执行结果: {result.success}")
        if result.success:
            print(f"数据: {result.data}")
        else:
            print(f"错误: {result.error}")
    
    # 5. 注册自定义工具
    print("\n=== 注册自定义工具 ===")
    # 这里可以注册你自己的工具
    # custom_tool = YourCustomTool()
    # registry.register(custom_tool)


if __name__ == "__main__":
    asyncio.run(example_usage())

