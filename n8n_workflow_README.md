# N8N 工作流配置说明

## 工作流概述

这个 N8N 工作流实现了合同处理自动化流程，包括文档解析、风险评估和基于风险等级的分支处理。

## 工作流节点说明

### 1. Webhook 触发器
- **节点名称**: Webhook - 合同处理触发
- **类型**: Webhook (POST)
- **路径**: `/contract-process`
- **参数**: 
  ```json
  {
    "contract_id": "合同ID"
  }
  ```

### 2. 步骤1: 文档解析
- **节点名称**: 步骤1: 文档解析
- **类型**: HTTP Request
- **API**: `POST http://localhost:8000/api/tools/execute`
- **请求体**:
  ```json
  {
    "tool_name": "document_parser",
    "parameters": {
      "file_path": "/path/to/contracts/{contract_id}.pdf"
    }
  }
  ```

### 3. 步骤2: 风险评估
- **节点名称**: 步骤2: 风险评估
- **类型**: HTTP Request
- **API**: `POST http://localhost:8000/api/tools/execute`
- **请求体**:
  ```json
  {
    "tool_name": "risk_assessment",
    "parameters": {
      "contract_text": "{从步骤1获取的文本内容}",
      "risk_types": ["legal", "financial"]
    }
  }
  ```

### 4. 风险等级判断
- **节点名称**: 风险等级判断
- **类型**: Switch
- **判断条件**: 
  - 低风险 (`low`) 或中风险 (`medium`) → 执行自动审批
  - 高风险 (`high`) → 发送邮件给法务团队

### 5. 低/中风险: 自动审批
- **节点名称**: 低/中风险: 自动审批
- **类型**: HTTP Request
- **API**: `POST http://localhost:8000/api/contracts/{contract_id}/auto-approve`
- **请求体**:
  ```json
  {
    "contract_id": "合同ID",
    "risk_level": "low/medium",
    "assessment_result": "{风险评估结果}"
  }
  ```

### 6. 高风险: 邮件通知法务
- **节点名称**: 高风险: 邮件通知法务
- **类型**: Email Send
- **收件人**: legal-team@company.com
- **主题**: 高风险合同需要人工审核 - 合同ID: {contract_id}
- **内容**: 包含合同ID、风险等级和详细评估结果

### 7. 设置最终结果
- **节点名称**: 设置最终结果
- **类型**: Set
- **功能**: 汇总最终处理结果

## 导入步骤

1. 打开 N8N 界面
2. 点击 "Workflows" → "Import from File"
3. 选择 `n8n_workflow_contract_processing.json` 文件
4. 配置以下内容：

### 需要配置的项目

1. **Webhook URL**: 
   - 工作流激活后，N8N 会提供一个 Webhook URL
   - 格式类似: `https://your-n8n-instance.com/webhook/contract-process`

2. **API 地址**: 
   - **默认配置**：工作流已配置为 `http://host.docker.internal:8000`（适用于 N8N 在 Docker 中，后端在宿主机）
   - **根据部署方式修改地址**：
     - **N8N 在 Docker 中，后端在宿主机（默认）**：`http://host.docker.internal:8000` ✅ 已配置
     - **本地开发（N8N 和后端在同一台机器）**：修改为 `http://127.0.0.1:8000`
     - **N8N 在 Docker 中，后端也在 Docker**：使用 Docker 网络名称，如 `http://backend:8000`
     - **远程服务器**：使用实际 IP 或域名，如 `http://192.168.1.100:8000` 或 `http://api.example.com:8000`
   - **重要**: 
     - 确保后端服务正在运行：`python backend/main.py` 或 `uvicorn backend.main:app --host 0.0.0.0 --port 8000`
     - 确保后端监听 `0.0.0.0` 而不是 `127.0.0.1`，以便外部访问
     - 检查防火墙是否允许 8000 端口访问
     - **注意**：`host.docker.internal` 在 Linux 上可能不可用，需要额外配置或使用宿主机 IP

3. **邮件配置**:
   - 在 "高风险: 邮件通知法务" 节点中配置 SMTP 服务器信息
   - 修改发件人和收件人邮箱地址

4. **文件路径**:
   - 在 "步骤1: 文档解析" 节点中，修改文件路径为实际存储路径
   - 可以使用表达式: `=/path/to/contracts/{{ $json.body.contract_id }}.pdf`

## API 调用示例

### 触发工作流

```bash
curl -X POST https://your-n8n-instance.com/webhook/contract-process \
  -H "Content-Type: application/json" \
  -d '{
    "contract_id": "contract-20250101-001"
  }'
```

### 后端 API 接口

工作流需要以下后端 API 接口：

1. **工具执行接口** (已存在):
   - `POST /api/tools/execute`
   - 参数: `tool_name`, `parameters`

2. **自动审批接口** (需要创建):
   - `POST /api/contracts/{contract_id}/auto-approve`
   - 参数: `contract_id`, `risk_level`, `assessment_result`

## 工作流执行流程

```
1. API 调用触发 Webhook
   ↓
2. 文档解析 (提取合同文本)
   ↓
3. 风险评估 (分析风险等级)
   ↓
4. 风险等级判断
   ├─ 低/中风险 → 自动审批 API
   └─ 高风险 → 邮件通知法务
   ↓
5. 设置最终结果
```

## 注意事项

1. **错误处理**: 建议在每个 HTTP Request 节点后添加错误处理节点
2. **重试机制**: 可以在节点设置中配置重试次数和间隔
3. **日志记录**: N8N 会自动记录每个节点的执行日志
4. **数据传递**: 使用 N8N 表达式语法访问上游节点的数据
   - `{{ $json.body.contract_id }}` - 访问 Webhook 的请求体
   - `{{ $('步骤1: 文档解析').item.json.data.text_content }}` - 访问步骤1的输出

## 扩展建议

1. **添加合规校验**: 在风险评估前添加合规规则检查
2. **添加通知节点**: 在自动审批后添加成功通知
3. **添加数据存储**: 将处理结果保存到数据库
4. **添加监控**: 集成监控和告警系统

