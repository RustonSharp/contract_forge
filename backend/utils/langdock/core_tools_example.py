"""
核心工具使用示例
演示如何使用 run(input, context) 标准接口
"""

import asyncio
from backend.utils.langdock import get_registry
from backend.utils.langdock.initialize import initialize_default_tools


async def example_document_parser():
    """文档解析工具示例"""
    print("=== 文档解析工具示例 ===\n")
    
    registry = get_registry()
    tool = registry.get("document_parser")
    
    if not tool:
        print("文档解析工具未注册")
        return
    
    # 使用 run 接口
    input_data = {
        "file_path": "./test_contract.pdf",  # 替换为实际文件路径
        "extract_structure": True
    }
    
    result = await tool.run(input_data)
    
    if result.success:
        print(f"✓ 解析成功")
        print(f"文件类型: {result.data.get('file_type')}")
        print(f"文本长度: {result.data.get('text_length')} 字符")
        print(f"执行时间: {result.execution_time:.2f} 秒")
        print(f"\n文本内容预览（前200字符）:")
        print(result.data.get('text_content', '')[:200])
    else:
        print(f"✗ 解析失败: {result.error}")


async def example_ocr_parser():
    """OCR 解析工具示例"""
    print("\n=== OCR 解析工具示例 ===\n")
    
    registry = get_registry()
    tool = registry.get("ocr_parser")
    
    if not tool:
        print("OCR 解析工具未注册")
        return
    
    # 使用 run 接口
    input_data = {
        "image_path": "./contract_image.jpg",  # 替换为实际图片路径
        "language": "zh+en"
    }
    
    result = await tool.run(input_data)
    
    if result.success:
        print(f"✓ OCR 识别成功")
        print(f"识别文本长度: {result.data.get('text_length')} 字符")
        print(f"执行时间: {result.execution_time:.2f} 秒")
        print(f"\n识别文本:")
        print(result.data.get('recognized_text', ''))
    else:
        print(f"✗ OCR 识别失败: {result.error}")


async def example_regulation_search():
    """法规检索工具示例"""
    print("\n=== 法规检索工具示例 ===\n")
    
    registry = get_registry()
    tool = registry.get("regulation_search")
    
    if not tool:
        print("法规检索工具未注册")
        return
    
    # 使用 run 接口
    input_data = {
        "keywords": "合同, 违约责任, 解除",
        "max_results": 5
    }
    
    result = await tool.run(input_data)
    
    if result.success:
        print(f"✓ 检索成功")
        print(f"找到 {result.data.get('total_results')} 条法规")
        print(f"执行时间: {result.execution_time:.2f} 秒")
        print(f"\n法规列表:")
        for reg in result.data.get('regulations', []):
            print(f"\n- {reg.get('title')}")
            print(f"  {reg.get('content')}")
            print(f"  分类: {reg.get('category')}")
    else:
        print(f"✗ 检索失败: {result.error}")


async def example_risk_assessment():
    """风险评估工具示例"""
    print("\n=== 风险评估工具示例 ===\n")
    
    registry = get_registry()
    tool = registry.get("risk_assessment")
    
    if not tool:
        print("风险评估工具未注册")
        return
    
    # 使用 run 接口
    input_data = {
        "contract_text": """
        本合同由甲方（供应商）与乙方（采购方）签订。
        甲方应于合同签订后30日内交付货物。
        如甲方延迟交付，应支付违约金，违约金为合同总金额的10%。
        本合同自双方签字盖章之日起生效。
        """,
        "risk_types": ["legal", "financial"]
    }
    
    result = await tool.run(input_data)
    
    if result.success:
        print(f"✓ 风险评估完成")
        print(f"总体风险等级: {result.data.get('overall_risk_level')}")
        print(f"执行时间: {result.execution_time:.2f} 秒")
        print(f"\n风险详情:")
        for risk in result.data.get('risks', []):
            print(f"\n- 风险类型: {risk.get('type')}")
            print(f"  严重程度: {risk.get('severity')}")
            print(f"  描述: {risk.get('description')}")
            if risk.get('conflicting_clauses'):
                print(f"  冲突条款: {', '.join(risk.get('conflicting_clauses', []))}")
            print(f"  建议: {risk.get('recommendation')}")
    else:
        print(f"✗ 风险评估失败: {result.error}")


async def example_workflow():
    """完整工作流示例：文档解析 -> 法规检索 -> 风险评估"""
    print("\n=== 完整工作流示例 ===\n")
    
    registry = get_registry()
    
    # 1. 解析文档
    doc_tool = registry.get("document_parser")
    if doc_tool:
        print("步骤1: 解析文档...")
        doc_result = await doc_tool.run({
            "file_path": "./test_contract.pdf",
            "extract_structure": True
        })
        
        if doc_result.success:
            contract_text = doc_result.data.get('text_content', '')
            print(f"✓ 文档解析成功，提取文本长度: {len(contract_text)} 字符\n")
            
            # 2. 检索相关法规
            reg_tool = registry.get("regulation_search")
            if reg_tool:
                print("步骤2: 检索相关法规...")
                keywords = "合同, 违约, 责任"  # 可以从合同文本中提取
                reg_result = await reg_tool.run({
                    "keywords": keywords,
                    "max_results": 3
                })
                
                if reg_result.success:
                    regulations = reg_result.data.get('regulations', [])
                    print(f"✓ 找到 {len(regulations)} 条相关法规\n")
                    
                    # 3. 风险评估
                    risk_tool = registry.get("risk_assessment")
                    if risk_tool:
                        print("步骤3: 进行风险评估...")
                        risk_result = await risk_tool.run({
                            "contract_text": contract_text[:1000],  # 限制长度
                            "regulations": regulations,
                            "risk_types": ["legal", "financial"]
                        })
                        
                        if risk_result.success:
                            print(f"✓ 风险评估完成")
                            print(f"总体风险等级: {risk_result.data.get('overall_risk_level')}")
                        else:
                            print(f"✗ 风险评估失败: {risk_result.error}")
                else:
                    print(f"✗ 法规检索失败: {reg_result.error}")
        else:
            print(f"✗ 文档解析失败: {doc_result.error}")


if __name__ == "__main__":
    # 初始化工具
    initialize_default_tools()
    
    print("=" * 50)
    print("核心工具使用示例")
    print("=" * 50)
    
    # 运行示例
    # asyncio.run(example_document_parser())
    # asyncio.run(example_ocr_parser())
    asyncio.run(example_regulation_search())
    asyncio.run(example_risk_assessment())
    # asyncio.run(example_workflow())

