import axios from "axios";

// 基础配置：指向 FastAPI 后端
const api = axios.create({
  baseURL: "http://localhost:8000/api",
  headers: {
    "Content-Type": "application/json",
  },
});

// 文件信息接口
export interface FileInfo {
  file_name: string;
  file_path: string;
  file_size: number;
  upload_date: string;
  file_type: string;
}

// LLM 对话消息接口
export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

// LLM 对话响应接口
export interface ChatResponse {
  message: string;
  workflow_id?: string;  // 工作流 ID（如果调用了 n8n_workflow_trigger）
  tool_calls?: Array<{
    tool_name: string;
    parameters: Record<string, any>;
    result: {
      success: boolean;
      data?: any;
    error?: string;
    };
  }>;
  usage?: {
    prompt_tokens?: number;
    completion_tokens?: number;
    total_tokens?: number;
  };
}

// 工作流状态响应接口
export interface WorkflowStatusResponse {
  workflow_id: string;
  status: "pending" | "running" | "completed" | "failed";
  file_path?: string;
  result?: {
    file_path?: string;
    risk_level?: string;
    [key: string]: any;
  };
  message?: string;
  error?: string;
  created_at: string;
  updated_at: string;
}

// 工作流节点接口
export interface WorkflowNode {
  id: string;
  name: string;
  type: string;
  position: number[];
  notes?: string;
  parameters?: Record<string, any>;
}

// 工作流定义响应接口
export interface WorkflowDefinitionResponse {
  name: string;
  nodes: WorkflowNode[];
  connections: Record<string, any>;
  active: boolean;
}

// 工作流进度响应接口
export interface WorkflowProgressResponse {
  workflow_id: string;
  status: "pending" | "running" | "completed" | "failed";
  current_node?: string;
  completed_nodes: string[];
  file_path?: string;
  result?: Record<string, any>;
  message?: string;
  error?: string;
  created_at: string;
  updated_at: string;
}

// 工具信息接口
export interface ToolInfo {
  name: string;
  display_name: string;
  description: string;
  parameters: Array<{
    name: string;
    type: string;
    description: string;
    required: boolean;
    default?: any;
  }>;
  category?: string;
  version: string;
}

// API 客户端
export const contractApi = {
  // ========== 文件管理接口 ==========
  
  // 上传文件
  uploadFile: async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);

    const response = await api.post("/files/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  },

  // 获取文件列表
  listFiles: async (date?: string, page: number = 1, pageSize: number = 20) => {
    const params: any = { page, page_size: pageSize };
    if (date) params.date = date;
    
    const response = await api.get("/files/list", { params });
    return response.data;
  },

  // 获取所有日期列表
  listDates: async () => {
    const response = await api.get("/files/list/dates");
    return response.data;
  },

  // 获取文件信息
  getFileInfo: async (fileName: string) => {
    const response = await api.get(`/files/info/${encodeURIComponent(fileName)}`);
    return response.data;
  },

  // ========== LLM 对话接口 ==========
  
  // 与 LLM 对话（支持工具调用，智能查找文件）
  chat: async (messages: ChatMessage[], temperature?: number, maxTokens?: number) => {
    const response = await api.post("/llm/chat", {
      messages,
      temperature,
      max_tokens: maxTokens,
      enable_tools: true,
    });
    return response.data as ChatResponse;
  },

  // 与 LLM 对话（指定文件路径，直接使用文件）
  chatWithFileName: async (filePath: string, messages: ChatMessage[], temperature?: number, maxTokens?: number) => {
    const response = await api.post("/llm/chat_with_file_name", {
      file_path: filePath,
      messages,
      temperature,
      max_tokens: maxTokens,
      enable_tools: true,
    });
    return response.data as ChatResponse;
  },

  // 简单对话接口
  chatSimple: async (userMessage: string, systemMessage?: string) => {
    const params: any = { user_message: userMessage };
    if (systemMessage) params.system_message = systemMessage;
    
    const response = await api.post("/llm/chat/simple", null, { params });
    return response.data as ChatResponse;
  },

  // ========== 工具管理接口 ==========
  
  // 获取所有工具列表
  listTools: async () => {
    const response = await api.get("/tools");
    return response.data as ToolInfo[];
  },

  // 获取工具信息
  getToolInfo: async (toolName: string) => {
    const response = await api.get(`/tools/${toolName}`);
    return response.data as ToolInfo;
  },

  // 执行工具
  executeTool: async (toolName: string, parameters: Record<string, any>) => {
    const response = await api.post("/tools/execute", {
      tool_name: toolName,
      parameters,
    });
    return response.data;
  },

  // 获取所有工具名称
  listToolNames: async () => {
    const response = await api.get("/tools/names");
    return response.data;
  },

  // ========== 工作流状态管理接口 ==========
  
  // 查询工作流状态
  getWorkflowStatus: async (workflowId: string) => {
    const response = await api.get(`/workflow/status/${workflowId}`);
    return response.data as WorkflowStatusResponse;
  },

  // 获取完整工作流程定义
  getWorkflowDefinition: async (configFile: string = "合同处理自动化流程.json") => {
    const response = await api.get("/workflow/definition", {
      params: { config_file: configFile },
    });
    return response.data as WorkflowDefinitionResponse;
  },

  // 获取工作流当前进度
  getWorkflowProgress: async (workflowId: string) => {
    const response = await api.get(`/workflow/progress/${workflowId}`);
    return response.data as WorkflowProgressResponse;
  },
};

export default api;
