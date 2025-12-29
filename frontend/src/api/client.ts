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
  
  // 与 LLM 对话（支持工具调用）
  chat: async (messages: ChatMessage[], temperature?: number, maxTokens?: number) => {
    const response = await api.post("/llm/chat", {
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
};

export default api;
