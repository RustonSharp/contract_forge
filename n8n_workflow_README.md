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
    "file_name": "文件名或文件标识符（程序会在 uploads 目录下自动查找）"
  }
  ```
- **示例**:
  ```json
  {
    "file_name": "4ed6db58-ff05-4b8a-b2a6-e6496b8072b0_test_contract.pdf"
  }
  ```

### 2. 步骤1: 文档解析
- **节点名称**: 步骤1: 文档解析
- **类型**: HTTP Request
- **API**: `POST http://host.docker.internal:8000/api/tools/execute`
- **请求体**:
  ```json
  {
    "tool_name": "document_parser",
    "parameters": {
      "file_path": "{从 Webhook 获取的 file_name}"
    }
  }
  ```
- **说明**: 文档解析工具支持文件名自动查找，会在 `uploads` 目录下自动匹配文件

### 3. 步骤2: 风险评估
- **节点名称**: 步骤2: 风险评估
- **类型**: HTTP Request
- **API**: `POST http://host.docker.internal:8000/api/tools/execute`
- **请求体**:
  ```json
  {
    "tool_name": "risk_assessment",
    "parameters": {
      "contract_text": "{从步骤1获取的 text_content}",
      "risk_types": ["legal", "financial"]
    }
  }
  ```
- **说明**: 使用 N8N 表达式语法 `$('步骤1: 文档解析').item.json.body.data.text_content` 获取文档解析结果

### 4. 风险等级判断
- **节点名称**: 风险等级判断
- **类型**: Switch
- **判断条件**: 
  - **规则1**: 风险等级 = `low` → 输出到路径 0（自动审批）
  - **规则2**: 风险等级 = `high` → 输出到路径 1（邮件通知）
  - **默认路径**: 其他情况（如 `medium`）→ 输出到路径 0（自动审批）
- **数据路径**: `$json.body.data.overall_risk_level`

### 5. 低/中风险: 自动审批
- **节点名称**: 低/中风险: 自动审批
- **类型**: HTTP Request
- **API**: `POST http://host.docker.internal:8000/api/contracts/auto-approve`
- **请求体**:
  ```json
  {
    "file_name": "{文件名}",
    "risk_level": "{风险等级}",
    "assessment_result": "{完整的风险评估结果对象}"
  }
  ```
- **说明**: 
  - 接收来自 Switch 节点路径 0 的数据（低风险）
  - 使用 `$('步骤2: 风险评估').item.json.body.data` 获取完整的评估结果

### 6. 高风险: 邮件通知法务
- **节点名称**: 高风险: 邮件通知法务
- **类型**: Email Send
- **收件人**: legal-team@company.com
- **发件人**: contract-system@company.com
- **主题**: 高风险合同需要人工审核 - 文件名: {file_name}
- **说明**: 
  - 接收来自 Switch 节点路径 1 的数据（高风险）
  - 需要在 N8N 界面中配置 SMTP 服务器信息
  - 建议添加邮件内容（message）字段，包含文件名、风险等级和详细评估结果

### 7. 设置最终结果
- **节点名称**: 设置最终结果
- **类型**: Set
- **功能**: 汇总最终处理结果

## 导入步骤

1. 打开 N8N 界面
2. 点击 "Workflows" → "Import from File"
3. 选择 `合同处理自动化流程.json` 文件
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

4. **文件查找**:
   - 文档解析工具支持文件名自动查找功能
   - 只需提供文件名或文件标识符，程序会在 `uploads` 目录下自动匹配
   - 支持精确匹配、部分匹配和 UUID 前缀匹配

## API 调用示例

### 触发工作流

```bash
curl -X POST https://your-n8n-instance.com/webhook/contract-process \
  -H "Content-Type: application/json" \
  -d '{
    "file_name": "4ed6db58-ff05-4b8a-b2a6-e6496b8072b0_test_contract.pdf"
  }'
```

或者仅提供文件名的一部分（UUID）：

```bash
curl -X POST https://your-n8n-instance.com/webhook/contract-process \
  -H "Content-Type: application/json" \
  -d '{
    "file_name": "4ed6db58-ff05-4b8a-b2a6-e6496b8072b0"
  }'
```

### 后端 API 接口

工作流需要以下后端 API 接口：

1. **工具执行接口** (已存在):
   - `POST /api/tools/execute`
   - 参数: `tool_name`, `parameters`

2. **自动审批接口** (需要创建):
   - `POST /api/contracts/auto-approve`
   - 请求体参数: 
     ```json
     {
       "file_name": "文件名",
       "risk_level": "风险等级（low/medium/high）",
       "assessment_result": "完整的风险评估结果对象"
     }
     ```

## 工作流执行流程

```
1. API 调用触发 Webhook (传入 file_name)
   ↓
2. Webhook 响应 (返回确认信息)
   ↓
3. 文档解析 (使用 file_name 在 uploads 目录查找文件，提取合同文本)
   ↓
4. 风险评估 (使用文档解析的 text_content，分析风险等级)
   ↓
5. 风险等级判断 (Switch 节点)
   ├─ [路径0] 低风险 (low) → 自动审批 API
   └─ [路径1] 高风险 (high) → 邮件通知法务
   ↓
6. 设置最终结果 (汇总处理结果)
```

## Switch 节点配置说明

Switch 节点使用 `rules.values` 结构，每个规则对应一个输出路径：

- **规则1** (路径 0): `overall_risk_level = "low"` → 自动审批
- **规则2** (路径 1): `overall_risk_level = "high"` → 邮件通知

**注意**: 如果风险等级是 `medium` 或其他值，且不匹配任何规则，数据会流向第一个匹配的路径或默认路径。

## 注意事项

1. **错误处理**: 建议在每个 HTTP Request 节点后添加错误处理节点
2. **重试机制**: 可以在节点设置中配置重试次数和间隔
3. **日志记录**: N8N 会自动记录每个节点的执行日志
4. **数据传递**: 使用 N8N 表达式语法访问上游节点的数据
   - `{{ $json.body.file_name }}` - 访问 Webhook 的请求体中的文件名
   - `$('步骤1: 文档解析').item.json.body.data.text_content` - 访问步骤1的输出（注意：使用 `body.data` 因为 HTTP Request 节点返回完整响应）
   - `$('步骤2: 风险评估').item.json.body.data.overall_risk_level` - 访问步骤2的风险等级
   - **重要**: 当 HTTP Request 节点设置了 `fullResponse: true` 时，响应数据在 `body.data` 中，而不是直接在 `data` 中

## 扩展建议

1. **添加合规校验**: 在风险评估前添加合规规则检查
2. **添加通知节点**: 在自动审批后添加成功通知
3. **添加数据存储**: 将处理结果保存到数据库
4. **添加监控**: 集成监控和告警系统

