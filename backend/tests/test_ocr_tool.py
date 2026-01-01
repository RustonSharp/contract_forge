"""
OCR 解析工具测试
测试 PaddleOCR 识别功能
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.service.tools.core_tools import OCRParserTool


class TestOCRParserTool:
    """OCR 解析工具测试类"""
    
    @pytest.fixture
    def ocr_tool(self):
        """创建 OCR 工具实例"""
        return OCRParserTool()
    
    @pytest.fixture
    def test_image_path(self):
        """获取测试图片路径"""
        # 使用项目根目录下的测试图片
        project_root = Path(__file__).resolve().parent.parent.parent
        test_image = project_root / "Screenshot 2025-12-31 at 19.44.08.png"
        
        # 如果根目录不存在，尝试 uploads 目录
        if not test_image.exists():
            test_image = project_root / "uploads" / "2025-12-31" / "Screenshot 2025-12-31 at 19.44.08.png"
        
        return str(test_image) if test_image.exists() else None
    
    def test_tool_info(self, ocr_tool):
        """测试工具信息"""
        info = ocr_tool.get_info()
        assert info.name == "ocr_parser"
        assert info.display_name == "OCR 解析工具"
        assert len(info.parameters) == 2
    
    def test_parameter_validation(self, ocr_tool):
        """测试参数验证"""
        # 缺少必需参数
        result = ocr_tool.validate_parameters()
        assert result[0] == False
        assert "image_path" in result[1]
    
    def test_invalid_file_path(self, ocr_tool):
        """测试无效文件路径"""
        import asyncio
        result = asyncio.run(ocr_tool.execute(image_path="nonexistent_file.png"))
        assert result.success == False
        assert "不存在" in result.error
    
    @pytest.mark.asyncio
    async def test_ocr_recognition_with_test_image(self, ocr_tool, test_image_path):
        """测试实际 OCR 识别（如果有测试图片）"""
        if test_image_path is None:
            pytest.skip("测试图片不存在，跳过 OCR 识别测试")
        
        result = await ocr_tool.execute(image_path=test_image_path, language="zh")
        
        if result.success:
            assert "recognized_text" in result.data
            assert len(result.data["recognized_text"]) > 0
            assert result.data["language"] == "zh"
        else:
            # 如果失败，可能是 PaddleOCR 未安装或初始化失败
            assert "PaddleOCR" in result.error or "初始化" in result.error or "安装" in result.error
    
    @pytest.mark.asyncio
    async def test_ocr_engine_singleton_pattern(self, ocr_tool):
        """测试 OCR 引擎单例模式"""
        # 多次调用应该使用同一个引擎实例
        engine1 = OCRParserTool._try_init_ocr()
        engine2 = OCRParserTool._try_init_ocr()
        
        # 如果引擎初始化成功，应该是同一个实例
        if engine1 is not None and engine2 is not None:
            assert engine1 is engine2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
