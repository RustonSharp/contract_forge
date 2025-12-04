# 项目结构说明

**智能合同处理自动化系统 - Contract Forge**

本文档详细说明项目的目录结构、各模块职责以及关键文件说明。

---

## 📁 总体结构

```
contract_forge/
├── frontend/                          # 前端应用（用户界面层）
├── services/                          # 后端服务
│   ├── langgraph/                    # LangGraph 流程控制服务
│   ├── langdock/                     # Langdock 工具执行服务
│   ├── gateway/                      # API 网关服务
│   └── shared/                       # 共享代码库
├── n8n/                              # N8N 工作流配置
├── infrastructure/                   # 基础设施配置
│   ├── docker/                       # Docker 相关配置
│   ├── k8s/                         # Kubernetes 配置（可选）
│   └── nginx/                        # Nginx 配置
├── data/                             # 数据目录（运行时）
│   ├── contracts/                    # 合同文件存储
│   ├── reports/                      # 生成的报告
│   └── regulations/                  # 法规向量库
├── tests/                            # 测试目录
│   ├── e2e/                         # 端到端测试
│   ├── integration/                  # 集成测试
│   └── unit/                        # 单元测试
├── docs/                             # 文档目录
│   ├── api/                         # API 文档
│   ├── architecture/                # 架构设计文档
│   └── guides/                      # 使用指南
├── scripts/                          # 脚本工具
│   ├── setup/                       # 初始化脚本
│   ├── deployment/                  # 部署脚本
│   └── utils/                       # 工具脚本
├── .github/                          # GitHub 配置
│   └── workflows/                   # CI/CD 工作流
├── docker-compose.yml                # Docker Compose 配置
├── .env.example                      # 环境变量示例
├── README.md                         # 项目说明
└── Makefile                          # 项目命令快捷方式
```

---

## 🎨 前端应用 (`frontend/`)

用户界面层，提供合同上传、进度查看、结果展示等功能。

```
frontend/
├── public/                           # 静态资源
│   ├── index.html
│   ├── favicon.ico
│   └── assets/
│       ├── images/
│       └── icons/
├── src/
│   ├── components/                   # React 组件
│   │   ├── common/                  # 通用组件
│   │   │   ├── Button.tsx
│   │   │   ├── Modal.tsx
│   │   │   └── LoadingSpinner.tsx
│   │   ├── upload/                  # 上传相关组件
│   │   │   ├── FileUploader.tsx
│   │   │   └── UploadProgress.tsx
│   │   ├── progress/                # 进度展示组件
│   │   │   ├── WorkflowVisualizer.tsx
│   │   │   ├── ProgressBar.tsx
│   │   │   └── StatusTimeline.tsx
│   │   └── results/                 # 结果展示组件
│   │       ├── ContractSummary.tsx
│   │       ├── RiskReport.tsx
│   │       └── ReportDownload.tsx
│   ├── pages/                       # 页面组件
│   │   ├── HomePage.tsx
│   │   ├── UploadPage.tsx
│   │   ├── ProcessingPage.tsx
│   │   ├── ResultsPage.tsx
│   │   └── HistoryPage.tsx
│   ├── services/                    # 服务层
│   │   ├── api.ts                   # API 调用封装
│   │   ├── websocket.ts             # WebSocket 客户端
│   │   └── storage.ts               # 本地存储
│   ├── store/                       # 状态管理（Redux/Zustand）
│   │   ├── slices/
│   │   │   ├── uploadSlice.ts
│   │   │   ├── progressSlice.ts
│   │   │   └── userSlice.ts
│   │   └── index.ts
│   ├── hooks/                       # 自定义 Hooks
│   │   ├── useWebSocket.ts
│   │   ├── useFileUpload.ts
│   │   └── useProgress.ts
│   ├── utils/                       # 工具函数
│   │   ├── formatters.ts
│   │   ├── validators.ts
│   │   └── constants.ts
│   ├── types/                       # TypeScript 类型定义
│   │   ├── contract.ts
│   │   ├── workflow.ts
│   │   └── api.ts
│   ├── styles/                      # 样式文件
│   │   ├── globals.css
│   │   ├── variables.css
│   │   └── themes/
│   ├── App.tsx                      # 主应用组件
│   └── main.tsx                     # 入口文件
├── package.json
├── tsconfig.json
├── vite.config.ts                   # Vite 配置
└── .env.development                 # 开发环境变量
```

