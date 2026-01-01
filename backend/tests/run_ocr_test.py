"""
简单的 OCR 测试运行脚本
不需要 pytest，可以直接运行
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from backend.service.tools.core_tools import OCRParserTool


async def test_ocr_basic():
    """基本 OCR 测试"""
    print("=" * 60)
    print("OCR 识别工具测试")
    print("=" * 60)
    
    # 创建工具实例
    ocr_tool = OCRParserTool()
    
    # 测试1: 检查工具信息
    print("\n[测试1] 检查工具信息...")
    info = ocr_tool.get_info()
    print(f"  工具名称: {info.name}")
    print(f"  显示名称: {info.display_name}")
    print(f"  参数数量: {len(info.parameters)}")
    print("  ✓ 工具信息测试通过")
    
    # 测试2: 测试参数验证
    print("\n[测试2] 测试参数验证...")
    result = await ocr_tool.execute()
    if not result.success:
        print(f"  ✓ 参数验证测试通过（正确拒绝了缺少参数）")
        print(f"  错误信息: {result.error[:100]}...")
    else:
        print("  ✗ 参数验证测试失败（应该拒绝缺少参数）")
    
    # 测试3: 测试无效文件路径
    print("\n[测试3] 测试无效文件路径...")
    result = await ocr_tool.execute(image_path="nonexistent_file.png")
    if not result.success:
        print(f"  ✓ 无效文件路径测试通过")
        print(f"  错误信息: {result.error[:100]}...")
    else:
        print("  ✗ 无效文件路径测试失败")
    
    # 测试4: 测试实际 OCR 识别（使用项目根目录的测试图片）
    print("\n[测试4] 测试实际 OCR 识别...")
    project_root = Path(__file__).resolve().parent.parent.parent
    # 优先使用项目根目录的测试图片
    test_image = project_root / "Screenshot 2025-12-31 at 19.44.08.png"
    
    # 如果根目录不存在，尝试 uploads 目录
    if not test_image.exists():
        test_image = project_root / "uploads" / "2025-12-31" / "Screenshot 2025-12-31 at 19.44.08.png"
    
    if test_image.exists():
        print(f"  使用测试图片: {test_image}")
        result = await ocr_tool.execute(image_path=str(test_image), language="zh")
        
        if result.success:
            data = result.data if hasattr(result, 'data') else {}
            recognized_text = data.get('recognized_text', '')
            text_length = data.get('text_length', 0)
            
            print(f"  ✓ OCR 识别成功")
            print(f"  识别文本长度: {text_length} 字符")
            print(f"  识别文本预览: {recognized_text[:200]}...")
        else:
            print(f"  ✗ OCR 识别失败")
            print(f"  错误信息: {result.error[:200]}...")
    else:
        print("  ⚠ 测试图片不存在，跳过 OCR 识别测试")
        print(f"  查找路径: {test_image}")
    
    # 测试5: 测试 OCR 引擎单例模式
    print("\n[测试5] 测试 OCR 引擎单例模式...")
    OCRParserTool._ocr_instance = None
    OCRParserTool._ocr_initialized = False
    OCRParserTool._ocr_init_failed = False
    
    engine1 = OCRParserTool._try_init_ocr()
    engine2 = OCRParserTool._try_init_ocr()
    
    if engine1 is not None and engine2 is not None and engine1 is engine2:
        print("  ✓ OCR 引擎单例模式测试通过（引擎只初始化一次）")
    elif engine1 is None:
        print("  ⚠ OCR 引擎初始化失败（可能 PaddleOCR 未安装）")
    else:
        print("  ✗ OCR 引擎单例模式测试失败")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_ocr_basic())

