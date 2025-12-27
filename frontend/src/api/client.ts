import axios from "axios";

// 基础配置：指向你的 FastAPI 后端
const api = axios.create({
  baseURL: "http://localhost:8000/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
});

export interface ChatContext {
  task_id?: string;
  user_id?: string;
  session_id?: string;
}

export interface FlowState {
  task_id: string;
  status: "running" | "completed" | "failed";
  current_step: string;
  steps: Array<{
    id: string;
    name: string;
    status: string;
    start_time?: string;
    end_time?: string;
    duration?: number;
    progress?: number;
    output?: any;
    error?: string;
  }>;
  graph_data?: {
    nodes: Array<{ id: string; label: string; status: string }>;
    edges: Array<{ from: string; to: string }>;
  };
}

export interface ReportRequest {
  task_id: string;
  template?: "simple" | "detailed";
  format?: "markdown" | "pdf" | "word";
}

export const contractApi = {
  // 1. 自然语言交互接口（增强版）
  chat: async (message: string, context?: ChatContext) => {
    const response = await api.post("/chat", { message, context });
    return response.data;
  },

  // 2. 核心审计接口：注意处理文件上传需使用 FormData
  auditContract: async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);

    const response = await api.post("/audit", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  },

  // 3. 获取流程状态（详细步骤信息）
  getFlowState: async (taskId: string): Promise<FlowState> => {
    const response = await api.get(`/state/${taskId}`);
    return response.data;
  },

  // 4. 获取任务日志
  getTaskLogs: async (taskId: string) => {
    const response = await api.get(`/logs/${taskId}`);
    return response.data;
  },

  // 5. 生成智能报告
  generateReport: async (request: ReportRequest) => {
    const response = await api.post("/report/generate", request);
    return response.data;
  },
};

export default api;