**技术栈**：React + TypeScript + Vite + TailwindCSS

---

## 🔄 LangGraph 服务 (`services/langgraph/`)

流程控制层，负责工作流编排和状态管理。

```
services/langgraph/
├── app/
│   ├── api/                         # FastAPI 路由
│   │   ├── __init__.py
│   │   ├── workflows.py             # 工作流执行端点
│   │   ├── status.py                # 状态查询端点
│   │   └── health.py                # 健康检查
│   ├── workflows/                   # 工作流定义
│   │   ├── __init__.py
│   │   ├── base.py                  # 基础工作流类
│   │   ├── contract_processing.py   # 合同处理工作流
│   │   └── nodes/                   # 工作流节点
│   │       ├── __init__.py
│   │       ├── identify_format.py
│   │       ├── parse_document.py
│   │       ├── parse_image.py
│   │       ├── retrieve_regulations.py
│   │       ├── assess_risk.py
│   │       ├── generate_report.py
│   │       ├── manual_approval.py
│   │       └── auto_approval.py
│   ├── models/                      # 数据模型
│   │   ├── __init__.py
│   │   ├── state.py                 # 状态定义
│   │   ├── request.py               # 请求模型
│   │   └── response.py              # 响应模型
│   ├── services/                    # 业务服务
│   │   ├── __init__.py
│   │   ├── langdock_client.py       # Langdock 客户端
│   │   ├── progress_tracker.py      # 进度跟踪器
│   │   └── state_manager.py         # 状态管理器
│   ├── core/                        # 核心功能
│   │   ├── __init__.py
│   │   ├── config.py                # 配置管理
│   │   ├── logging.py               # 日志配置
│   │   └── exceptions.py            # 自定义异常
│   ├── utils/                       # 工具函数
│   │   ├── __init__.py
│   │   ├── redis_helper.py
│   │   └── retry.py
│   └── main.py                      # FastAPI 应用入口
├── tests/                           # 测试
│   ├── test_workflows.py
│   ├── test_nodes.py
│   └── conftest.py
├── requirements.txt                 # Python 依赖
├── Dockerfile
└── .env.example
```

**技术栈**：Python + FastAPI + LangGraph + Redis

---

## 🔧 Langdock 服务 (`services/langdock/`)

工具执行层，实现具体的业务处理工具。

```
services/langdock/
├── app/
│   ├── api/                         # FastAPI 路由
│   │   ├── __init__.py
│   │   ├── tools.py                 # 工具执行端点
│   │   └── health.py
│   ├── tools/                       # 工具实现
│   │   ├── __init__.py
│   │   ├── base.py                  # 基础工具类
│   │   ├── registry.py              # 工具注册表
│   │   ├── document_parser/         # 文档解析工具
│   │   │   ├── __init__.py
│   │   │   ├── tool.py
│   │   │   ├── pdf_parser.py
│   │   │   ├── docx_parser.py
│   │   │   └── extractors.py        # 信息提取器
│   │   ├── ocr_parser/              # OCR 解析工具
│   │   │   ├── __init__.py
│   │   │   ├── tool.py
│   │   │   └── ocr_engine.py
│   │   ├── regulation_retrieval/    # 法规检索工具
│   │   │   ├── __init__.py
│   │   │   ├── tool.py
│   │   │   ├── vector_search.py
│   │   │   └── keyword_expander.py
│   │   ├── risk_assessment/         # 风险评估工具
│   │   │   ├── __init__.py
│   │   │   ├── tool.py
│   │   │   ├── llm_analyzer.py
│   │   │   └── risk_calculator.py
│   │   └── report_generator/        # 报告生成工具
│   │       ├── __init__.py
│   │       ├── tool.py
│   │       ├── template_engine.py
│   │       └── templates/           # 报告模板
│   │           ├── default.docx
│   │           └── risk_matrix.xlsx
│   ├── models/                      # 数据模型
│   │   ├── __init__.py
│   │   ├── tool_request.py
│   │   ├── tool_response.py
│   │   └── contract_data.py
│   ├── services/                    # 外部服务
│   │   ├── __init__.py
│   │   ├── llm_service.py           # LLM 调用服务
│   │   ├── vector_db.py             # 向量数据库客户端
│   │   └── file_storage.py          # 文件存储服务
│   ├── core/                        # 核心功能
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── validation.py
│   ├── utils/                       # 工具函数
│   │   ├── __init__.py
│   │   ├── text_utils.py
│   │   └── file_utils.py
│   └── main.py                      # FastAPI 应用入口
├── tests/                           # 测试
│   ├── tools/
│   │   ├── test_document_parser.py
│   │   ├── test_ocr_parser.py
│   │   ├── test_regulation_retrieval.py
│   │   ├── test_risk_assessment.py
│   │   └── test_report_generator.py
│   └── conftest.py
├── requirements.txt
├── Dockerfile
└── .env.example
```

