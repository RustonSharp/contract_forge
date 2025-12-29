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
    
    # 示例1: 使用合同ID触发工作流
    print("示例1: 使用合同ID触发工作流")
    result = await tool.run({
        "contract_id": "contract-20250101-001"
    })
    
    if result.success:
        print(f"✓ 工作流触发成功")
        print(f"合同ID: {result.data.get('contract_id')}")
        print(f"Webhook URL: {result.data.get('webhook_url')}")
        print(f"N8N 响应: {result.data.get('n8n_response')}")
        print(f"执行时间: {result.execution_time:.2f} 秒")
    else:
        print(f"✗ 工作流触发失败: {result.error}")
    print()
    
    # 示例2: 指定文件路径
    print("示例2: 指定文件路径触发工作流")
    result = await tool.run({
        "contract_id": "contract-20250101-002",
        "file_path": "./uploads/contract-20250101-002.pdf"
    })
    
    if result.success:
        print(f"✓ 工作流触发成功")
        print(f"文件路径: {result.data.get('file_path')}")
    else:
        print(f"✗ 工作流触发失败: {result.error}")
    print()
    
    # 示例3: 使用自定义工作流路径
    print("示例3: 使用自定义工作流路径")
    result = await tool.run({
        "contract_id": "contract-20250101-003",
        "workflow_path": "/webhook/custom-workflow"
    })
    
    if result.success:
        print(f"✓ 工作流触发成功")
        print(f"Webhook URL: {result.data.get('webhook_url')}")
    else:
        print(f"✗ 工作流触发失败: {result.error}")
    print()


async def example_llm_usage_scenario():
    """模拟大模型使用场景"""
    print("=== 大模型使用场景示例 ===\n")
    
    print("场景: 用户说'处理合同文件 contract-20250101-001'")
    print("大模型应该识别这是一个泛泛的处理请求，使用 N8N 工作流触发工具\n")
    
    registry = get_registry()
    tool = registry.get("n8n_workflow_trigger")
    
    if tool:
        # 模拟大模型调用
        result = await tool.execute(
            contract_id="contract-20250101-001"
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

