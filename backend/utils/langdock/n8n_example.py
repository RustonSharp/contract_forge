"""
N8N 工作流触发工具使用示例
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import asyncio
from backend.utils.langdock import get_registry
from backend.utils.langdock.initialize import initialize_default_tools


async def example_n8n_workflow_trigger():
    """N8N 工作流触发工具示例"""
    print("=== N8N 工作流触发工具示例 ===\n")
    
    registry = get_registry()
    tool = registry.get("n8n_workflow_trigger")
    
    if not tool:
        print("N8N 工作流触发工具未注册")
        return
    

    
    # 示例2: 使用文件名触发工作流
    print("示例2: 使用文件名触发工作流")
    result = await tool.run({
        "file_name": "4ed6db58-ff05-4b8a-b2a6-e6496b8072b0_test_contract.pdf"
    })
    
    if result.success:
        print(f"✓ 工作流触发成功")
        print(f"文件名: {result.data.get('file_name')}")
    else:
        print(f"✗ 工作流触发失败: {result.error}")
    print()



async def example_llm_usage_scenario():
    """模拟大模型使用场景"""
    print("=== 大模型使用场景示例 ===\n")
    
    print("场景: 用户说'处理合同文件 4ed6db58-ff05-4b8a-b2a6-e6496b8072b0_test_contract.pdf'")
    print("大模型应该识别这是一个泛泛的处理请求，使用 N8N 工作流触发工具\n")
    
    registry = get_registry()
    tool = registry.get("n8n_workflow_trigger")
    
    if tool:
        # 模拟大模型调用
        result = await tool.execute(
            file_name="4ed6db58-ff05-4b8a-b2a6-e6496b8072b0_test_contract.pdf"
        )
        
        if result.success:
            print("✓ 大模型成功触发 N8N 工作流")
            print(f"工作流将自动执行以下步骤:")
            print("  1. 文档解析")
            print("  2. 合规校验")
            print("  3. 风险评估")
            print("  4. 根据风险等级进行分支处理")
        else:
            print(f"✗ 触发失败: {result.error}")
    print()


if __name__ == "__main__":
    # 初始化工具
    initialize_default_tools()
    
    print("=" * 50)
    print("N8N 工作流触发工具使用示例")
    print("=" * 50)
    print()
    
    # 检查环境变量
    n8n_api = os.getenv("N8N_API")
    if n8n_api:
        print(f"✓ 检测到 N8N_API 环境变量: {n8n_api}\n")
    else:
        print("⚠ 未检测到 N8N_API 环境变量，将使用默认值\n")
        print("提示: 在 .env 文件中设置 N8N_API=http://your-n8n-instance:5678\n")
    
    # 运行示例
    asyncio.run(example_n8n_workflow_trigger())
    # asyncio.run(example_llm_usage_scenario())