**技术栈**：Python + FastAPI + LangChain + ChromaDB/Milvus

---

## 🚪 API 网关 (`services/gateway/`)

统一入口，处理认证、限流、路由等。

```
services/gateway/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/                      # API v1
│   │   │   ├── __init__.py
│   │   │   ├── upload.py            # 文件上传端点
│   │   │   ├── contracts.py         # 合同管理端点
│   │   │   └── users.py             # 用户管理端点
│   │   └── websocket/               # WebSocket 端点
│   │       ├── __init__.py
│   │       └── progress.py          # 进度推送
│   ├── middleware/                  # 中间件
│   │   ├── __init__.py
│   │   ├── auth.py                  # 认证中间件
│   │   ├── rate_limit.py            # 限流中间件
│   │   └── logging.py               # 日志中间件
│   ├── services/                    # 业务服务
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── file_service.py
│   │   └── notification_service.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── security.py
│   └── main.py
├── requirements.txt
├── Dockerfile
└── .env.example
```

**技术栈**：Python + FastAPI + JWT + Redis

---

## 🎭 共享代码库 (`services/shared/`)

各服务共享的代码和配置。

```
services/shared/
├── src/
│   ├── __init__.py
│   ├── models/                      # 共享数据模型
│   │   ├── __init__.py
│   │   ├── contract.py
│   │   ├── user.py
│   │   └── workflow.py
│   ├── database/                    # 数据库操作
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   ├── session.py
│   │   └── models/
│   │       ├── __init__.py
│   │       ├── contract.py
│   │       ├── user.py
│   │       └── execution_log.py
│   ├── cache/                       # 缓存操作
│   │   ├── __init__.py
│   │   ├── redis_client.py
│   │   └── cache_manager.py
│   ├── messaging/                   # 消息队列
│   │   ├── __init__.py
│   │   ├── publisher.py
│   │   └── subscriber.py
│   ├── logging/                     # 日志配置
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   └── formatters.py
│   └── utils/                       # 通用工具
│       ├── __init__.py
│       ├── datetime_utils.py
│       ├── file_utils.py
│       └── validators.py
├── setup.py
└── requirements.txt
```

---

## 🎨 N8N 工作流 (`n8n/`)

N8N 可视化编排层的配置和备份。

```
n8n/
├── workflows/                       # 工作流定义（JSON）
│   ├── contract_processing.json     # 主工作流
│   ├── notification.json            # 通知工作流
│   └── data_sync.json               # 数据同步工作流
├── credentials/                     # 凭证配置（加密）
│   └── .gitkeep
├── custom-nodes/                    # 自定义节点（可选）
│   └── .gitkeep
├── backups/                         # 工作流备份
│   └── .gitkeep
└── README.md                        # N8N 使用说明
```

**说明**：N8N 工作流可通过 UI 导出为 JSON 文件存储在此目录。

