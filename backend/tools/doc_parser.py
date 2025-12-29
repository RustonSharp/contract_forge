# 常规文档解析工具
try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

try:
    from docx import Document
except Exception:
    Document = None
import sys
import os

# 添加当前目录到模块搜索路径，以便导入base模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from base import BaseTool

class ContractParser(BaseTool):
    name = "ContractParser"
    description = "解析合同文档并提取结构化信息"

    def run(self, input_data: dict, context: dict) -> dict:
        file_path = input_data.get("file_path")
        if not file_path:
            return self._format_error("缺少文件路径", "400")
        
        file_type = file_path.split('.')[-1].lower()
        
        try:
            # 1. 提取纯文本
            raw_text = ""
            if file_type == "pdf":
                if fitz:
                    with fitz.open(file_path) as doc:
                        for page in doc:
                            raw_text += page.get_text()
                else:
                    raw_text = self._mock_text()
            elif file_type in ["doc", "docx"]:
                if Document:
                    doc = Document(file_path)
                    raw_text = "\n".join([p.text for p in doc.paragraphs])
                else:
                    raw_text = self._mock_text()
            elif file_type in ["jpeg", "jpg", "png"]:  # 添加对图片格式的支持
                # 对于图片格式，我们可能需要OCR处理
                # 这里暂时返回提示信息
                return self._format_error("图片格式需要OCR处理，暂不支持", "400")
            else:
                return self._format_error("暂不支持的文件格式", "400")

            # 2. 调用 LLM 进行结构化（伪代码，实际需接 OpenAI/Anthropic）
            # 这一步对应 req.md 3.1：提取签约主体、金额、违约金等
            structured_data = self._llm_extract(raw_text)
            
            return self._format_success({
                "raw_text": raw_text,
                "structured_data": structured_data
            })
        except Exception as e:
            return self._format_error(str(e))

    def _llm_extract(self, text: str):
        # 此处 Prompt 应严格遵循 req.md 中的 JSON 返回格式要求
        return {
            "subject": "设备采购合同",
            "price": "100万元",
            "sign_parties": [{"name": "甲方", "type": "enterprise"}],
            "obligations": ["甲方负责提供资金", "乙方负责提供设备"],
            "breach_responsibility": ["违约金为合同总额的10%"],
            "dispute_resolution": ["协商解决，不成提交仲裁"],
            "validity_period": ["合同有效期为一年"]
        }
    
    def _format_success(self, data):
        return {
            "status": "success",
            "data": data
        }
    
    def _format_error(self, message, status_code="500"):
        return {
            "status": "error",
            "message": message,
            "status_code": status_code
        }

    def _mock_text(self) -> str:
        """当依赖未安装或读取失败时返回的模拟文本，便于 MVP 演示"""
        return """合同编号：HT-2025-001
甲方：A 公司
乙方：B 公司
标的：设备采购，金额 100 万元
违约金：逾期付款每日 0.05%，逾期交付每日 0.05%
诉讼时效：3 年
争议解决：提交仲裁"""

if __name__ == "__main__":
    parser = ContractParser()
    # 使用示例路径，实际使用时需要替换为有效路径
    path = "test_contract.pdf"  # 修正路径
    print(parser.run({"file_path": path}, {}))
