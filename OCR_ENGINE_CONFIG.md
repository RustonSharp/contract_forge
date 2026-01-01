# OCR 引擎配置说明

## 概述

OCR 解析工具支持两种引擎：
1. **LLM OCR**（默认）：使用大语言模型进行图片文字识别
2. **PaddleOCR**：使用 PaddleOCR 进行图片文字识别

## 配置方式

### 引擎选择

通过环境变量 `OCR_ENGINE` 来配置使用的引擎：

### 使用 LLM OCR（默认）

```bash
# 在 .env 文件中设置
OCR_ENGINE=llm
```

或者在终端中设置：
```bash
export OCR_ENGINE=llm
```

**要求：**
- 需要配置支持视觉的 LLM 模型（如 GPT-4 Vision、通义千问 VL 等）
- 需要配置 LLM API 密钥（DASHSCOPE_API_KEY 或 MODEL_STUDIO_KEY）

**OCR 专用模型配置：**

默认使用 `qwen3-omni-flash-2025-12-01` 模型进行 OCR 识别。如需使用其他模型，可通过环境变量 `OCR_MODEL_NAME` 配置：

```bash
# 在 .env 文件中设置
OCR_MODEL_NAME=qwen3-omni-flash-2025-12-01
```

或者在终端中设置：
```bash
export OCR_MODEL_NAME=qwen3-omni-flash-2025-12-01
```

**注意：** OCR 专用模型配置会覆盖默认的 `MODEL_NAME` 配置，仅用于 OCR 识别任务。

### 使用 PaddleOCR

```bash
# 在 .env 文件中设置
OCR_ENGINE=paddle
```

或者在终端中设置：
```bash
export OCR_ENGINE=paddle
```

**要求：**
- 需要安装 PaddleOCR 相关依赖：
  ```bash
  pip install paddlepaddle paddleocr opencv-python shapely
  ```

## 引擎对比

| 特性 | LLM OCR | PaddleOCR |
|------|---------|-----------|
| 识别准确率 | 高（特别是复杂布局） | 高（针对中文优化） |
| 速度 | 较慢（需要网络请求） | 快（本地处理） |
| 依赖 | LLM API 密钥 | 本地模型文件 |
| 成本 | API 调用费用 | 免费 |
| 离线支持 | 否 | 是 |
| 多语言支持 | 优秀 | 良好 |

## 推荐使用场景

### 使用 LLM OCR 的场景：
- 需要识别复杂布局的文档
- 需要理解文档结构和语义
- 对识别准确率要求很高
- 有稳定的网络连接和 API 预算

### 使用 PaddleOCR 的场景：
- 需要离线处理
- 需要快速响应
- 需要控制成本
- 主要识别中文文档

## 切换引擎

如果需要临时切换引擎，可以在代码中设置环境变量：

```python
import os
os.environ["OCR_ENGINE"] = "paddle"  # 或 "llm"
```

或者在运行测试/应用前设置：

```bash
OCR_ENGINE=paddle python -m backend.tests.run_ocr_test
```

## 故障排除

### LLM OCR 失败

如果遇到 "当前 LLM 模型不支持图片识别" 错误：

1. **检查模型是否支持视觉**：
   - GPT-4 Vision: `gpt-4-vision-preview` 或 `gpt-4o`
   - 通义千问 VL: `qwen-vl-max` 或 `qwen-vl-plus`
   - 确保在 `.env` 中配置了正确的模型名称

2. **切换到 PaddleOCR**：
   ```bash
   export OCR_ENGINE=paddle
   ```

### PaddleOCR 初始化失败

如果遇到 PaddleOCR 初始化错误：

1. **检查依赖是否安装**：
   ```bash
   pip install paddlepaddle paddleocr opencv-python shapely
   ```

2. **检查 langchain 版本**：
   ```bash
   pip install langchain==0.0.350
   ```

3. **查看详细错误信息**，根据错误提示进行修复

## 默认配置

默认使用 **LLM OCR** 引擎，因为：
- 识别准确率更高
- 支持更复杂的文档布局
- 可以理解文档语义

如果需要使用 PaddleOCR，请设置 `OCR_ENGINE=paddle`。