---

## 🏗️ 基础设施配置 (`infrastructure/`)

Docker、Kubernetes、Nginx 等基础设施配置。

```
infrastructure/
├── docker/
│   ├── frontend.Dockerfile
│   ├── langgraph.Dockerfile
│   ├── langdock.Dockerfile
│   ├── gateway.Dockerfile
│   └── n8n.Dockerfile
├── k8s/                             # Kubernetes 配置（生产环境）
│   ├── namespaces/
│   │   └── contract-forge.yaml
│   ├── deployments/
│   │   ├── frontend.yaml
│   │   ├── langgraph.yaml
│   │   ├── langdock.yaml
│   │   ├── gateway.yaml
│   │   ├── n8n.yaml
│   │   ├── redis.yaml
│   │   └── postgres.yaml
│   ├── services/
│   │   ├── frontend-service.yaml
│   │   ├── langgraph-service.yaml
│   │   ├── langdock-service.yaml
│   │   ├── gateway-service.yaml
│   │   └── n8n-service.yaml
│   ├── configmaps/
│   │   └── app-config.yaml
│   ├── secrets/
│   │   └── app-secrets.yaml.example
│   ├── ingress/
│   │   └── ingress.yaml
│   └── volumes/
│       ├── contracts-pvc.yaml
│       └── reports-pvc.yaml
├── nginx/
│   ├── nginx.conf                   # Nginx 主配置
│   ├── conf.d/
│   │   ├── frontend.conf            # 前端代理
│   │   └── api.conf                 # API 代理
│   └── ssl/                         # SSL 证书
│       └── .gitkeep
└── monitoring/                      # 监控配置（可选）
    ├── prometheus/
    │   └── prometheus.yml
    └── grafana/
        └── dashboards/
```

---

## 📊 数据目录 (`data/`)

运行时数据存储（不提交到 Git）。

```
data/
├── contracts/                       # 上传的合同文件
│   ├── 2025-12-04/
│   ├── 2025-12-05/
│   └── .gitkeep
├── reports/                         # 生成的报告
│   ├── 2025-12-04/
│   └── .gitkeep
├── regulations/                     # 法规向量库
│   ├── embeddings/
│   └── index/
├── logs/                            # 日志文件
│   ├── langgraph/
│   ├── langdock/
│   └── gateway/
└── temp/                            # 临时文件
    └── .gitkeep
```

**说明**：此目录添加到 `.gitignore`，仅保留 `.gitkeep` 文件。

---

## 🧪 测试目录 (`tests/`)

各类测试代码。

```
tests/
├── e2e/                             # 端到端测试
│   ├── test_contract_upload.py
│   ├── test_workflow_execution.py
│   └── test_user_scenarios.py
├── integration/                     # 集成测试
│   ├── test_n8n_langgraph.py
│   ├── test_langgraph_langdock.py
│   └── test_api_gateway.py
├── unit/                            # 单元测试（分服务）
│   ├── langgraph/
│   │   ├── test_workflows.py
│   │   └── test_nodes.py
│   ├── langdock/
│   │   ├── test_document_parser.py
│   │   ├── test_risk_assessment.py
│   │   └── test_report_generator.py
│   └── gateway/
│       ├── test_auth.py
│       └── test_upload.py
├── fixtures/                        # 测试数据
│   ├── sample_contracts/
│   │   ├── sample_01.pdf
│   │   ├── sample_02.docx
│   │   └── sample_03.jpg
│   └── expected_outputs/
├── conftest.py                      # Pytest 配置
└── pytest.ini
```

---

## 📚 文档目录 (`docs/`)

项目文档。

