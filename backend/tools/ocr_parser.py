"""
OCR 解析工具
支持图片类合同识别（JPEG、PNG等）
"""
import sys
import os
from typing import Dict, Any
import re

# 添加当前目录到模块搜索路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from base import BaseTool

# 注意：实际生产环境应使用真实的 OCR 库，如：
# - pytesseract (Tesseract OCR)
# - paddleocr
# - 或调用 OCR API 服务
# 这里提供一个模拟实现

class OCRParser(BaseTool):
    name = "OCRParser"
    description = "使用 OCR 技术识别图片类合同并提取文本"

    def run(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行 OCR 识别
        
        Args:
            input_data: 包含 file_path 的字典
            context: 上下文信息
            
        Returns:
            包含 raw_text 和 structured_data 的字典
        """
        file_path = input_data.get("file_path")
        if not file_path:
            return self._format_error("缺少文件路径", "400")
        
        file_type = file_path.split('.')[-1].lower()
        
        # 检查是否为支持的图片格式
        if file_type not in ["jpeg", "jpg", "png", "bmp", "tiff"]:
            return self._format_error(f"不支持的图片格式: {file_type}", "400")
        
        try:
            # TODO: 实际实现应调用 OCR 库
            # 示例：使用 pytesseract
            # from PIL import Image
            # import pytesseract
            # image = Image.open(file_path)
            # raw_text = pytesseract.image_to_string(image, lang='chi_sim+eng')
            
            # 模拟 OCR 识别结果（实际应替换为真实 OCR 调用）
            raw_text = self._mock_ocr(file_path)
            
            # 调用 LLM 进行结构化提取
            structured_data = self._llm_extract(raw_text)
            
            return self._format_success({
                "raw_text": raw_text,
                "structured_data": structured_data
            })
            
        except Exception as e:
            return self._format_error(f"OCR 识别失败: {str(e)}")
    
    def _mock_ocr(self, file_path: str) -> str:
        """
        模拟 OCR 识别结果
        实际应替换为真实的 OCR 调用
        """
        # 这里返回一个模拟的合同文本
        # 实际实现应读取图片文件并使用 OCR 库识别
        return """合同编号：HT-2025-001
        
甲方：XX 有限公司
乙方：YY 科技有限公司

合同标的：设备采购合同
合同金额：人民币100万元

违约责任：
1. 如甲方逾期付款，应按日支付合同总金额的0.05%作为违约金。
2. 如乙方逾期交货，应按日支付合同总金额的0.05%作为违约金。

诉讼时效：本合同争议的诉讼时效为3年。

争议解决：双方因本合同发生争议，应协商解决；协商不成的，提交北京仲裁委员会仲裁。
"""
    
    def _llm_extract(self, text: str) -> Dict[str, Any]:
        """
        从 OCR 识别的文本中提取结构化信息
        实际应调用 LLM API
        """
        # 简单的文本提取逻辑（实际应使用 LLM）
        structured_data = {
            "subject": "设备采购合同",
            "price": "100万元",
            "sign_parties": [],
            "obligations": [],
            "breach_responsibility": [],
            "dispute_resolution": [],
            "validity_period": []
        }
        
        # 提取金额
        price_match = re.search(r'(\d+(?:\.\d+)?)\s*万元', text)
        if price_match:
            structured_data["price"] = f"{price_match.group(1)}万元"
        
        # 提取违约金比例
        breach_match = re.search(r'违约金.*?(\d+(?:\.\d+)?)%', text)
        if breach_match:
            structured_data["breach_responsibility"] = [f"违约金为合同总金额的{breach_match.group(1)}%"]
        
        # 提取诉讼时效
        statute_match = re.search(r'诉讼时效.*?(\d+)\s*年', text)
        if statute_match:
            structured_data["validity_period"] = [f"诉讼时效为{statute_match.group(1)}年"]
        
        # 提取争议解决方式
        if "仲裁" in text and "诉讼" in text:
            structured_data["dispute_resolution"] = ["同时约定仲裁和诉讼"]
        elif "仲裁" in text:
            structured_data["dispute_resolution"] = ["提交仲裁"]
        elif "诉讼" in text or "法院" in text:
            structured_data["dispute_resolution"] = ["提交法院诉讼"]
        
        return structured_data
    
    def _format_success(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "success",
            "data": data
        }
    
    def _format_error(self, message: str, status_code: str = "500") -> Dict[str, Any]:
        return {
            "status": "error",
            "message": message,
            "status_code": status_code
        }

if __name__ == "__main__":
    # 测试 OCR 工具
    ocr = OCRParser()
    result = ocr.run({"file_path": "test_contract.jpg"}, {})
    print(result)

