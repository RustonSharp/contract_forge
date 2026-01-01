# 测试说明

## OCR 识别工具测试

### 运行测试

#### 方式1: 使用 pytest（推荐）

```bash
# 安装测试依赖
pip install pytest pytest-asyncio

# 运行所有测试
pytest backend/tests/test_ocr_tool.py -v

# 运行特定测试类
pytest backend/tests/test_ocr_tool.py::TestOCRParserTool -v

# 运行特定测试方法
pytest backend/tests/test_ocr_tool.py::TestOCRParserTool::test_tool_info -v

# 显示详细输出
pytest backend/tests/test_ocr_tool.py -v -s
```

#### 方式2: 直接运行测试文件

```bash
python -m backend.tests.test_ocr_tool
```

### 测试覆盖

测试文件 `test_ocr_tool.py` 包含以下测试：

1. **工具信息测试** (`test_tool_info`)
   - 测试工具名称、显示名称、参数定义等

2. **参数验证测试**
   - `test_parameter_validation_missing_image_path`: 测试缺少必需参数
   - `test_parameter_validation_invalid_image_path`: 测试无效文件路径
   - `test_unsupported_file_format`: 测试不支持的文件格式

3. **OCR 识别功能测试**
   - `test_ocr_recognition_with_test_image`: 测试实际 OCR 识别
   - `test_ocr_with_language_parameter`: 测试不同语言参数
   - `test_ocr_with_relative_path`: 测试相对路径支持

4. **单例模式测试** (`test_ocr_singleton_pattern`)
   - 测试 OCR 引擎只初始化一次

5. **错误处理测试**
   - `test_empty_image_path`: 测试空文件路径
   - `test_none_image_path`: 测试 None 文件路径
   - `test_invalid_image_path_format`: 测试无效路径格式

### 测试要求

- 测试需要项目中有测试图片文件（位于 `uploads/2025-12-31/Screenshot 2025-12-31 at 19.44.08.png`）
- 如果测试图片不存在，相关测试会自动跳过
- 某些测试可能需要 PaddleOCR 已正确安装和配置

### 注意事项

- OCR 识别测试可能需要较长时间（模型加载和识别过程）
- 如果 PaddleOCR 未安装或初始化失败，某些测试可能会失败，这是正常的
- 测试会自动尝试使用备选 OCR 方案（RapidOCR、Tesseract）

