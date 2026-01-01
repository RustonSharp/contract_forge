"""
核心工具实现
包括：文档解析、OCR、法规检索、风险评估、合规校验
"""

import time
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
import json

from backend.service.tools.base import BaseTool
from backend.service.tools.models import ToolInfo, ToolParameter, ToolResult
from backend.utils.logger import get_logger


def _convert_to_relative_path(file_path: str, uploads_dir: str = "./uploads") -> str:
    """
    将文件路径转换为相对路径（相对于 uploads 目录）
    
    Args:
        file_path: 文件路径（可以是绝对路径、相对路径或文件名）
        uploads_dir: uploads 目录路径，默认为 "./uploads"
    
    Returns:
        相对路径（如 "2025-12-29/test_contract.pdf"），如果无法转换则返回原始路径
    """
    uploads_path = Path(uploads_dir).resolve()
    file_path_obj = Path(file_path)
    
    # 如果是绝对路径，尝试转换为相对路径
    if file_path_obj.is_absolute():
        try:
            relative = file_path_obj.relative_to(uploads_path)
            return str(relative).replace("\\", "/")
        except ValueError:
            # 不在 uploads 目录下，返回原始路径
            pass
    
    # 如果不是绝对路径，可能是相对于 uploads 的路径，直接返回（统一使用 / 作为分隔符）
    return str(file_path).replace("\\", "/")


def find_file_in_uploads(file_path: str, uploads_dir: str = "./uploads") -> Optional[str]:
    """
    在 uploads 目录中查找文件
    
    支持以下查找方式：
    1. 如果 file_path 是绝对路径且存在，直接返回
    2. 如果 file_path 是相对路径且存在（相对于当前工作目录），直接返回
    3. 如果 file_path 包含路径分隔符（如 "2025-12-29/test.pdf"），尝试在 uploads 目录下查找
    4. 如果只是文件名，在 uploads 目录下查找：
       - 精确匹配文件名
       - 匹配文件名（忽略扩展名）
       - 匹配包含该文件名的文件
    
    Args:
        file_path: 文件路径或文件名（支持相对路径，如 "2025-12-29/test.pdf"，相对于 uploads 目录）
        uploads_dir: uploads 目录路径，默认为 "./uploads"
    
    Returns:
        找到的文件完整路径，如果未找到返回 None
    """
    # 如果是绝对路径且存在，直接返回
    if os.path.isabs(file_path) and os.path.exists(file_path):
        return file_path
    
    # 如果是相对路径且存在（相对于当前工作目录），直接返回
    if os.path.exists(file_path):
        return os.path.abspath(file_path)
    
    # 在 uploads 目录中查找
    uploads_path = Path(uploads_dir)
    if not uploads_path.exists():
        return None
    
    # 如果 file_path 包含路径分隔符（相对路径，如 "2025-12-29/test.pdf"），尝试在 uploads 目录下查找
    if "/" in file_path or "\\" in file_path:
        relative_path = uploads_path / file_path
        if relative_path.exists() and relative_path.is_file():
            return str(relative_path.resolve())
    
    file_name = Path(file_path).name
    file_stem = Path(file_path).stem  # 不带扩展名的文件名
    
    # 1. 精确匹配文件名（在 uploads 根目录下）
    exact_match = uploads_path / file_name
    if exact_match.exists() and exact_match.is_file():
        return str(exact_match.resolve())
    
    # 2. 递归查找：在所有子目录中查找文件名
    for file in uploads_path.rglob(file_name):
        if file.is_file():
            return str(file.resolve())
    
    # 3. 匹配文件名（忽略扩展名）
    for file in uploads_path.rglob(f"{file_stem}.*"):
        if file.is_file():
            return str(file.resolve())
    
    # 4. 匹配文件名开头（适用于 UUID 开头的文件名）
    # 例如：contract_id = "172c63a7-8698-49aa-89c8-cbc316e446b1"
    # 可以匹配 "172c63a7-8698-49aa-89c8-cbc316e446b1_test_contract.pdf"
    for file in uploads_path.rglob(f"{file_name}*"):
        if file.is_file() and file.name.startswith(file_name):
            return str(file.resolve())
    
    # 5. 匹配包含该文件名的文件（部分匹配）
    for file in uploads_path.rglob(f"*{file_name}*"):
        if file.is_file() and file_name in file.name:
            return str(file.resolve())
    
    return None