```
docs/
├── api/                             # API 文档
│   ├── gateway-api.md               # 网关 API
│   ├── langgraph-api.md             # LangGraph API
│   └── langdock-api.md              # Langdock API
├── architecture/                    # 架构设计
│   ├── system-overview.md           # 系统概述
│   ├── data-flow.md                 # 数据流转
│   ├── security.md                  # 安全设计
│   └── diagrams/                    # 架构图
│       ├── system-architecture.png
│       └── workflow-diagram.png
├── guides/                          # 使用指南
│   ├── deployment.md                # 部署指南
│   ├── development.md               # 开发指南
│   ├── n8n-setup.md                 # N8N 配置指南
│   └── troubleshooting.md           # 故障排查
├── implementation-guide.md          # 实现指南（已存在）
├── req.md                           # 需求文档（已存在）
└── PROJECT_STATUS.md                # 项目状态（已存在）
```

---

## 🔧 脚本工具 (`scripts/`)

自动化脚本。

```
scripts/
├── setup/                           # 初始化脚本
│   ├── init_project.sh              # 项目初始化
│   ├── setup_database.sh            # 数据库初始化
│   └── load_regulations.py          # 加载法规数据
├── deployment/                      # 部署脚本
│   ├── deploy_dev.sh                # 部署到开发环境
│   ├── deploy_prod.sh               # 部署到生产环境
│   └── rollback.sh                  # 回滚脚本
├── utils/                           # 工具脚本
│   ├── backup.sh                    # 数据备份
│   ├── clean_temp.sh                # 清理临时文件
│   └── health_check.py              # 健康检查
└── README.md                        # 脚本说明
```

---

## 📝 根目录文件说明

### 核心配置文件

```
contract_forge/
├── docker-compose.yml               # Docker Compose 编排
├── docker-compose.dev.yml           # 开发环境覆盖配置
├── docker-compose.prod.yml          # 生产环境覆盖配置
├── Makefile                         # 命令快捷方式
├── .env.example                     # 环境变量示例
├── .gitignore                       # Git 忽略规则
├── .dockerignore                    # Docker 忽略规则
├── README.md                        # 项目说明
├── LICENSE                          # 许可证
└── CHANGELOG.md                     # 变更日志
```

### docker-compose.yml 示例结构

```yaml
services:
  # 前端服务
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    
  # API 网关
  gateway:
    build: ./services/gateway
    ports:
      - "8000:8000"
  
  # LangGraph 服务
  langgraph:
    build: ./services/langgraph
    ports:
      - "8001:8001"
  
  # Langdock 服务
  langdock:
    build: ./services/langdock
    ports:
      - "8002:8002"
  
  # N8N 服务
  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"
  
  # Redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  # PostgreSQL
  postgres:
    image: postgres:15
    ports:
      - "5432:5432"
  
  # 向量数据库（ChromaDB 或 Milvus）
  vectordb:
    image: chromadb/chroma
    ports:
      - "8000:8000"
```

### Makefile 示例

```makefile
.PHONY: help dev prod stop clean test

help:  ## 显示帮助信息
	@echo "可用命令："
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

dev:  ## 启动开发环境
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

prod:  ## 启动生产环境
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

stop:  ## 停止所有服务
	docker-compose down

clean:  ## 清理数据和临时文件
	docker-compose down -v
	./scripts/utils/clean_temp.sh

test:  ## 运行测试
	pytest tests/ -v

logs:  ## 查看日志
	docker-compose logs -f

setup:  ## 初始化项目
	./scripts/setup/init_project.sh
```

---

## 🔄 数据流转路径

```
用户上传文件
    ↓
[frontend] → [gateway] → [n8n workflow]
                              ↓
                         保存文件到 data/contracts/
                              ↓
                         调用 [langgraph]
                              ↓
                    [workflow orchestration]
                         ↙        ↘
                [langdock]      [langdock]
              (document_parser) (regulation_retrieval)
                         ↘        ↙
                    [继续工作流]
                              ↓
                    [langdock] (risk_assessment)
                              ↓
                    [langdock] (report_generator)
                              ↓
                    保存报告到 data/reports/
                              ↓
                    返回结果给 [n8n]
                              ↓
                    [n8n] 后续处理（通知、入库）
                              ↓
                    返回给 [gateway] → [frontend]
                              ↓
                         用户看到结果
```

---

## 🚀 开发流程

### 1. 初始化项目

