# 实现指南：从用户界面到底层实现

**智能合同处理自动化系统 - 自顶向下完整实现指南**

本文档详细讲解系统从用户界面到底层工具的完整实现流程，采用自顶向下的方式，帮助开发者理解整个系统的架构和数据流转。

---

## 📖 目录

- [场景介绍](#场景介绍)
- [第一层：用户界面层](#第一层用户界面层)
- [第二层：N8N 可视化编排层](#第二层n8n-可视化编排层)
- [第三层：LangGraph 流程控制层](#第三层langgraph-流程控制层)
- [第四层：Langdock 工具执行层](#第四层langdock-工具执行层)
- [第五层：数据流转和状态同步](#第五层数据流转和状态同步)
- [完整用户体验流程](#完整用户体验流程)
- [关键技术要点](#关键技术要点)
- [设计优势](#设计优势)

---

## 场景介绍

### 👤 用户故事：财务小王要处理一份销售合同

小王是公司财务部门的员工，每天需要处理大量合同。传统流程需要：
1. 手动打开合同文件
2. 阅读并提取关键信息
3. 查找相关法规条文
4. 评估合同风险
5. 撰写审批报告
6. 提交给法务或直接审批

这个过程耗时耗力，容易出错。现在有了智能合同处理系统，一切都变得简单了。

---

## 第一层：用户界面层

### 👤 用户视角：小王的操作流程

#### 步骤 1: 访问系统主界面

```
小王打开浏览器：http://company.com/contract-system

看到的界面：
┌─────────────────────────────────────────────────┐
│  📄 智能合同处理系统                             │
│                                                  │
│  [上传合同文件]  [查看处理历史]  [流程管理]     │
│                                                  │
│  快速上传：                                      │
│  ┌─────────────────────────────────────────┐    │
│  │  📁 拖拽文件到这里 或 点击选择文件       │    │
│  │                                          │    │
│  │  支持格式：PDF, DOCX, JPG, PNG          │    │
│  └─────────────────────────────────────────┘    │
│                                                  │
│  最近处理：                                      │
│  ✅ contract_2025_001.pdf - 低风险 - 已自动审批 │
│  ⏳ contract_2025_002.docx - 处理中...          │
└─────────────────────────────────────────────────┘
```

#### 步骤 2: 上传合同文件

```
小王点击上传区域，选择文件：sales_contract_20251204.pdf

界面立即显示：
┌─────────────────────────────────────────────────┐
│  📤 正在上传: sales_contract_20251204.pdf       │
│  ████████████████████████ 100%                   │
│                                                  │
│  ✅ 上传成功！正在启动处理流程...                │
│                                                  │
│  执行ID: exec_abc123                             │
│  [查看实时进度]                                  │
└─────────────────────────────────────────────────┘
```

#### 步骤 3: 实时查看处理进度

```
小王点击"查看实时进度"，看到流程图：

┌─────────────────────────────────────────────────────────┐
│  合同处理进度 - exec_abc123                              │
│                                                          │
│  ✅ [附件上传]           ← 已完成 (2秒)                  │
│       ↓                                                  │
│  ✅ [文件格式识别]       ← 已完成 (1秒) 识别为：PDF      │
│       ↓                                                  │
│  🔄 [文档内容解析]       ← 进行中... (已用时5秒)         │
│       ↓                                                  │
│  ⏳ [法规检索]           ← 等待中                        │
│       ↓                                                  │
│  ⏳ [风险评估]           ← 等待中                        │
│       ↓                                                  │
│  ⏳ [生成报告]           ← 等待中                        │
│       ↓                                                  │
│  ⏳ [审批流转]           ← 等待中                        │
│                                                          │
│  [查看详细日志]  [暂停处理]  [导出流程图]               │
└─────────────────────────────────────────────────────────┘
```

**背后发生了什么？** 👇

---

## 第二层：N8N 可视化编排层

### 🎨 N8N 工作流设计（管理员预先创建）

#### 管理员在 N8N 中的配置界面

访问：`http://localhost:5678`

```
┌──────────────────────────────────────────────────────────┐
│ N8N - 合同处理流程                        [保存] [激活]   │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  [1. Webhook]                                            │
│     ┃ POST /api/contract/upload                          │
│     ┃                                                     │
│     ┗━━━━━━━━━━━━━━━━━━━━┓                               │
│                          ┃                               │
│  [2. Save File]          ┃                               │
│     ┃ 保存上传的文件      ┃                               │
│     ┃                    ┃                               │
│     ┗━━━━━━━━━┳━━━━━━━━━┛                               │
│               ┃                                           │
│  [3. Call LangGraph]                                     │
│     ┃ POST http://langgraph:8001/execute                 │
│     ┃ Body: {                                            │
│     ┃   "workflow": "contract_processing",               │
│     ┃   "input": {                                       │
│     ┃     "file_path": "{{ $json.file_path }}"          │
│     ┃   }                                                │
│     ┃ }                                                  │
│     ┃                                                     │
│     ┗━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓        │
│               ┃                                  ┃        │
│  [4. IF: Risk Level]                             ┃        │
│     ┃ {{ $json.risk_level === "high" }}         ┃        │
│     ┃                                            ┃        │
│     ┣━━━True━━▶ [5a. Send to Legal]             ┃        │
│     ┃              ┃ Email: legal@company.com    ┃        │
│     ┃              ┃ 钉钉通知                     ┃        │
│     ┃                                            ┃        │
│     ┗━━False━━▶ [5b. Auto Approve]              ┃        │
│                   ┃ 自动审批通过                  ┃        │
│                   ┃                              ┃        │
│                   ┗━━━━━━━┳━━━━━━━━━━━━━━━━━━━┛        │
│                           ┃                              │
│  [6. Update Database]                                    │
│     ┃ 保存处理结果                                       │
│     ┃                                                     │
│     ┗━━━━━━━━━┳━━━━━━━━━━                               │
│               ┃                                           │
│  [7. Respond to User]                                    │
│     ┃ 返回处理结果和报告链接                             │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### 📝 节点详细配置

#### 节点 1: Webhook - 接收用户上传

```javascript
// N8N Webhook 节点配置
{
  "name": "接收合同上传",
  "type": "n8n-nodes-base.webhook",
  "parameters": {
    "httpMethod": "POST",
    "path": "api/contract/upload",
    "responseMode": "lastNode",  // 等待整个流程完成后返回
    "options": {
      "rawBody": false
    }
  }
}

// 用户上传时发送的数据：
{
  "file": "<binary data>",
  "filename": "sales_contract_20251204.pdf",
  "user_id": "user_xiaowang",
  "department": "finance"
}
```

#### 节点 2: Save File - 保存文件

```javascript
// N8N Write Binary File 节点
{
  "name": "保存上传文件",
  "type": "n8n-nodes-base.writeBinaryFile",
  "parameters": {
    "fileName": "={{ $json.filename }}",
    "dataPropertyName": "data",
    "options": {
      "path": "/data/contracts/{{ $now.format('YYYY-MM-DD') }}"
    }
  }
}

// 输出：
{
  "file_path": "/data/contracts/2025-12-04/sales_contract_20251204.pdf",
  "file_size": 1024000,
  "saved_at": "2025-12-04T10:30:00Z"
}
```

#### 节点 3: Call LangGraph - 核心处理

```javascript
// N8N HTTP Request 节点（调用 LangGraph 服务）
{
  "name": "调用合同处理流程",
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "method": "POST",
    "url": "http://langgraph-service:8001/execute/contract_processing",
    "authentication": "none",
    "sendBody": true,
    "bodyParameters": {
      "parameters": [
        {
          "name": "file_path",
          "value": "={{ $json.file_path }}"
        },
        {
          "name": "user_id",
          "value": "={{ $json.user_id }}"
        },
        {
          "name": "execution_id",
          "value": "={{ $execution.id }}"  // N8N 执行ID
        }
      ]
    },
    "options": {
      "timeout": 300000  // 5分钟超时
    }
  }
}
```

**这个 HTTP 请求发送后，控制权交给 LangGraph** 👇

---

## 第三层：LangGraph 流程控制层

### 🔄 LangGraph 服务收到请求

#### LangGraph API 服务器

```python
# langgraph_service/api.py

from fastapi import FastAPI, BackgroundTasks
from langgraph_workflows import ContractProcessingWorkflow

app = FastAPI()

@app.post("/execute/contract_processing")
async def execute_workflow(
    request: WorkflowRequest,
    background_tasks: BackgroundTasks
):
    """
    接收 N8N 的调用请求
    """
    # 1. 创建工作流实例
    workflow = ContractProcessingWorkflow()
    
    # 2. 初始化状态
    initial_state = {
        "contract_file": {
            "path": request.file_path,
            "user_id": request.user_id
        },
        "execution_id": request.execution_id,
        "current_step": "start",
        "progress": 0
    }
    
    # 3. 异步执行工作流（在后台运行）
    background_tasks.add_task(
        workflow.execute,
        initial_state
    )
    
    # 4. 立即返回执行ID给 N8N
    return {
        "status": "started",
        "execution_id": request.execution_id,
        "tracking_url": f"/status/{request.execution_id}"
    }
```

### 🔀 LangGraph 工作流定义

```python
# langgraph_workflows/contract_processing.py

from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal

# 定义状态
class ContractState(TypedDict):
    # 输入
    contract_file: dict
    execution_id: str
    
    # 流程控制
    current_step: str
    progress: int  # 0-100
    
    # 中间结果
    file_format: Literal["pdf", "docx", "image"]
    parsed_text: str
    contract_structure: dict
    regulations: list
    risk_assessment: dict
    report: dict
    
    # 输出
    final_result: dict
    error: Optional[str]

class ContractProcessingWorkflow:
    def __init__(self):
        # 创建状态图
        self.graph = StateGraph(ContractState)
        
        # 添加所有节点
        self._add_nodes()
        
        # 添加边和条件分支
        self._add_edges()
        
        # 编译
        self.app = self.graph.compile()
    
    def _add_nodes(self):
        """添加所有处理节点"""
        
        # 节点1: 识别文件格式
        self.graph.add_node("identify_format", self.identify_format_node)
        
        # 节点2a: PDF/DOCX 解析
        self.graph.add_node("parse_document", self.parse_document_node)
        
        # 节点2b: 图片 OCR
        self.graph.add_node("parse_image", self.parse_image_node)
        
        # 节点3: 法规检索
        self.graph.add_node("retrieve_regulations", self.retrieve_regulations_node)
        
        # 节点4: 风险评估
        self.graph.add_node("assess_risk", self.assess_risk_node)
        
        # 节点5: 生成报告
        self.graph.add_node("generate_report", self.generate_report_node)
        
        # 节点6a: 人工审批
        self.graph.add_node("manual_approval", self.manual_approval_node)
        
        # 节点6b: 自动审批
        self.graph.add_node("auto_approval", self.auto_approval_node)
    
    def _add_edges(self):
        """定义流程路径"""
        
        # 入口点
        self.graph.set_entry_point("identify_format")
        
        # 条件分支1: 根据文件格式选择解析方式
        self.graph.add_conditional_edges(
            "identify_format",
            self.route_by_format,  # 路由函数
            {
                "document": "parse_document",
                "image": "parse_image"
            }
        )
        
        # 两个解析节点都连接到法规检索
        self.graph.add_edge("parse_document", "retrieve_regulations")
        self.graph.add_edge("parse_image", "retrieve_regulations")
        
        # 串行执行：检索 → 评估 → 报告
        self.graph.add_edge("retrieve_regulations", "assess_risk")
        self.graph.add_edge("assess_risk", "generate_report")
        
        # 条件分支2: 根据风险等级选择审批方式
        self.graph.add_conditional_edges(
            "generate_report",
            self.route_by_risk,  # 路由函数
            {
                "high": "manual_approval",
                "low": "auto_approval"
            }
        )
        
        # 两个审批节点都是终点
        self.graph.add_edge("manual_approval", END)
        self.graph.add_edge("auto_approval", END)
    
    # ========== 节点实现 ==========
    
    def identify_format_node(self, state: ContractState) -> ContractState:
        """节点1: 识别文件格式"""
        
        # 更新进度
        self.update_progress(state["execution_id"], 10, "识别文件格式")
        
        file_path = state["contract_file"]["path"]
        ext = file_path.split('.')[-1].lower()
        
        if ext in ['pdf', 'docx', 'doc']:
            state["file_format"] = "document"
        elif ext in ['jpg', 'jpeg', 'png']:
            state["file_format"] = "image"
        
        state["progress"] = 10
        return state
    
    def parse_document_node(self, state: ContractState) -> ContractState:
        """节点2a: 解析文档格式"""
        
        # 更新进度
        self.update_progress(state["execution_id"], 30, "解析文档内容")
        
        # 调用 Langdock 工具
        result = self.call_langdock_tool(
            "document_parser",
            {
                "file_path": state["contract_file"]["path"]
            }
        )
        
        state["parsed_text"] = result["data"]["raw_text"]
        state["contract_structure"] = result["data"]["structure"]
        state["progress"] = 30
        
        return state
    
    def retrieve_regulations_node(self, state: ContractState) -> ContractState:
        """节点3: 检索法规"""
        
        self.update_progress(state["execution_id"], 50, "检索相关法规")
        
        # 调用 Langdock 工具
        result = self.call_langdock_tool(
            "regulation_retrieval",
            {
                "contract_text": state["parsed_text"]
            }
        )
        
        # 检查结果数量
        if result["data"]["count"] < 3:
            # 自动重试（工具内部已实现）
            self.update_progress(
                state["execution_id"], 
                55, 
                "检索结果不足，正在补充关键词重试..."
            )
        
        state["regulations"] = result["data"]["regulations"]
        state["progress"] = 50
        
        return state
    
    def assess_risk_node(self, state: ContractState) -> ContractState:
        """节点4: 风险评估"""
        
        self.update_progress(state["execution_id"], 70, "评估合同风险")
        
        result = self.call_langdock_tool(
            "risk_assessment",
            {
                "contract_text": state["parsed_text"],
                "regulations": state["regulations"]
            }
        )
        
        state["risk_assessment"] = result["data"]
        state["progress"] = 70
        
        return state
    
    def generate_report_node(self, state: ContractState) -> ContractState:
        """节点5: 生成报告"""
        
        self.update_progress(state["execution_id"], 85, "生成审批报告")
        
        result = self.call_langdock_tool(
            "report_generator",
            {
                "contract_data": state["contract_structure"],
                "regulations": state["regulations"],
                "risk_assessment": state["risk_assessment"]
            }
        )
        
        state["report"] = result["data"]
        state["progress"] = 85
        
        return state
    
    # ========== 条件路由函数 ==========
    
    def route_by_format(self, state: ContractState) -> str:
        """根据文件格式路由"""
        return "document" if state["file_format"] == "document" else "image"
    
    def route_by_risk(self, state: ContractState) -> str:
        """根据风险等级路由"""
        risk_level = state["risk_assessment"]["risk_level"]
        return "high" if risk_level == "high" else "low"
    
    # ========== 辅助方法 ==========
    
    def call_langdock_tool(self, tool_name: str, input_data: dict) -> dict:
        """调用 Langdock 工具"""
        # 这里是关键：LangGraph 调用 Langdock
        response = requests.post(
            f"http://langdock-service:8002/tools/{tool_name}",
            json=input_data
        )
        return response.json()
    
    def update_progress(self, execution_id: str, progress: int, message: str):
        """更新进度（推送给前端）"""
        # 通过 WebSocket 或 Redis 发布进度
        redis_client.publish(
            f"progress:{execution_id}",
            json.dumps({
                "progress": progress,
                "message": message,
                "timestamp": datetime.now().isoformat()
            })
        )
```

**LangGraph 需要调用具体工具时，请求 Langdock** 👇

---

## 第四层：Langdock 工具执行层

### 🔧 Langdock 服务

```python
# langdock_service/api.py

from fastapi import FastAPI
from tools import ToolRegistry

app = FastAPI()
registry = ToolRegistry()

# 注册所有工具
registry.register(DocumentParserTool())
registry.register(OCRParserTool())
registry.register(RegulationRetrievalTool())
registry.register(RiskAssessmentTool())
registry.register(ReportGeneratorTool())

@app.post("/tools/{tool_name}")
async def execute_tool(tool_name: str, request: ToolRequest):
    """
    执行指定工具
    """
    # 1. 获取工具实例
    tool = registry.get_tool(tool_name)
    
    # 2. 验证输入
    is_valid, error = tool.validate_input(request.input)
    if not is_valid:
        return {"success": False, "error": error}
    
    # 3. 执行工具
    try:
        result = tool.run(request.input, request.context)
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

### 📄 文档解析工具实现（示例）

```python
# tools/document_parser.py

class DocumentParserTool(BaseTool):
    """文档解析工具"""
    
    def __init__(self):
        self.name = "document_parser"
        self.description = "解析 PDF/DOCX 格式的合同文档"
    
    def run(self, input: dict, context: dict) -> dict:
        """
        执行解析
        """
        file_path = input["file_path"]
        
        # 1. 判断文件类型
        if file_path.endswith('.pdf'):
            text, structure = self._parse_pdf(file_path)
        elif file_path.endswith(('.docx', '.doc')):
            text, structure = self._parse_docx(file_path)
        else:
            return {
                "success": False,
                "error": "不支持的文件格式"
            }
        
        # 2. 返回结果
        return {
            "success": True,
            "data": {
                "raw_text": text,
                "structure": structure,
                "metadata": {
                    "page_count": len(structure.get("pages", [])),
                    "word_count": len(text.split())
                }
            }
        }
    
    def _parse_pdf(self, file_path: str) -> tuple[str, dict]:
        """解析 PDF"""
        import pdfplumber
        
        text = ""
        pages = []
        
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                text += page_text + "\n"
                
                pages.append({
                    "page_number": i + 1,
                    "text": page_text
                })
        
        # 提取结构化信息
        structure = {
            "pages": pages,
            "parties": self._extract_parties(text),
            "clauses": self._extract_clauses(text)
        }
        
        return text, structure
    
    def _extract_parties(self, text: str) -> dict:
        """提取合同双方"""
        # 使用正则或 NLP 提取
        import re
        
        party_a = re.search(r'甲方[：:](.*?)(?:\n|乙方)', text)
        party_b = re.search(r'乙方[：:](.*?)(?:\n|第)', text)
        
        return {
            "party_a": party_a.group(1).strip() if party_a else None,
            "party_b": party_b.group(1).strip() if party_b else None
        }
```

**工具执行完成，结果返回给 LangGraph** 👆

---

## 第五层：数据流转和状态同步

### 📡 实时进度更新（WebSocket）

```python
# frontend/websocket_client.js

// 前端连接 WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = function() {
    // 订阅执行进度
    ws.send(JSON.stringify({
        action: 'subscribe',
        execution_id: 'exec_abc123'
    }));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    // 更新 UI 进度条
    updateProgressBar(data.progress);
    updateStatusMessage(data.message);
    
    // 如果完成，显示结果
    if (data.status === 'completed') {
        showResults(data.result);
    }
};
```

### 🔄 完整数据流转图

```
用户上传文件
    ↓
┌───────────────────────────────────────────────────┐
│ N8N: Webhook 接收                                  │
│ → 保存文件到 /data/contracts/...                  │
│ → POST http://langgraph:8001/execute             │
│   Body: { file_path, user_id, execution_id }     │
└───────────────┬───────────────────────────────────┘
                ↓
┌───────────────────────────────────────────────────┐
│ LangGraph: 工作流编排                              │
│                                                    │
│ 节点1: identify_format                            │
│   → 识别格式: PDF                                  │
│   → 更新进度: 10%                                  │
│   → WebSocket 推送给前端                           │
│                                                    │
│ 节点2: parse_document                             │
│   → POST http://langdock:8002/tools/document_parser│
│   → 等待 Langdock 返回...                         │
└───────────────┬───────────────────────────────────┘
                ↓
┌───────────────────────────────────────────────────┐
│ Langdock: document_parser 工具                    │
│   → 打开 PDF 文件                                  │
│   → 提取文本（使用 pdfplumber）                   │
│   → 识别结构（甲方、乙方、条款）                  │
│   → 返回结果                                       │
│   Return: {                                       │
│     success: true,                                │
│     data: {                                       │
│       raw_text: "...",                            │
│       structure: {...}                            │
│     }                                             │
│   }                                               │
└───────────────┬───────────────────────────────────┘
                ↓
┌───────────────────────────────────────────────────┐
│ LangGraph: 继续执行                                │
│   → 保存 parsed_text 到状态                       │
│   → 更新进度: 30%                                  │
│   → 进入下一节点: retrieve_regulations            │
│                                                    │
│   → POST http://langdock:8002/tools/regulation_retrieval│
└───────────────┬───────────────────────────────────┘
                ↓
             (继续...)
                ↓
┌───────────────────────────────────────────────────┐
│ LangGraph: 所有节点执行完成                       │
│   → 最终状态:                                      │
│     {                                             │
│       risk_level: "low",                          │
│       report: {                                   │
│         report_path: "/reports/abc123.pdf",      │
│         report_url: "http://..."                  │
│       }                                           │
│     }                                             │
│   → 返回结果给 N8N                                │
└───────────────┬───────────────────────────────────┘
                ↓
┌───────────────────────────────────────────────────┐
│ N8N: 接收 LangGraph 返回                          │
│   → IF 节点判断: risk_level === "low"            │
│   → 走 False 分支: auto_approval                 │
│   → 发送邮件通知用户                               │
│   → 保存结果到数据库                               │
│   → 返回响应给用户 (Webhook Response)            │
└───────────────┬───────────────────────────────────┘
                ↓
┌───────────────────────────────────────────────────┐
│ 用户界面: 显示最终结果                            │
│   ✅ 处理完成！                                    │
│   风险等级: 低风险                                 │
│   审批状态: 已自动通过                             │
│   [下载报告] [查看详情]                           │
└───────────────────────────────────────────────────┘
```

---

## 完整用户体验流程

### ⏱️ 时间线视图

```
T+0秒   用户: 点击上传文件
        ↓
T+1秒   前端: 文件上传到服务器
        UI: 显示 "上传中..." 
        ↓
T+2秒   N8N: Webhook 接收请求
        N8N: 保存文件
        N8N: 调用 LangGraph
        UI: 显示 "处理中..." 进度 0%
        ↓
T+3秒   LangGraph: 识别格式 → PDF
        UI: 进度 10% "识别文件格式"
        ↓
T+8秒   LangGraph: 调用文档解析工具
        Langdock: 执行 PDF 解析
        UI: 进度 30% "解析文档内容"
        ↓
T+15秒  LangGraph: 调用法规检索工具
        Langdock: 向量检索相关法规
        UI: 进度 50% "检索相关法规"
        ↓
T+25秒  LangGraph: 调用风险评估工具
        Langdock: LLM 分析风险
        UI: 进度 70% "评估合同风险"
        ↓
T+30秒  LangGraph: 生成报告
        Langdock: 生成 Word 文档
        UI: 进度 85% "生成审批报告"
        ↓
T+32秒  LangGraph: 判断风险等级 → 低风险
        LangGraph: 进入自动审批分支
        LangGraph: 返回结果给 N8N
        UI: 进度 95% "完成审批流程"
        ↓
T+34秒  N8N: 发送通知邮件
        N8N: 保存到数据库
        N8N: 返回响应
        ↓
T+35秒  UI: 显示完成界面
        UI: ✅ 处理完成！
        UI: 风险等级: 低风险
        UI: 状态: 已自动通过
        UI: [下载报告]
```

---

## 关键技术要点

### 1. 前端实时更新

```javascript
// 使用 WebSocket 接收实时进度
function connectProgressStream(executionId) {
    const ws = new WebSocket(`ws://server/progress/${executionId}`);
    
    ws.onmessage = (event) => {
        const update = JSON.parse(event.data);
        
        // 更新进度条
        document.getElementById('progress-bar').style.width = 
            `${update.progress}%`;
        
        // 更新状态文本
        document.getElementById('status-text').textContent = 
            update.message;
        
        // 更新流程图中对应节点的状态
        updateFlowchartNode(update.current_step, update.status);
    };
}
```

### 2. N8N 调用外部服务

```javascript
// N8N HTTP Request 节点配置
{
  "method": "POST",
  "url": "http://langgraph-service:8001/execute/contract_processing",
  "body": {
    "file_path": "={{ $json.file_path }}",
    "user_id": "={{ $json.user_id }}"
  },
  "options": {
    "response": {
      "response": {
        "fullResponse": false,
        "responseFormat": "json"
      }
    }
  }
}
```

### 3. LangGraph 状态管理

```python
# 状态持久化（使用 Redis）
def save_state(execution_id: str, state: dict):
    redis_client.setex(
        f"workflow_state:{execution_id}",
        3600,  # 1小时过期
        json.dumps(state)
    )

def load_state(execution_id: str) -> dict:
    data = redis_client.get(f"workflow_state:{execution_id}")
    return json.loads(data) if data else None
```

### 4. Langdock 工具隔离

```python
# 每个工具独立运行，互不影响
class ToolRegistry:
    def __init__(self):
        self.tools = {}
    
    def register(self, tool: BaseTool):
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> BaseTool:
        if name not in self.tools:
            raise ToolNotFoundError(f"Tool {name} not registered")
        return self.tools[name]
```

### 5. 错误处理和重试

```python
# 工具调用失败自动重试
@retry(max_attempts=3, backoff=30)
def call_langdock_tool(tool_name: str, input_data: dict) -> dict:
    try:
        response = requests.post(
            f"http://langdock-service:8002/tools/{tool_name}",
            json=input_data,
            timeout=60
        )
        return response.json()
    except Exception as e:
        logger.error(f"Tool {tool_name} failed: {e}")
        # 尝试备用工具
        if has_backup(tool_name):
            return call_backup_tool(tool_name, input_data)
        raise
```

### 6. 进度推送机制

```python
# 使用 Redis Pub/Sub 实现实时进度推送
def update_progress(execution_id: str, progress: int, message: str):
    """更新进度并推送给前端"""
    # 1. 保存到 Redis
    redis_client.hset(
        f"progress:{execution_id}",
        mapping={
            "progress": progress,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
    )
    
    # 2. 发布到频道（前端 WebSocket 订阅此频道）
    redis_client.publish(
        f"progress:{execution_id}",
        json.dumps({
            "progress": progress,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    )
```

---

## 设计优势

### ✅ 用户体验优势

1. **简单易用**
   - 只需拖拽上传文件
   - 实时看到处理进度
   - 可视化流程图展示

2. **快速高效**
   - 自动化处理，无需人工干预
   - 并行处理多个步骤
   - 平均 30-40 秒完成一份合同

3. **透明可控**
   - 每一步都有进度反馈
   - 可以查看详细日志
   - 支持暂停和重试

### ✅ 管理员优势

1. **可视化配置**
   - N8N 拖拽式配置流程
   - 无需编写代码
   - 修改流程只需几分钟

2. **灵活调整**
   - 随时添加新节点
   - 修改条件分支
   - 调整工具参数

3. **实时监控**
   - 查看所有执行历史
   - 监控系统性能
   - 及时发现问题

### ✅ 开发者优势

1. **清晰分层**
   - 每层职责明确
   - 接口标准统一
   - 易于理解和维护

2. **独立开发**
   - 工具层独立开发测试
   - 流程层独立调试
   - UI 层独立优化

3. **易于扩展**
   - 添加新工具只需实现标准接口
   - 新增流程只需在 LangGraph 中定义
   - 前端可独立升级

### ✅ 系统可靠性

1. **容错机制**
   - 工具调用失败自动重试
   - 支持备用工具切换
   - 异常时人工介入

2. **状态管理**
   - 所有中间结果持久化
   - 支持断点续传
   - 24小时后自动清理

3. **日志追踪**
   - 完整的执行日志
   - 每步输入输出记录
   - 便于问题排查

---

## 实施建议

### 📝 开发顺序

1. **第1-2周**：搭建基础设施
   - 部署 N8N、Redis、数据库
   - 搭建 LangGraph 服务框架
   - 搭建 Langdock 服务框架

2. **第3-4周**：开发核心工具
   - 实现文档解析工具
   - 实现法规检索工具（Mock 数据）
   - 实现风险评估工具（简化版）

3. **第5-6周**：集成流程
   - 在 LangGraph 中定义流程
   - 在 N8N 中创建工作流
   - 实现端到端测试

4. **第7-8周**：完善功能
   - 添加进度推送
   - 实现可视化展示
   - 完善错误处理

5. **第9-10周**：优化和测试
   - 性能优化
   - 压力测试
   - 用户测试

### 🎯 关键里程碑

- ✅ **Week 2**: 基础架构搭建完成，各服务可互相调用
- ✅ **Week 4**: 核心工具开发完成，可独立运行
- ✅ **Week 6**: 端到端流程打通，可处理简单合同
- ✅ **Week 8**: 功能完善，支持实时进度和可视化
- ✅ **Week 10**: 系统优化完成，达到生产环境标准

---

## 相关文档

- [需求文档](./req.md) - 详细的功能需求和考核标准
- [模块划分](./modules.md) - 13 个模块的详细设计
- [N8N 学习笔记](./notes/N8N/N8N.md) - N8N 使用指南
- [项目 README](./README.md) - 项目概述

---

## 总结

本指南从用户界面开始，自顶向下讲解了整个智能合同处理系统的实现。关键点包括：

1. **四层架构**：UI → N8N → LangGraph → Langdock
2. **清晰职责**：每层专注自己的功能，通过标准接口通信
3. **数据流转**：从用户上传到最终结果，数据如何在各层间流动
4. **实时反馈**：通过 WebSocket 和 Redis 实现进度推送
5. **可视化**：N8N 提供流程可视化，便于配置和监控

这样的设计确保了系统的**灵活性**、**可维护性**和**可扩展性**，同时提供了良好的**用户体验**。

---

*文档版本: v1.0*  
*最后更新: 2025-12-04*  
*作者: Contract Forge Team*

