# Contract Forge - 智能合同审计系统

一个基于大语言模型的智能合同处理与审计系统，支持合同文档解析、合规校验、风险评估、电子签名等功能。

## 📋 目录

- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [工具列表](#工具列表)
- [API 文档](#api-文档)
- [开发指南](#开发指南)

## ✨ 功能特性

### 核心功能

- **文档解析**：支持 PDF、DOCX 等格式的合同文档解析
- **OCR 识别**：支持图片类合同文件的文字识别（支持 PaddleOCR 和 LLM Vision）
- **合规校验**：签署主体合规校验、核心条款完整性校验、法规冲突校验
- **风险评估**：基于合同文本和法规条文的智能风险评估
- **电子签名**：文件数字签名和签名验证功能
- **工作流集成**：支持 N8N 自动化工作流集成

### AI 能力

- **大语言模型集成**：支持 OpenAI、阿里云通义千问等多种 LLM 提供商
- **智能工具调用**：LLM 可以根据用户需求自动选择合适的工具
- **法规检索**：智能检索相关法规条文
- **企业信息查询**：企业主体信息验证

## 🛠 技术栈

### 后端

- **框架**：FastAPI + Uvicorn
- **Python 版本**：3.8+
- **AI/ML**：
  - LangChain / LangGraph
  - OpenAI API / 阿里云通义千问
  - Sentence Transformers (向量化)
  - ChromaDB (向量数据库)
- **文档处理**：
  - PyMuPDF (PDF 解析)
  - python-docx (Word 文档)
  - PaddleOCR (OCR 识别)
- **加密/签名**：
  - cryptography (数字签名)

### 前端

- **框架**：React 19 + TypeScript
- **构建工具**：Vite
- **UI 库**：Tailwind CSS
- **路由**：React Router
- **HTTP 客户端**：Axios

## 📁 项目结构

```
contract_forge/
├── backend/                 # 后端代码
│   ├── api/                # API 路由层
│   │   ├── files/         # 文件管理 API
│   │   ├── llm/           # LLM 对话 API
│   │   ├── tools/         # 工具管理 API
│   │   └── workflow/      # 工作流 API
│   ├── service/           # 业务逻辑层
│   │   ├── files/         # 文件服务
│   │   ├── llm/           # LLM 服务
│   │   ├── tools/         # 工具服务
│   │   └── workflow/      # 工作流服务
│   ├── utils/             # 工具类
│   │   ├── llm/           # LLM 客户端封装
│   │   └── logger/        # 日志系统
│   └── main.py            # FastAPI 应用入口
├── frontend/              # 前端代码
│   ├── src/
│   │   ├── api/          # API 客户端
│   │   ├── components/   # React 组件
│   │   └── pages/        # 页面组件
│   └── package.json
├── uploads/               # 上传文件目录
├── keys/                  # 电子签名私钥目录（不提交到 Git）
├── signatures/            # 签名文件目录（不提交到 Git）
├── logs/                  # 日志文件目录
├── n8n_config/           # N8N 工作流配置
├── requirements.txt       # Python 依赖
└── README.md             # 本文档
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+
- (可选) N8N 服务器（用于工作流集成）

### 后端安装

1. **克隆项目**

```bash
git clone <repository-url>
cd contract_forge
```

2. **创建虚拟环境**

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **安装依赖**

```bash
pip install -r requirements.txt
```

4. **配置环境变量**

创建 `backend/.env` 文件（参考 `backend/.env.example`）：

```env
# LLM 配置
LLM_PROVIDER=openai  # 或 aliyun
OPENAI_API_KEY=your_openai_api_key
ALIYUN_API_KEY=your_aliyun_api_key
ALIYUN_DASHSCOPE_API_KEY=your_dashscope_key

# OCR 引擎配置（可选）
OCR_ENGINE=llm  # 或 paddle

# N8N 配置（可选）
N8N_API=http://localhost:5678/webhook/contract-process
```

5. **启动后端服务**

```bash
cd backend
python main.py
# 或
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

后端服务将在 `http://localhost:8000` 启动，API 文档地址：`http://localhost:8000/docs`

### 前端安装

1. **进入前端目录**

```bash
cd frontend
```

2. **安装依赖**

```bash
npm install
```

3. **启动开发服务器**

```bash
npm run dev
```

前端应用将在 `http://localhost:5173` 启动（默认 Vite 端口）

## ⚙️ 配置说明

### LLM 提供商配置

系统支持多种 LLM 提供商，通过环境变量 `LLM_PROVIDER` 配置：

- `openai`：使用 OpenAI API（GPT-4, GPT-3.5 等）
- `aliyun`：使用阿里云通义千问

### OCR 引擎配置

通过环境变量 `OCR_ENGINE` 配置 OCR 引擎：

- `llm`：使用大语言模型进行 OCR（默认，需要支持 Vision 的模型）
- `paddle`：使用 PaddleOCR（本地运行，无需 API）

详细配置说明请参考：[OCR_ENGINE_CONFIG.md](./OCR_ENGINE_CONFIG.md)

### N8N 工作流配置

系统支持集成 N8N 自动化工作流，配置说明请参考：[n8n_workflow_README.md](./n8n_workflow_README.md)

## 🔧 工具列表

系统提供了丰富的工具供 LLM 调用：

### 文档处理工具

1. **文档解析工具** (`document_parser`)

   - 解析 PDF、DOCX 格式的合同文档
   - 提取结构化文本内容

2. **OCR 解析工具** (`ocr_parser`)

   - 识别图片类合同文件
   - 支持中文、英文识别

3. **图片转 PDF 工具** (`image_to_pdf`)
   - 将图片文件转换为 PDF 格式

### 合规与风险评估工具

4. **法规检索工具** (`regulation_search`)

   - 检索相关法规条文

5. **风险评估工具** (`risk_assessment`)

   - 分析合同风险等级
   - 识别冲突条款

6. **签署主体合规校验工具** (`signing_subject_compliance`)

   - 校验合同签署主体合规性

7. **核心条款完整性校验工具** (`core_clauses_completeness`)

   - 校验合同核心条款完整性

8. **法规冲突校验工具** (`legal_conflict_compliance`)
   - 校验合同条款与法规冲突

### 查询工具

9. **企业信息查询工具** (`enterprise_info_query`)

   - 查询企业主体信息

10. **合同分析工具** (`contract_analysis`)
    - 分析合同内容，提取关键信息

### 安全工具

11. **电子签名工具** (`digital_signature`)
    - 对文件进行数字签名
    - 验证文件数字签名
    - 支持 RSA-PSS 签名算法

### 工作流工具

12. **N8N 工作流触发工具** (`n8n_workflow_trigger`)
    - 触发 N8N 自动化工作流
    - 支持完整的合同处理流程

## 📚 API 文档

### 工具 API

- `GET /api/tools` - 获取所有工具列表
- `GET /api/tools/{tool_name}` - 获取指定工具信息
- `GET /api/tools/names` - 获取所有工具名称
- `POST /api/tools/execute` - 执行工具

### 文件 API

- `POST /api/files/upload` - 上传文件
- `GET /api/files/list` - 获取文件列表

### LLM API

- `POST /api/llm/chat` - LLM 对话（支持工具调用）
- `POST /api/llm/chat-with-file` - 带文件的 LLM 对话

### 工作流 API

- `GET /api/workflow/status/{workflow_id}` - 查询工作流状态

完整的 API 文档请访问：`http://localhost:8000/docs` (Swagger UI)

## 💻 开发指南

### 添加新工具

1. **创建工具类**

在 `backend/service/tools/core_tools.py` 中创建工具类：

```python
from backend.service.tools.base import BaseTool
from backend.service.tools.models import ToolInfo, ToolParameter, ToolResult

class MyNewTool(BaseTool):
    def get_info(self) -> ToolInfo:
        return ToolInfo(
            name="my_new_tool",
            display_name="我的新工具",
            description="工具功能描述",
            parameters=[
                ToolParameter(
                    name="param1",
                    type="string",
                    description="参数描述",
                    required=True
                )
            ],
            category="category_name",
            version="1.0.0"
        )

    async def execute(self, **kwargs) -> ToolResult:
        # 实现工具逻辑
        pass
```

2. **注册工具**

在 `backend/service/tools/initialize.py` 中注册工具：

```python
from backend.service.tools.core_tools import MyNewTool

def initialize_default_tools():
    registry = get_registry()
    my_tool = MyNewTool()
    registry.register(my_tool)
```

3. **更新提示词（可选）**

如果需要 LLM 更好地识别和使用新工具，可以在 `backend/service/llm/service.py` 的 `_build_system_prompt()` 方法中添加工具使用说明。

### 日志系统

系统使用统一的日志系统，日志文件保存在 `logs/` 目录。

```python
from backend.utils.logger import get_logger

logger = get_logger(__name__)
logger.info("日志信息")
```

### 测试

运行测试：

```bash
cd backend
pytest
```

## 📝 注意事项

1. **敏感信息**：`keys/` 目录包含私钥文件，已添加到 `.gitignore`，不要提交到版本控制
2. **上传文件**：`uploads/` 目录存储用户上传的文件，建议定期清理
3. **日志文件**：`logs/` 目录的日志文件可能较大，建议配置日志轮转
4. **环境变量**：生产环境请妥善保管 API 密钥等敏感信息

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

[添加许可证信息]

## 📮 联系方式

[添加联系方式]