```bash
# 克隆项目
git clone <repository-url>
cd contract_forge

# 复制环境变量文件
cp .env.example .env

# 初始化项目
make setup

# 启动开发环境
make dev
```

### 2. 开发新功能

```bash
# 创建功能分支
git checkout -b feature/new-tool

# 开发 Langdock 工具
cd services/langdock/app/tools/
# ... 编写代码 ...

# 运行单元测试
pytest tests/unit/langdock/test_new_tool.py

# 集成到 LangGraph
cd services/langgraph/app/workflows/
# ... 更新工作流 ...

# 配置 N8N
# 访问 http://localhost:5678 配置工作流

# 运行集成测试
pytest tests/integration/

# 提交代码
git add .
git commit -m "feat: add new tool"
git push origin feature/new-tool
```

### 3. 部署到生产

```bash
# 构建生产镜像
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# 部署
./scripts/deployment/deploy_prod.sh

# 健康检查
./scripts/utils/health_check.py
```

---

## 📊 服务端口分配

| 服务 | 端口 | 说明 |
|-----|------|-----|
| Frontend | 3000 | 用户界面 |
| Gateway | 8000 | API 网关 |
| LangGraph | 8001 | 流程控制服务 |
| Langdock | 8002 | 工具执行服务 |
| N8N | 5678 | 工作流编排界面 |
| Redis | 6379 | 缓存和消息队列 |
| PostgreSQL | 5432 | 主数据库 |
| VectorDB | 8003 | 向量数据库 |
| Prometheus | 9090 | 监控（可选） |
| Grafana | 3001 | 可视化（可选） |

---

## 🔒 安全考虑

### 敏感文件保护

以下文件/目录不应提交到 Git：

```
.env                          # 环境变量
data/                         # 运行时数据
*.log                         # 日志文件
n8n/credentials/*             # N8N 凭证
infrastructure/nginx/ssl/*    # SSL 证书
.vscode/                      # IDE 配置
__pycache__/                  # Python 缓存
node_modules/                 # Node 依赖
*.pyc                         # Python 编译文件
```

### 环境变量管理

```bash
# .env.example 示例
# 数据库
DATABASE_URL=postgresql://user:password@postgres:5432/contract_forge

# Redis
REDIS_URL=redis://redis:6379/0

# LLM API
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# JWT
JWT_SECRET=your-secret-key-here

# N8N
N8N_ENCRYPTION_KEY=your-encryption-key

# 文件存储
CONTRACTS_PATH=/data/contracts
REPORTS_PATH=/data/reports
```

---

## 📈 扩展建议

### 添加新工具

1. 在 `services/langdock/app/tools/` 创建新目录
2. 实现工具类继承 `BaseTool`
3. 在 `registry.py` 注册工具
4. 编写单元测试
5. 在 LangGraph 工作流中使用

### 添加新工作流

1. 在 `services/langgraph/app/workflows/` 创建新文件
2. 定义状态和节点
3. 配置边和条件分支
4. 在 N8N 中创建触发工作流
5. 编写集成测试

### 添加新 UI 功能

1. 在 `frontend/src/components/` 创建组件
2. 在 `frontend/src/pages/` 创建页面
3. 在 `frontend/src/services/` 添加 API 调用
4. 更新路由配置
5. 编写 E2E 测试

---

## 📖 相关文档

- [实现指南](./implementation-guide.md) - 自顶向下的完整实现流程
- [需求文档](./req.md) - 详细功能需求
- [API 文档](./docs/api/) - 各服务 API 说明
- [部署指南](./docs/guides/deployment.md) - 部署步骤
- [开发指南](./docs/guides/development.md) - 开发规范

---

## 🎯 核心设计原则

1. **模块化**：各服务独立开发、测试、部署
2. **可扩展**：易于添加新工具和工作流
3. **低耦合**：通过标准接口通信，减少依赖
4. **可维护**：清晰的目录结构和命名规范
5. **可测试**：完善的测试覆盖
6. **可监控**：完整的日志和监控体系

---

*文档版本: v1.0*  
*最后更新: 2025-12-04*  
*作者: Contract Forge Team*