class DocumentParserTool(BaseTool):
    """文档解析工具 - 支持 docx/pdf 文本提取"""
    
    def get_info(self) -> ToolInfo:
        return ToolInfo(
            name="document_parser",
            display_name="文档解析工具",
            description="解析合同文档（支持 docx/pdf 格式），提取结构化文本内容",
            parameters=[
                ToolParameter(
                    name="file_path",
                    type="string",
                    description="文档文件路径或文件名（支持 .docx 和 .pdf 格式）。可以是完整路径，或仅文件名（程序会在 uploads 目录下自动查找）",
                    required=True
                ),
                ToolParameter(
                    name="extract_structure",
                    type="boolean",
                    description="是否提取结构化信息（章节、段落等）",
                    required=False,
                    default=True
                )
            ],
            category="document",
            version="1.0.0"
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行文档解析"""
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
            
            file_path = kwargs.get("file_path")
            extract_structure = kwargs.get("extract_structure", True)
            
            # 获取项目根目录的 uploads 目录路径（用于后续相对路径转换）
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            uploads_dir = project_root / "uploads"
            
            # 查找文件（支持文件名自动查找）
            resolved_path = find_file_in_uploads(file_path)
            if not resolved_path:
                # 尝试查找项目根目录下的 uploads
                resolved_path = find_file_in_uploads(file_path, str(uploads_dir))
            
            if not resolved_path:
                return ToolResult(
                    success=False,
                    error=f"文件不存在: {file_path}。已尝试在 uploads 目录下查找，未找到匹配的文件。",
                    execution_time=time.time() - start_time
                )
            
            # 使用找到的文件路径
            absolute_file_path = resolved_path
            
            # 保存原始输入路径（可能是相对路径）
            original_file_path = kwargs.get("file_path")
            
            # 转换为相对路径（相对于 uploads 目录）
            # 使用项目根目录的 uploads
            relative_file_path = _convert_to_relative_path(absolute_file_path, str(uploads_dir))
            
            # 获取文件扩展名
            file_ext = Path(absolute_file_path).suffix.lower()
            
            # 如果原始输入已经是相对路径格式，优先使用原始输入
            if original_file_path and ("/" in original_file_path or "\\" in original_file_path):
                if not Path(original_file_path).is_absolute():
                    # 原始输入是相对路径，使用它
                    relative_file_path = original_file_path.replace("\\", "/")
            
            # 解析文档
            text_content = ""
            structure = {}
            
            if file_ext == ".pdf":
                # 解析 PDF
                try:
                    import fitz  # PyMuPDF
                    doc = fitz.open(absolute_file_path)
                    total_pages = len(doc)  # 在关闭文档前保存总页数
                    pages = []
                    for page_num in range(total_pages):
                        page = doc[page_num]
                        text = page.get_text()
                        pages.append({
                            "page": page_num + 1,
                            "text": text
                        })
                        text_content += f"\n\n--- 第 {page_num + 1} 页 ---\n\n{text}"
                    doc.close()
                    
                    if extract_structure:
                        structure = {
                            "total_pages": total_pages,
                            "pages": pages
                        }
                except ImportError:
                    return ToolResult(
                        success=False,
                        error="PDF 解析需要安装 PyMuPDF: pip install pymupdf",
                        execution_time=time.time() - start_time
                    )
                except Exception as e:
                    return ToolResult(
                        success=False,
                        error=f"PDF 解析失败: {str(e)}",
                        execution_time=time.time() - start_time
                    )
            
            elif file_ext == ".docx":
                # 解析 DOCX
                try:
                    from docx import Document
                    doc = Document(absolute_file_path)
                    
                    paragraphs = []
                    for para in doc.paragraphs:
                        if para.text.strip():
                            paragraphs.append(para.text)
                            text_content += para.text + "\n"
                    
                    if extract_structure:
                        structure = {
                            "total_paragraphs": len(paragraphs),
                            "paragraphs": paragraphs
                        }
                except ImportError:
                    return ToolResult(
                        success=False,
                        error="DOCX 解析需要安装 python-docx: pip install python-docx",
                        execution_time=time.time() - start_time
                    )
                except Exception as e:
                    return ToolResult(
                        success=False,
                        error=f"DOCX 解析失败: {str(e)}",
                        execution_time=time.time() - start_time
                    )
            else:
                return ToolResult(
                    success=False,
                    error=f"不支持的文件格式: {file_ext}。支持格式: .pdf, .docx",
                    execution_time=time.time() - start_time
                )
            
            result_data = {
                "file_path": relative_file_path,  # 使用相对路径
                "file_type": file_ext,
                "text_content": text_content.strip(),
                "structure": structure if extract_structure else None,
                "text_length": len(text_content),
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
                error=f"执行文档解析时发生错误: {str(e)}",
                execution_time=time.time() - start_time
            )


# ==================== OCR 引擎抽象和实现 ====================

class OCREngine(ABC):
    """OCR 引擎抽象基类"""
    
    @abstractmethod
    async def recognize(self, image_path: str, language: str = "zh") -> str:
        """
        识别图片中的文本
        
        Args:
            image_path: 图片文件路径
            language: 识别语言（zh: 中文, en: 英文）
            
        Returns:
            str: 识别出的文本内容
        """
        pass


class PaddleOCREngine(OCREngine):
    """PaddleOCR 引擎实现"""
    
    _instance = None
    _initialized = False
    _init_failed = False
    
    @classmethod
    def get_instance(cls):
        """获取 PaddleOCR 实例（单例模式）"""
        if cls._initialized and cls._instance is not None:
            return cls._instance
        
        if cls._init_failed:
            return None
        
        # 尝试从全局变量获取
        try:
            import backend.main as main_module
            if hasattr(main_module, 'global_ocr_engine') and main_module.global_ocr_engine is not None:
                cls._instance = main_module.global_ocr_engine
                cls._initialized = True
                return cls._instance
        except:
            pass
        
        # 创建新的 PaddleOCR 实例
        try:
            import os
            os.environ.setdefault('KMP_DUPLICATE_LIB_OK', 'TRUE')
            os.environ.setdefault('OBJC_DISABLE_INITIALIZE_FORK_SAFETY', 'YES')
            os.environ.setdefault('DISABLE_MODEL_SOURCE_CHECK', 'True')
            
            if cls._instance is not None:
                cls._initialized = True
                return cls._instance
            
            # 尝试修复 langchain.docstore 导入问题
            try:
                import langchain.docstore  # type: ignore
            except ImportError:
                try:
                    import langchain
                    import sys
                    if 'langchain.docstore' not in sys.modules:
                        from types import ModuleType
                        docstore_module = ModuleType('langchain.docstore')
                        sys.modules['langchain.docstore'] = docstore_module
                except ImportError:
                    pass
            
            from paddleocr import PaddleOCR
            cls._instance = PaddleOCR(use_angle_cls=True, lang='ch')
            cls._initialized = True
            logger = get_logger(__name__)
            logger.info("✓ PaddleOCR 引擎初始化成功")
            return cls._instance
        except ImportError as e:
            cls._init_failed = True
            logger = get_logger(__name__)
            error_msg = str(e)
            if 'langchain' in error_msg.lower():
                logger.error(f"PaddleOCR 依赖问题: {error_msg}")
            else:
                logger.error(f"PaddleOCR 未安装: {error_msg}")
            return None
        except Exception as e:
            error_msg = str(e)
            if 'PDX has already been initialized' in error_msg:
                if cls._instance is not None:
                    cls._initialized = True
                    return cls._instance
                try:
                    import backend.main as main_module
                    if hasattr(main_module, 'global_ocr_engine') and main_module.global_ocr_engine is not None:
                        cls._instance = main_module.global_ocr_engine
                        cls._initialized = True
                        return cls._instance
                except:
                    pass
            cls._init_failed = True
            logger = get_logger(__name__)
            logger.error(f"初始化 PaddleOCR 失败: {error_msg}")
            return None
    
    async def recognize(self, image_path: str, language: str = "zh") -> str:
        """使用 PaddleOCR 识别图片"""
        ocr_engine = self.get_instance()
        if ocr_engine is None:
            raise Exception("PaddleOCR 初始化失败")
        
        # 执行 OCR 识别
        result = ocr_engine.ocr(str(image_path))
        
        # 提取文本内容
        if result and len(result) > 0:
            lines = []
            for page_result in result:
                if page_result:
                    for line in page_result:
                        if line and len(line) >= 2:
                            text_info = line[1]
                            if isinstance(text_info, (list, tuple)) and len(text_info) >= 1:
                                text = text_info[0] if isinstance(text_info[0], str) else str(text_info[0])
                            elif isinstance(text_info, str):
                                text = text_info
                            else:
                                text = str(text_info)
                            
                            if text and text.strip():
                                lines.append(text.strip())
            return '\n'.join(lines)
        return ""


class LLMOCREngine(OCREngine):
    """使用大语言模型进行 OCR 识别的引擎实现"""
    
    # OCR 专用模型名称（可通过环境变量 OCR_MODEL_NAME 配置）
    OCR_MODEL_NAME = os.getenv("OCR_MODEL_NAME", "qwen3-omni-flash-2025-12-01")
    
    def __init__(self):
        from backend.utils.llm import get_llm_client
        self.llm_client = get_llm_client()
    
    async def recognize(self, image_path: str, language: str = "zh") -> str:
        """使用 LLM 识别图片中的文本"""
        import base64
        from pathlib import Path
        
        # 读取图片并转换为 base64
        image_path_obj = Path(image_path)
        if not image_path_obj.exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")
        
        with open(image_path, 'rb') as f:
            image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # 确定图片格式
        file_ext = image_path_obj.suffix.lower()
        mime_type = "image/jpeg"
        if file_ext in ['.png']:
            mime_type = "image/png"
        elif file_ext in ['.gif']:
            mime_type = "image/gif"
        elif file_ext in ['.webp']:
            mime_type = "image/webp"
        
        # 构建提示词
        lang_prompt = "中文" if language == "zh" else "英文"
        prompt = f"""请识别这张图片中的所有文字内容，并按照原始格式（包括换行、段落等）输出。图片中的文字是{lang_prompt}。

要求：
1. 完整识别图片中的所有文字
2. 保持原有的格式和排版
3. 如果是合同或文档，请保持段落结构
4. 只输出识别出的文字内容，不要添加任何解释或说明

请开始识别："""
        
        try:
            # 尝试使用支持视觉的模型（如 GPT-4 Vision、通义千问 VL）
            # 对于 OpenAI 兼容 API，需要直接调用底层客户端发送图片
            if hasattr(self.llm_client, 'provider') and hasattr(self.llm_client.provider, 'client'):
                try:
                    from openai import AsyncOpenAI
                    if isinstance(self.llm_client.provider.client, AsyncOpenAI):
                        # 构建包含图片的消息（OpenAI Vision API 格式）
                        vision_messages = [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:{mime_type};base64,{image_base64}"
                                        }
                                    }
                                ]
                            }
                        ]
                        
                        # 直接调用底层 API，使用 OCR 专用模型
                        ocr_model_name = self.OCR_MODEL_NAME
                        response = await self.llm_client.provider.client.chat.completions.create(
                            model=ocr_model_name,
                            messages=vision_messages,
                            temperature=0.1,
                            max_tokens=4000
                        )
                        
                        content = response.choices[0].message.content
                        if content:
                            return content.strip()
                except Exception as e:
                    # 如果底层 API 调用失败，检查是否是图片相关错误
                    error_msg = str(e)
                    if "vision" in error_msg.lower() or "image" in error_msg.lower() or "unsupported" in error_msg.lower():
                        raise Exception(f"当前 LLM 模型不支持图片识别。请使用支持视觉的模型（如 GPT-4 Vision 或通义千问 VL），或切换到 PaddleOCR 引擎。错误: {error_msg}")
                    # 如果不是图片相关错误，继续尝试其他方式
                    pass
            
            # 如果上面的方式失败，尝试使用普通文本方式（可能不支持图片）
            # 这种情况下会失败并提示用户切换引擎
            from backend.utils.llm.providers import ChatMessage
            messages = [
                ChatMessage(role="user", content=prompt),
            ]
            response = await self.llm_client.chat(messages, temperature=0.1)
            return response.content.strip()
            
        except Exception as e:
            # 如果 LLM 不支持图片或调用失败，抛出错误
            error_msg = str(e)
            if "vision" in error_msg.lower() or "image" in error_msg.lower() or "unsupported" in error_msg.lower():
                raise Exception(f"当前 LLM 模型不支持图片识别。请使用支持视觉的模型（如 GPT-4 Vision 或通义千问 VL），或切换到 PaddleOCR 引擎。错误: {error_msg}")
            raise Exception(f"LLM OCR 识别失败: {error_msg}")


def get_ocr_engine() -> OCREngine:
    """
    获取配置的 OCR 引擎
    
    通过环境变量 OCR_ENGINE 配置：
    - "llm": 使用大语言模型（默认）
    - "paddle": 使用 PaddleOCR
    
    Returns:
        OCREngine: OCR 引擎实例
    """
    engine_type = os.getenv("OCR_ENGINE", "llm").lower()
    
    if engine_type == "paddle":
        return PaddleOCREngine()
    else:  # 默认使用 LLM
        return LLMOCREngine()


class OCRParserTool(BaseTool):
    """OCR 解析工具 - 支持可配置的 OCR 引擎（默认使用 LLM）"""
    
    # 类变量：存储当前使用的 OCR 引擎
    _ocr_engine: Optional[OCREngine] = None
    _engine_type: Optional[str] = None
    
    def get_info(self) -> ToolInfo:
        # 获取当前使用的引擎类型
        engine_type = os.getenv("OCR_ENGINE", "llm").lower()
        engine_name = "大语言模型" if engine_type == "llm" else "PaddleOCR"
        
        return ToolInfo(
            name="ocr_parser",
            display_name="OCR 解析工具",
            description=f"识别图片类合同，提取文本内容（支持常见图片格式）。当前使用引擎: {engine_name}。可通过环境变量 OCR_ENGINE 配置（llm/paddle）。",
            parameters=[
                ToolParameter(
                    name="image_path",
                    type="string",
                    description="图片文件路径（支持 .jpg, .png, .jpeg, .bmp 等格式）",
                    required=True
                ),
                ToolParameter(
                    name="language",
                    type="string",
                    description="识别语言（zh: 中文, en: 英文, zh+en: 中英文）",
                    required=False,
                    default="zh"  # 默认使用中文
                )
            ],
            category="document",
            version="1.0.0"
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行 OCR 解析"""
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
            
            image_path = kwargs.get("image_path")
            language = kwargs.get("language", "zh")  # 默认使用中文
            
            # 保存原始输入路径
            original_image_path = image_path
            
            # 查找文件（支持文件名自动查找）
            resolved_path = find_file_in_uploads(image_path)
            if not resolved_path:
                # 尝试查找项目根目录下的 uploads
                project_root = Path(__file__).resolve().parent.parent.parent.parent
                uploads_dir = project_root / "uploads"
                resolved_path = find_file_in_uploads(image_path, str(uploads_dir))
            
            if not resolved_path:
                return ToolResult(
                    success=False,
                    error=f"图片文件不存在: {image_path}。已尝试在 uploads 目录下查找，未找到匹配的文件。",
                    execution_time=time.time() - start_time
                )
            
            # 使用找到的文件路径
            absolute_image_path = resolved_path
            
            # 转换为相对路径（相对于 uploads 目录）
            # 使用项目根目录的 uploads
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            uploads_dir = project_root / "uploads"
            relative_image_path = _convert_to_relative_path(absolute_image_path, str(uploads_dir))
            
            # 如果原始输入已经是相对路径格式，优先使用原始输入
            if original_image_path and ("/" in original_image_path or "\\" in original_image_path):
                if not Path(original_image_path).is_absolute():
                    # 原始输入是相对路径，使用它
                    relative_image_path = original_image_path.replace("\\", "/")
            
            # 检查文件格式
            file_ext = Path(absolute_image_path).suffix.lower()
            supported_formats = [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"]
            if file_ext not in supported_formats:
                return ToolResult(
                    success=False,
                    error=f"不支持的图片格式: {file_ext}。支持格式: {', '.join(supported_formats)}",
                    execution_time=time.time() - start_time
                )
            
            # 使用配置的 OCR 引擎进行识别
            ocr_text = ""
            try:
                # 获取当前配置的 OCR 引擎类型
                current_engine_type = os.getenv("OCR_ENGINE", "llm").lower()
                
                # 如果引擎类型改变，重新获取引擎实例
                if OCRParserTool._engine_type != current_engine_type:
                    OCRParserTool._ocr_engine = get_ocr_engine()
                    OCRParserTool._engine_type = current_engine_type
                    logger = get_logger(__name__)
                    logger.info(f"使用 OCR 引擎: {current_engine_type.upper()}")
                
                # 如果还没有初始化，获取引擎实例
                if OCRParserTool._ocr_engine is None:
                    OCRParserTool._ocr_engine = get_ocr_engine()
                    OCRParserTool._engine_type = current_engine_type
                
                # 使用引擎识别图片
                ocr_text = await OCRParserTool._ocr_engine.recognize(
                    str(absolute_image_path),
                    language=language
                )
                
                if not ocr_text or not ocr_text.strip():
                    return ToolResult(
                        success=False,
                        error="OCR 识别成功但未提取到文本内容。请检查图片是否包含文字。",
                        execution_time=time.time() - start_time
                    )
                
                # 构建返回结果
                result_data = {
                    "image_path": relative_image_path,
                    "language": language,
                    "recognized_text": ocr_text.strip(),
                    "text_length": len(ocr_text),
                    "engine": OCRParserTool._engine_type or "llm",
                    "status": "completed"
                }
                
                return ToolResult(
                    success=True,
                    data=result_data,
                    execution_time=time.time() - start_time
                )
                    
            except Exception as e:
                error_msg = str(e)
                # 如果是 LLM OCR 失败且提示不支持图片，提供更友好的错误信息
                if "不支持图片" in error_msg or "vision" in error_msg.lower():
                    return ToolResult(
                        success=False,
                        error=f"{error_msg}\n提示：可以通过设置环境变量 OCR_ENGINE=paddle 切换到 PaddleOCR 引擎。",
                        execution_time=time.time() - start_time
                    )
                return ToolResult(
                    success=False,
                    error=f"OCR 识别失败: {error_msg}",
                    execution_time=time.time() - start_time
                )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"执行 OCR 解析时发生错误: {str(e)}",
                execution_time=time.time() - start_time
            )


class RegulationSearchTool(BaseTool):
    """法规检索工具 - 接入公开法规数据库（Mock）"""
    
    def __init__(self):
        super().__init__()
        # Mock 法规数据库
        self.mock_regulations = {
            "合同": [
                {
                    "title": "《中华人民共和国民法典》第四百六十四条",
                    "content": "合同是民事主体之间设立、变更、终止民事法律关系的协议。",
                    "category": "合同法"
                },
                {
                    "title": "《中华人民共和国民法典》第四百六十五条",
                    "content": "依法成立的合同，受法律保护。依法成立的合同，仅对当事人具有法律约束力，但是法律另有规定的除外。",
                    "category": "合同法"
                }
            ],
            "违约责任": [
                {
                    "title": "《中华人民共和国民法典》第五百七十七条",
                    "content": "当事人一方不履行合同义务或者履行合同义务不符合约定的，应当承担继续履行、采取补救措施或者赔偿损失等违约责任。",
                    "category": "合同法"
                }
            ],
            "解除": [
                {
                    "title": "《中华人民共和国民法典》第五百六十三条",
                    "content": "有下列情形之一的，当事人可以解除合同：（一）因不可抗力致使不能实现合同目的；（二）在履行期限届满前，当事人一方明确表示或者以自己的行为表明不履行主要债务；",
                    "category": "合同法"
                }
            ],
            "保密": [
                {
                    "title": "《中华人民共和国反不正当竞争法》第九条",
                    "content": "经营者不得实施下列侵犯商业秘密的行为：（一）以盗窃、贿赂、欺诈、胁迫、电子侵入或者其他不正当手段获取权利人的商业秘密；",
                    "category": "反不正当竞争法"
                }
            ]
        }
    
    def get_info(self) -> ToolInfo:
        return ToolInfo(
            name="regulation_search",
            display_name="法规检索工具",
            description="检索相关法规条文，输入合同条款关键词，返回匹配的法规条文",
            parameters=[
                ToolParameter(
                    name="keywords",
                    type="string",
                    description="检索关键词（合同条款关键词，多个关键词用逗号分隔）",
                    required=True
                ),
                ToolParameter(
                    name="max_results",
                    type="integer",
                    description="最大返回结果数量",
                    required=False,
                    default=5
                )
            ],
            category="search",
            version="1.0.0"
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行法规检索"""
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
            
            keywords_str = kwargs.get("keywords", "")
            max_results = kwargs.get("max_results", 5)
            
            # 解析关键词
            keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]
            
            if not keywords:
                return ToolResult(
                    success=False,
                    error="关键词不能为空",
                    execution_time=time.time() - start_time
                )
            
            # 检索法规
            results = []
            for keyword in keywords:
                # 简单的关键词匹配（实际应该使用更复杂的检索算法）
                for reg_key, regulations in self.mock_regulations.items():
                    if keyword in reg_key or any(keyword in reg.get("title", "") or keyword in reg.get("content", "") for reg in regulations):
                        results.extend(regulations)
            
            # 去重
            seen = set()
            unique_results = []
            for reg in results:
                reg_id = reg.get("title", "")
                if reg_id not in seen:
                    seen.add(reg_id)
                    unique_results.append(reg)
            
            # 限制结果数量
            unique_results = unique_results[:max_results]
            
            result_data = {
                "keywords": keywords,
                "total_results": len(unique_results),
                "regulations": unique_results,
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
                error=f"执行法规检索时发生错误: {str(e)}",
                execution_time=time.time() - start_time
            )


class RiskAssessmentTool(BaseTool):
    """风险评估工具 - 输入合同文本+法规条文，输出风险等级+冲突条款说明"""
    
    def get_info(self) -> ToolInfo:
        return ToolInfo(
            name="risk_assessment",
            display_name="风险评估工具",
            description="分析合同文本和法规条文，识别风险等级和冲突条款",
            parameters=[
                ToolParameter(
                    name="contract_text",
                    type="string",
                    description="合同文本内容",
                    required=True
                ),
                ToolParameter(
                    name="file_path",
                    type="string",
                    description="合同文件相对路径（相对于 uploads 目录，如 '2025-12-29/test_contract.pdf'），用于在输出结果中包含文件位置信息",
                    required=False
                ),
                ToolParameter(
                    name="regulations",
                    type="array",
                    description="相关法规条文列表（可选，如果不提供则自动检索）",
                    required=False,
                    default=None
                ),
                ToolParameter(
                    name="risk_types",
                    type="array",
                    description="要评估的风险类型列表，如 ['legal', 'financial', 'operational']",
                    required=False,
                    default=["legal", "financial"]
                )
            ],
            category="analysis",
            version="1.0.0"
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行风险评估"""
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
            
            contract_text = kwargs.get("contract_text", "")
            file_path = kwargs.get("file_path")  # 获取 file_path 参数
            regulations = kwargs.get("regulations")
            risk_types = kwargs.get("risk_types", ["legal", "financial"])
            
            if not contract_text:
                return ToolResult(
                    success=False,
                    error="合同文本不能为空",
                    execution_time=time.time() - start_time
                )
            
            # 如果没有提供法规条文，尝试自动检索
            if not regulations:
                # 调用法规检索工具
                try:
                    from backend.service.tools.registry import get_registry
                    registry = get_registry()
                    regulation_tool = registry.get("regulation_search")
                    if regulation_tool:
                        keywords = self._extract_keywords(contract_text)
                        if keywords:
                            keywords_str = ", ".join(keywords)
                            search_result = await regulation_tool.execute(keywords=keywords_str, max_results=5)
                            if search_result.success and search_result.data:
                                regulations = search_result.data.get("regulations", [])
                except Exception as e:
                    print(f"自动检索法规失败: {str(e)}")
                    regulations = []
            
            # 分析风险（这里使用 LLM 进行实际分析）
            risks = await self._analyze_risks(contract_text, regulations, risk_types)
            
            # 计算总体风险等级
            overall_risk_level = self._calculate_risk_level(risks)
            
            result_data = {
                "file_path": file_path,  # 包含文件相对路径
                "contract_text_length": len(contract_text),
                "regulations_count": len(regulations) if regulations else 0,
                "risk_types_analyzed": risk_types,
                "overall_risk_level": overall_risk_level,
                "risks": risks,
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
                error=f"执行风险评估时发生错误: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _extract_keywords(self, text: str) -> List[str]:
        """从文本中提取关键词"""
        # 简化的关键词提取（实际应该使用 NLP 技术）
        keywords = []
        common_terms = ["合同", "违约", "解除", "保密", "责任", "赔偿", "期限"]
        for term in common_terms:
            if term in text:
                keywords.append(term)
        return keywords[:5]  # 返回前5个关键词
    
    async def _analyze_risks(self, contract_text: str, regulations: List[Dict], risk_types: List[str]) -> List[Dict]:
        """分析风险（使用 LLM）"""
        risks = []
        
        try:
            # 使用 LLM 进行风险分析
            from backend.utils.llm import get_llm_client, ChatMessage
            
            # 构建提示词
            regulations_text = ""
            if regulations:
                regulations_text = "\n\n相关法规条文：\n"
                for reg in regulations:
                    regulations_text += f"- {reg.get('title', '')}: {reg.get('content', '')}\n"
            
            # 限制合同文本长度避免超出 token 限制
            contract_text_limited = contract_text[:2000]
            
            prompt = f"""请分析以下合同文本，识别潜在风险。

合同文本：
{contract_text_limited}
{regulations_text}

请从以下风险类型进行分析：{', '.join(risk_types)}

请以 JSON 格式返回分析结果，包含：
1. 风险类型
2. 风险严重程度（high/medium/low）
3. 风险描述
4. 冲突条款说明（如果有）
5. 建议措施

格式示例：
{{
    "risks": [
        {{
            "type": "legal",
            "severity": "high",
            "description": "风险描述",
            "conflicting_clauses": ["冲突条款1", "冲突条款2"],
            "recommendation": "建议措施"
        }}
    ]
}}
"""
            
            client = get_llm_client()
            messages = [
                ChatMessage(
                    role="system",
                    content="你是一个专业的合同风险分析专家，擅长识别合同中的法律、财务和运营风险。"
                ),
                ChatMessage(role="user", content=prompt)
            ]
            
            response = await client.chat(messages, temperature=0.3)
            
            # 解析 LLM 响应
            import json
            import re
            response_text = response.content
            
            # 尝试提取 JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    risks = result.get("risks", [])
                except json.JSONDecodeError:
                    # 如果 JSON 解析失败，使用简化的风险分析
                    risks = self._fallback_risk_analysis(contract_text, regulations, risk_types)
            else:
                # 如果没有找到 JSON，使用简化的风险分析
                risks = self._fallback_risk_analysis(contract_text, regulations, risk_types)
                
        except Exception as e:
            # 如果 LLM 调用失败，使用简化的风险分析
            print(f"LLM 分析失败，使用简化分析: {str(e)}")
            risks = self._fallback_risk_analysis(contract_text, regulations, risk_types)
        
        return risks
    
    def _fallback_risk_analysis(self, contract_text: str, regulations: List[Dict], risk_types: List[str]) -> List[Dict]:
        """简化的风险分析（当 LLM 不可用时使用）"""
        risks = []
        
        # 简化的风险分析逻辑
        if "legal" in risk_types:
            risks.append({
                "type": "legal",
                "severity": "medium",
                "description": "合同条款可能存在法律风险，建议咨询法律顾问",
                "conflicting_clauses": [],
                "recommendation": "建议审查相关法规条文，确保合同条款符合法律规定"
            })
        
        if "financial" in risk_types:
            risks.append({
                "type": "financial",
                "severity": "low",
                "description": "财务风险较低，但需注意付款条款",
                "conflicting_clauses": [],
                "recommendation": "建议明确付款方式和时间"
            })
        
        return risks
    
    def _calculate_risk_level(self, risks: List[Dict]) -> str:
        """计算总体风险等级"""
        if not risks:
            return "low"
        
        severities = [r.get("severity", "low") for r in risks]
        if "high" in severities:
            return "high"
        elif "medium" in severities:
            return "medium"
        else:
            return "low"


# ============================================================================
# 合规校验工具
# ============================================================================

class EnterpriseInfoQueryTool(BaseTool):
    """企业信息查询工具（Mock）"""
    
    def get_info(self) -> ToolInfo:
        return ToolInfo(
            name="enterprise_info_query",
            display_name="企业信息查询工具",
            description="查询企业信息（Mock），验证企业主体状态",
            parameters=[
                ToolParameter(
                    name="enterprise_name",
                    type="string",
                    description="企业名称",
                    required=True
                ),
                ToolParameter(
                    name="credit_code",
                    type="string",
                    description="统一社会信用代码（可选，用于精确查询）",
                    required=False
                )
            ],
            category="query",
            version="1.0.0"
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行企业信息查询（Mock）"""
        start_time = time.time()
        
        try:
            is_valid, error_msg = self.validate_parameters(**kwargs)
            if not is_valid:
                return ToolResult(
                    success=False,
                    error=error_msg,
                    execution_time=time.time() - start_time
                )
            
            enterprise_name = kwargs.get("enterprise_name")
            credit_code = kwargs.get("credit_code")
            
            # Mock 企业信息查询
            # 实际应该调用国家企业信用信息公示系统 API
            mock_enterprises = {
                "XX有限公司": {
                    "name": "XX有限公司",
                    "credit_code": "91110000MA01234567",
                    "status": "存续",
                    "legal_representative": "张三",
                    "registered_capital": "1000万元"
                },
                "YY科技公司": {
                    "name": "YY科技公司",
                    "credit_code": "91110000MA09876543",
                    "status": "存续",
                    "legal_representative": "李四",
                    "registered_capital": "500万元"
                }
            }
            
            # 查找企业信息
            enterprise_info = None
            if credit_code:
                # 按信用代码查找
                for ent in mock_enterprises.values():
                    if ent.get("credit_code") == credit_code:
                        enterprise_info = ent
                        break
            else:
                # 按名称查找
                enterprise_info = mock_enterprises.get(enterprise_name)
            
            if not enterprise_info:
                # 模拟查询失败的情况
                enterprise_info = {
                    "name": enterprise_name,
                    "status": "未查询到",
                    "message": "企业信息未找到或已注销"
                }
            
            result_data = {
                "enterprise_name": enterprise_name,
                "enterprise_info": enterprise_info,
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
                error=f"执行企业信息查询时发生错误: {str(e)}",
                execution_time=time.time() - start_time
            )


class SigningSubjectComplianceTool(BaseTool):
    """规则1：合同签署主体合规校验"""
    
    def get_info(self) -> ToolInfo:
        return ToolInfo(
            name="signing_subject_compliance",
            display_name="签署主体合规校验",
            description="校验合同签署方是否具备合法签约资格，避免无权签署风险",
            parameters=[
                ToolParameter(
                    name="contract_text",
                    type="string",
                    description="合同文本内容",
                    required=True
                )
            ],
            category="compliance",
            version="1.0.0"
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行签署主体合规校验"""
        start_time = time.time()
        
        try:
            is_valid, error_msg = self.validate_parameters(**kwargs)
            if not is_valid:
                return ToolResult(
                    success=False,
                    error=error_msg,
                    execution_time=time.time() - start_time
                )
            
            contract_text = kwargs.get("contract_text", "")
            
            # 提取签署方信息
            parties = self._extract_parties(contract_text)
            
            if not parties:
                # 未提取到任何签署方信息
                return ToolResult(
                    success=True,
                    data={
                        "rule_name": "签署主体合规校验",
                        "compliance_status": "违规",
                        "risk_level": "中风险",
                        "violations": [
                            {
                                "type": "缺失签署方信息",
                                "description": "未从合同文本中提取到任何签署方信息",
                                "suggestion": "请补充签署方合法资质证明（如营业执照复印件、身份证复印件）"
                            }
                        ],
                        "parties": [],
                        "next_action": "法务人工复核",
                        "notification": "需要邮件通知"
                    },
                    execution_time=time.time() - start_time
                )
            
            # 校验每个签署方
            violations = []
            valid_parties = []
            
            for party in parties:
                party_type = party.get("type")  # "enterprise" 或 "individual"
                party_name = party.get("name")
                party_info = party.get("info", {})
                
                if party_type == "enterprise":
                    # 企业主体校验
                    credit_code = party_info.get("credit_code")
                    business_license = party_info.get("business_license")
                    
                    if not credit_code and not business_license:
                        violations.append({
                            "type": "企业主体缺少资质证明",
                            "party": party_name,
                            "description": f"企业主体 '{party_name}' 缺少统一社会信用代码或营业执照注册号",
                            "suggestion": "请补充营业执照复印件，确保包含统一社会信用代码（18位）或营业执照注册号（15位）"
                        })
                        continue
                    
                    # 验证企业状态（调用企业信息查询工具）
                    enterprise_tool = None
                    try:
                        from backend.service.tools.registry import get_registry
                        registry = get_registry()
                        enterprise_tool = registry.get("enterprise_info_query")
                    except:
                        pass
                    
                    if enterprise_tool:
                        query_result = await enterprise_tool.execute(
                            enterprise_name=party_name,
                            credit_code=credit_code
                        )
                        
                        if query_result.success:
                            enterprise_info = query_result.data.get("enterprise_info", {})
                            status = enterprise_info.get("status", "")
                            
                            if status not in ["存续", "在营"]:
                                violations.append({
                                    "type": "企业主体状态异常",
                                    "party": party_name,
                                    "description": f"企业主体 '{party_name}' 状态为 '{status}'，不符合签约要求",
                                    "suggestion": "请确认企业主体状态为'存续'或'在营'，否则合同可能无效"
                                })
                                continue
                    
                    valid_parties.append({
                        "name": party_name,
                        "type": "enterprise",
                        "status": "合规",
                        "credit_code": credit_code or business_license
                    })
                
                elif party_type == "individual":
                    # 个人主体校验
                    id_card = party_info.get("id_card")
                    adult_declaration = party_info.get("adult_declaration", False)
                    
                    if not id_card and not adult_declaration:
                        violations.append({
                            "type": "个人主体缺少资质证明",
                            "party": party_name,
                            "description": f"个人主体 '{party_name}' 缺少身份证号且无明确的成年声明",
                            "suggestion": "请补充身份证复印件，或明确声明'本人已年满18周岁'"
                        })
                        continue
                    
                    # 验证身份证号格式（18位）
                    if id_card and len(id_card) != 18:
                        violations.append({
                            "type": "身份证号格式错误",
                            "party": party_name,
                            "description": f"个人主体 '{party_name}' 的身份证号格式不正确（应为18位）",
                            "suggestion": "请确认身份证号为18位有效号码"
                        })
                        continue
                    
                    valid_parties.append({
                        "name": party_name,
                        "type": "individual",
                        "status": "合规",
                        "id_card": id_card or "已声明成年"
                    })
            
            # 判断合规状态
            compliance_status = "合规" if not violations else "违规"
            risk_level = "中风险" if violations else "无风险"
            
            result_data = {
                "rule_name": "签署主体合规校验",
                "compliance_status": compliance_status,
                "risk_level": risk_level,
                "parties": valid_parties,
                "violations": violations,
                "next_action": "法务人工复核" if violations else None,
                "notification": "需要邮件通知" if violations else None
            }
            
            return ToolResult(
                success=True,
                data=result_data,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"执行签署主体合规校验时发生错误: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _extract_parties(self, text: str) -> List[Dict]:
        """从合同文本中提取签署方信息"""
        parties = []
        
        # 提取企业主体（匹配"甲方：XX有限公司"等模式）
        enterprise_patterns = [
            r'(?:甲方|乙方|丙方|签署方)[：:]\s*([^，,。\n]+(?:有限公司|股份公司|公司|企业|集团))',
            r'([^，,。\n]+(?:有限公司|股份公司|公司|企业|集团))[：:]\s*(?:甲方|乙方|丙方)',
        ]
        
        for pattern in enterprise_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                name = match.group(1).strip()
                # 提取统一社会信用代码（18位）
                credit_code_match = re.search(r'统一社会信用代码[：:]\s*([A-Z0-9]{18})', text)
                credit_code = credit_code_match.group(1) if credit_code_match else None
                # 提取营业执照注册号（15位）
                license_match = re.search(r'营业执照[注册号]*[：:]\s*([0-9A-Z]{15})', text)
                business_license = license_match.group(1) if license_match else None
                
                parties.append({
                    "name": name,
                    "type": "enterprise",
                    "info": {
                        "credit_code": credit_code,
                        "business_license": business_license
                    }
                })
        
        # 提取个人主体（匹配"甲方：张三"等模式，排除公司名称）
        individual_patterns = [
            r'(?:甲方|乙方|丙方|签署方)[：:]\s*([^，,。\n]+(?!有限公司|股份公司|公司|企业|集团))',
        ]
        
        for pattern in individual_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                name = match.group(1).strip()
                # 排除明显是企业名称的情况
                if any(keyword in name for keyword in ["有限公司", "公司", "企业"]):
                    continue
                
                # 提取身份证号（18位）
                id_card_match = re.search(r'身份证[号]*[：:]\s*([0-9X]{18})', text)
                id_card = id_card_match.group(1) if id_card_match else None
                # 检查是否有成年声明
                adult_declaration = bool(re.search(r'(?:已年满|年满|已满)\s*18\s*周岁', text))
                
                parties.append({
                    "name": name,
                    "type": "individual",
                    "info": {
                        "id_card": id_card,
                        "adult_declaration": adult_declaration
                    }
                })
        
        # 去重
        seen = set()
        unique_parties = []
        for party in parties:
            key = (party["name"], party["type"])
            if key not in seen:
                seen.add(key)
                unique_parties.append(party)
        
        return unique_parties


class CoreClausesCompletenessTool(BaseTool):
    """规则2：合同核心条款完整性校验"""
    
    def get_info(self) -> ToolInfo:
        return ToolInfo(
            name="core_clauses_completeness",
            display_name="核心条款完整性校验",
            description="校验合同是否包含法定必备条款，避免关键信息缺失风险",
            parameters=[
                ToolParameter(
                    name="contract_text",
                    type="string",
                    description="合同文本内容",
                    required=True
                )
            ],
            category="compliance",
            version="1.0.0"
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行核心条款完整性校验"""
        start_time = time.time()
        
        try:
            is_valid, error_msg = self.validate_parameters(**kwargs)
            if not is_valid:
                return ToolResult(
                    success=False,
                    error=error_msg,
                    execution_time=time.time() - start_time
                )
            
            contract_text = kwargs.get("contract_text", "")
            
            # 检查必备条款
            required_clauses = {
                "标的": self._check_subject_matter(contract_text),
                "价款": self._check_price(contract_text),
                "履行期限": self._check_performance_period(contract_text),
                "违约责任": self._check_breach_of_contract(contract_text),
            }
            
            # 统计缺失的条款
            missing_clauses = [name for name, found in required_clauses.items() if not found]
            core_clauses = ["标的", "价款", "履行期限"]
            missing_core_clauses = [name for name in missing_clauses if name in core_clauses]
            
            # 判断合规状态
            if len(missing_core_clauses) > 0:
                # 缺失核心条款
                compliance_status = "违规"
                risk_level = "高风险"
            elif len(missing_clauses) >= 2:
                # 缺失2个或以上条款
                compliance_status = "违规"
                risk_level = "高风险"
            elif len(missing_clauses) == 1 and missing_clauses[0] == "违约责任":
                # 仅缺失违约责任
                compliance_status = "合规（需补充）"
                risk_level = "低风险"
            else:
                compliance_status = "合规"
                risk_level = "无风险"
            
            result_data = {
                "rule_name": "核心条款完整性校验",
                "compliance_status": compliance_status,
                "risk_level": risk_level,
                "required_clauses": {
                    name: "存在" if found else "缺失"
                    for name, found in required_clauses.items()
                },
                "missing_clauses": missing_clauses,
                "missing_core_clauses": missing_core_clauses,
                "next_action": "法务人工审批" if compliance_status == "违规" else ("建议补充违约责任" if "违约责任" in missing_clauses else None),
                "notification": "需要邮件通知" if compliance_status == "违规" else None
            }
            
            return ToolResult(
                success=True,
                data=result_data,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"执行核心条款完整性校验时发生错误: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _check_subject_matter(self, text: str) -> bool:
        """检查标的"""
        patterns = [
            r'标的[：:]\s*[^。\n]+',
            r'合同标的[：:]\s*[^。\n]+',
            r'货物名称[：:]\s*[^。\n]+',
            r'服务内容[：:]\s*[^。\n]+',
            r'产品名称[：:]\s*[^。\n]+',
        ]
        return any(re.search(pattern, text) for pattern in patterns)
    
    def _check_price(self, text: str) -> bool:
        """检查价款/报酬"""
        patterns = [
            r'(?:价款|价格|金额|报酬|费用|总价)[：:]\s*[^。\n]*(?:元|万元|人民币)',
            r'人民币\s*[0-9]+(?:\.[0-9]+)?\s*(?:元|万元)',
            r'按[^。\n]*(?:市场价|成本价|协议价)',
        ]
        return any(re.search(pattern, text) for pattern in patterns)
    
    def _check_performance_period(self, text: str) -> bool:
        """检查履行期限"""
        patterns = [
            r'(?:履行期限|合同期限|服务期限|交付期限)[：:]\s*[^。\n]+',
            r'\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日[^。\n]*(?:至|到)\s*\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日',
            r'自\s*\d{4}[年/-]\d{1,2}[月/-]\d{1,2}[日]?\s*起[^。\n]*(?:至|到)',
        ]
        return any(re.search(pattern, text) for pattern in patterns)
    
    def _check_breach_of_contract(self, text: str) -> bool:
        """检查违约责任"""
        patterns = [
            r'违约责任[：:]\s*[^。\n]+',
            r'违约[^。\n]*(?:违约金|赔偿|承担)',
            r'(?:逾期|延迟)[^。\n]*(?:支付|交付)[^。\n]*(?:违约金|赔偿)',
        ]
        return any(re.search(pattern, text) for pattern in patterns)


class LegalConflictComplianceTool(BaseTool):
    """规则3：合同条款与现行法规冲突校验"""
    
    def get_info(self) -> ToolInfo:
        return ToolInfo(
            name="legal_conflict_compliance",
            display_name="法规冲突校验",
            description="校验合同条款是否违反国家强制性法规，避免违法无效风险",
            parameters=[
                ToolParameter(
                    name="contract_text",
                    type="string",
                    description="合同文本内容",
                    required=True
                ),
                ToolParameter(
                    name="regulations",
                    type="array",
                    description="相关法规条文列表（可选，如果不提供则自动检索）",
                    required=False,
                    default=None
                )
            ],
            category="compliance",
            version="1.0.0"
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行法规冲突校验"""
        start_time = time.time()
        
        try:
            is_valid, error_msg = self.validate_parameters(**kwargs)
            if not is_valid:
                return ToolResult(
                    success=False,
                    error=error_msg,
                    execution_time=time.time() - start_time
                )
            
            contract_text = kwargs.get("contract_text", "")
            regulations = kwargs.get("regulations")
            
            # 如果没有提供法规，自动检索
            if not regulations:
                try:
                    from backend.service.tools.registry import get_registry
                    registry = get_registry()
                    regulation_tool = registry.get("regulation_search")
                    if regulation_tool:
                        keywords = "违约金,诉讼时效,争议解决,仲裁,诉讼"
                        search_result = await regulation_tool.execute(keywords=keywords, max_results=10)
                        if search_result.success:
                            regulations = search_result.data.get("regulations", [])
                except:
                    regulations = []
            
            # 检查三类冲突
            conflicts = []
            
            # 1. 违约金冲突检查
            penalty_conflict = self._check_penalty_conflict(contract_text)
            if penalty_conflict:
                conflicts.append(penalty_conflict)
            
            # 2. 诉讼时效冲突检查
            limitation_conflict = self._check_limitation_conflict(contract_text)
            if limitation_conflict:
                conflicts.append(limitation_conflict)
            
            # 3. 争议解决方式冲突检查
            dispute_resolution_conflict = self._check_dispute_resolution_conflict(contract_text)
            if dispute_resolution_conflict:
                conflicts.append(dispute_resolution_conflict)
            
            # 判断合规状态
            compliance_status = "合规" if not conflicts else "违规"
            risk_level = "高风险" if conflicts else "无风险"
            
            result_data = {
                "rule_name": "法规冲突校验",
                "compliance_status": compliance_status,
                "risk_level": risk_level,
                "conflicts": conflicts,
                "regulations_referenced": regulations[:3] if regulations else [],
                "next_action": "法务人工修改" if conflicts else None,
                "notification": "需要邮件通知" if conflicts else None
            }
            
            return ToolResult(
                success=True,
                data=result_data,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"执行法规冲突校验时发生错误: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _check_penalty_conflict(self, text: str) -> Optional[Dict]:
        """检查违约金冲突（《民法典》第585条）"""
        # 提取违约金比例
        patterns = [
            r'违约金[^。\n]*(?:按|为|比例|标准)[^。\n]*([0-9]+(?:\.[0-9]+)?)\s*%',
            r'违约金[^。\n]*(?:按|为|比例|标准)[^。\n]*([0-9]+(?:\.[0-9]+)?)\s*‰',
            r'违约金[^。\n]*(?:按|为|比例|标准)[^。\n]*([0-9]+(?:\.[0-9]+)?)\s*倍',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                value = float(match.group(1))
                # 检查是否超过30%
                if value > 30:
                    # 检查是否有实际损失举证说明
                    has_loss_proof = bool(re.search(r'(?:实际损失|损失举证|损失证明|损失计算)', text))
                    
                    if not has_loss_proof:
                        return {
                            "type": "违约金冲突",
                            "description": f"约定违约金比例 {value}% 超过法定上限 30%",
                            "law_reference": "《民法典》第585条",
                            "conflict_detail": "约定违约金比例超过合同总金额的30%，且无实际损失举证说明",
                            "suggestion": f"建议将违约金比例调整为不超过合同总金额的30%，或补充实际损失举证说明",
                            "severity": "高风险"
                        }
        
        return None
    
    def _check_limitation_conflict(self, text: str) -> Optional[Dict]:
        """检查诉讼时效冲突（《民法典》第188条）"""
        # 提取诉讼时效
        patterns = [
            r'诉讼时效[^。\n]*(?:为|是|约定)[^。\n]*([0-9]+)\s*年',
            r'时效[^。\n]*(?:为|是|约定)[^。\n]*([0-9]+)\s*年',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                years = int(match.group(1))
                # 普通合同纠纷应为3年，特殊纠纷（如人身损害赔偿）为1年
                if years < 3:
                    # 检查是否是特殊纠纷
                    is_special = bool(re.search(r'(?:人身损害|身体伤害|医疗事故)', text))
                    if is_special and years < 1:
                        return {
                            "type": "诉讼时效冲突",
                            "description": f"约定诉讼时效 {years} 年低于法定最低期限 1 年（特殊纠纷）",
                            "law_reference": "《民法典》第188条",
                            "conflict_detail": "特殊纠纷（如人身损害赔偿）的诉讼时效不得低于1年",
                            "suggestion": "建议将诉讼时效调整为至少1年，或删除该约定使用法定时效",
                            "severity": "高风险"
                        }
                    elif not is_special and years < 3:
                        return {
                            "type": "诉讼时效冲突",
                            "description": f"约定诉讼时效 {years} 年低于法定最低期限 3 年（普通合同纠纷）",
                            "law_reference": "《民法典》第188条",
                            "conflict_detail": "普通合同纠纷的诉讼时效不得低于3年",
                            "suggestion": "建议将诉讼时效调整为至少3年，或删除该约定使用法定时效",
                            "severity": "高风险"
                        }
        
        return None
    
    def _check_dispute_resolution_conflict(self, text: str) -> Optional[Dict]:
        """检查争议解决方式冲突（《仲裁法》第5条）"""
        # 检查是否同时约定仲裁和诉讼
        has_arbitration = bool(re.search(r'(?:仲裁|仲裁委|仲裁委员会|仲裁机构)', text))
        has_litigation = bool(re.search(r'(?:诉讼|法院|人民法院|起诉)', text))
        
        # 检查是否有冲突性表述
        conflict_patterns = [
            r'(?:仲裁|诉讼)[^。\n]*(?:或|或者)[^。\n]*(?:诉讼|仲裁)',
            r'(?:可|可以)[^。\n]*(?:向仲裁委申请仲裁|向法院起诉)[^。\n]*(?:或|或者)[^。\n]*(?:向法院起诉|向仲裁委申请仲裁)',
        ]
        
        has_conflict = any(re.search(pattern, text) for pattern in conflict_patterns)
        
        if has_conflict or (has_arbitration and has_litigation and "或" in text):
            return {
                "type": "争议解决方式冲突",
                "description": "同时约定仲裁和诉讼，违反《仲裁法》第5条",
                "law_reference": "《仲裁法》第5条",
                "conflict_detail": "合同不能同时约定仲裁和诉讼两种争议解决方式，仲裁约定无效",
                "suggestion": "建议明确选择一种争议解决方式：要么选择仲裁（需明确仲裁机构），要么选择诉讼（需明确管辖法院），删除另一种约定",
                "severity": "高风险"
            }
        
        return None


class ImageToPdfTool(BaseTool):
    """图片转 PDF 工具 - 将图片格式文件转换为 PDF 格式"""
    
    def get_info(self) -> ToolInfo:
        return ToolInfo(
            name="image_to_pdf",
            display_name="图片转 PDF 工具",
            description="将图片格式文件（jpg, jpeg, png, bmp 等）转换为 PDF 格式，保存到与原图片相同的位置",
            parameters=[
                ToolParameter(
                    name="image_path",
                    type="string",
                    description="图片文件路径（支持 .jpg, .jpeg, .png, .bmp, .tiff, .tif 等格式）",
                    required=True
                )
            ],
            category="document",
            version="1.0.0"
        )
    
    def _generate_unique_filename(self, file_path: Path) -> str:
        """
        生成唯一的文件名（如果文件已存在，添加 UUID 前缀）
        
        Args:
            file_path: 目标文件路径
            
        Returns:
            str: 唯一文件名
        """
        if not file_path.exists():
            return file_path.name
        
        # 如果文件已存在，添加 UUID 前缀
        import uuid
        file_stem = file_path.stem
        file_ext = file_path.suffix
        unique_id = str(uuid.uuid4()).replace("-", "")[:8]
        new_filename = f"{unique_id}_{file_stem}{file_ext}"
        
        return new_filename
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行图片转 PDF 转换"""
        start_time = time.time()
        
        try:
            is_valid, error_msg = self.validate_parameters(**kwargs)
            if not is_valid:
                return ToolResult(
                    success=False,
                    error=error_msg,
                    execution_time=time.time() - start_time
                )
            
            image_path = kwargs.get("image_path")
            
            # 查找图片文件
            resolved_path = find_file_in_uploads(image_path)
            if not resolved_path:
                project_root = Path(__file__).resolve().parent.parent.parent.parent
                uploads_dir = project_root / "uploads"
                resolved_path = find_file_in_uploads(image_path, str(uploads_dir))
            
            if not resolved_path:
                return ToolResult(
                    success=False,
                    error=f"图片文件不存在: {image_path}。已尝试在 uploads 目录下查找，未找到匹配的文件。",
                    execution_time=time.time() - start_time
                )
            
            absolute_image_path = Path(resolved_path)
            
            # 检查文件格式
            file_ext = absolute_image_path.suffix.lower()
            supported_formats = [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"]
            if file_ext not in supported_formats:
                return ToolResult(
                    success=False,
                    error=f"不支持的图片格式: {file_ext}。支持格式: {', '.join(supported_formats)}",
                    execution_time=time.time() - start_time
                )
            
            # 检查是否已经是 PDF 格式
            if file_ext == ".pdf":
                return ToolResult(
                    success=False,
                    error="文件已经是 PDF 格式，无需转换",
                    execution_time=time.time() - start_time
                )
            
            # 生成 PDF 文件路径（与原图片相同位置，相同文件名，后缀改为 .pdf）
            pdf_path = absolute_image_path.parent / f"{absolute_image_path.stem}.pdf"
            
            # 处理重名文件
            unique_pdf_name = self._generate_unique_filename(pdf_path)
            pdf_path = pdf_path.parent / unique_pdf_name
            
            # 使用 Pillow 将图片转换为 PDF
            try:
                from PIL import Image
                
                # 打开图片
                img = Image.open(absolute_image_path)
                
                # 如果是 RGBA 模式，转换为 RGB（PDF 不支持透明度）
                if img.mode == 'RGBA':
                    # 创建白色背景
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    rgb_img.paste(img, mask=img.split()[3])  # 使用 alpha 通道作为 mask
                    img = rgb_img
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 保存为 PDF
                img.save(pdf_path, 'PDF', resolution=100.0, quality=95)
                
                logger = get_logger(__name__)
                logger.info(f"图片转 PDF 成功: {absolute_image_path} -> {pdf_path}")
                
            except ImportError:
                return ToolResult(
                    success=False,
                    error="Pillow 未安装。请运行: pip install Pillow",
                    execution_time=time.time() - start_time
                )
            except Exception as e:
                return ToolResult(
                    success=False,
                    error=f"图片转 PDF 失败: {str(e)}",
                    execution_time=time.time() - start_time
                )
            
            # 转换为相对路径（相对于 uploads 目录）
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            uploads_dir = project_root / "uploads"
            relative_pdf_path = _convert_to_relative_path(str(pdf_path), str(uploads_dir))
            relative_image_path = _convert_to_relative_path(str(absolute_image_path), str(uploads_dir))
            
            # 构建返回结果
            result_data = {
                "image_path": relative_image_path,
                "pdf_path": relative_pdf_path,
                "pdf_filename": pdf_path.name,
                "pdf_size": pdf_path.stat().st_size,
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
                error=f"执行图片转 PDF 时发生错误: {str(e)}",
                execution_time=time.time() - start_time
            )

