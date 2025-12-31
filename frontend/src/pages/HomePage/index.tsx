import React, { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import FileUpload from "../../components/FileUpload";
import WorkflowPanel from "../../components/WorkflowPanel";
import {
  Send,
  Bot,
  User,
  Activity,
  CheckCircle2,
  Circle,
  Loader2,
  AlertCircle,
  Workflow,
} from "lucide-react";

import {
  contractApi,
  type ChatMessage,
  type ChatResponse,
  type WorkflowStatusResponse,
} from "../../api/client";

// 定义合同类型
interface Contract {
  id: string;
  name: string;
  size: string;
  uploadTime: string;
}

// 定义消息类型
interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

const HomePage: React.FC = () => {
  const [selectedContract, setSelectedContract] = useState<Contract | null>(
    null
  );
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [workflowId, setWorkflowId] = useState<string | null>(null);
  const [showWorkflowPanel, setShowWorkflowPanel] = useState(false); // 默认关闭，当收到 workflow_id 时自动打开
  const pollingIntervalsRef = useRef<Map<string, NodeJS.Timeout>>(new Map());

  const simulateAIResponse = async (userMessage: string) => {
    setIsTyping(true);

    try {
      // 构建消息列表
      const chatMessages: ChatMessage[] = [
        ...messages.map((msg) => ({
          role: msg.role as "user" | "assistant",
          content: msg.content,
        })),
        {
          role: "user",
          content: userMessage,
        },
      ];

      // 根据是否选中合同调用不同的接口
      let response: ChatResponse;
      if (selectedContract) {
        // 选中了合同，使用指定文件路径的接口（Contract 的 id 就是 file_path）
        response = await contractApi.chatWithFileName(selectedContract.id, chatMessages);
      } else {
        // 未选中合同，使用智能查找接口
        response = await contractApi.chat(chatMessages);
      }

      // 调试：打印完整响应
      console.log("完整响应:", JSON.stringify(response, null, 2));
      console.log("response.workflow_id:", response.workflow_id);
      console.log("response.workflow_id 类型:", typeof response.workflow_id);

      const aiMessage: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content: response.message,
        timestamp: new Date().toLocaleTimeString("zh-CN", {
          hour: "2-digit",
          minute: "2-digit",
        }),
      };

      setMessages((prev) => [...prev, aiMessage]);

      // 如果有 workflow_id，开始轮询工作流状态并自动打开工作流面板
      if (response.workflow_id && response.workflow_id.trim()) {
        console.log("✅ 收到 workflow_id:", response.workflow_id);
        setWorkflowId(response.workflow_id);
        setShowWorkflowPanel(true); // 自动打开工作流面板
        startWorkflowPolling(response.workflow_id, aiMessage.id);
      } else {
        console.log("❌ 响应中没有 workflow_id", {
          workflow_id: response.workflow_id,
          has_workflow_id: !!response.workflow_id,
          workflow_id_trimmed: response.workflow_id?.trim(),
          full_response: response
        });
        // 如果这次响应没有 workflow_id，不清除之前的 workflowId
        // 这样用户可以继续查看之前的工作流进度
      }
      // 如果需要确认多个文件处理
      if ((response as any).requires_confirmation && (response as any).files) {
        // 这里可以添加UI提示，让用户选择要处理的文件
        // 目前先显示提示信息，用户可以通过回复"全部处理"或"是"来确认
        console.log("需要确认处理多个文件:", (response as any).files);
      }

      // 如果需要确认多个文件处理
      if ((response as any).requires_confirmation && (response as any).files) {
        // 显示文件列表，等待用户确认
        console.log("需要确认处理多个文件:", (response as any).files);
        // 用户可以通过回复"全部处理"或"是"来确认
      }

      // 如果有工具调用，显示相关信息
      if (response.tool_calls && response.tool_calls.length > 0) {
        console.log("工具调用:", response.tool_calls);
        // 可以在这里添加工具调用结果的显示
      }
    } catch (error: any) {
      console.error("Error calling backend API:", error);

      const errorMsg =
        error.response?.data?.detail ||
        error.message ||
        "无法连接到后端服务器，请检查服务是否启动。";

      const aiMessage: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content: `❌ 错误: ${errorMsg}`,
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages((prev) => [...prev, aiMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  // 处理文件上传
  const handleFileUpload = async (file: File) => {
    // 文件上传已经在 FileUpload 组件中处理
    // 这里可以添加额外的处理逻辑，比如自动发送消息
    console.log("File uploaded:", file.name);

    // 可选：自动发送一条消息
    if (selectedContract) {
      const autoMessage = `请帮我处理一下 ${selectedContract.name}`;
      setInput(autoMessage);
      // 不自动发送，让用户决定
    }
  };

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date().toLocaleTimeString("zh-CN", {
        hour: "2-digit",
        minute: "2-digit",
      }),
    };

    setMessages((prev) => [...prev, userMessage]);
    simulateAIResponse(input);
    setInput("");
    // 注意：不在这里清除 workflowId，因为用户可能想继续查看之前的工作流进度
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // 开始轮询工作流状态
  const startWorkflowPolling = (workflowId: string, messageId: string) => {
    // 清除之前的轮询（如果存在）
    const existingInterval = pollingIntervalsRef.current.get(messageId);
    if (existingInterval) {
      clearInterval(existingInterval);
    }

    // 立即查询一次状态
    pollWorkflowStatus(workflowId, messageId);

    // 每 2 秒轮询一次
    const interval = setInterval(() => {
      pollWorkflowStatus(workflowId, messageId);
    }, 2000);

    pollingIntervalsRef.current.set(messageId, interval);
  };

  // 轮询工作流状态
  const pollWorkflowStatus = async (workflowId: string, messageId: string) => {
    try {
      const status: WorkflowStatusResponse = await contractApi.getWorkflowStatus(workflowId);

      // 更新消息内容
      setMessages((prev) => {
        return prev.map((msg) => {
          if (msg.id === messageId) {
            let content = msg.content;

            // 根据状态更新消息内容（只在 completed 或 failed 时更新）
            if (status.status === "completed") {
              // 工作流完成，显示结果
              let resultText = status.message || "✅ 工作流处理完成。";
              
              if (status.result) {
                // 格式化结果
                const resultParts: string[] = [];
                
                if (status.result.file_path) {
                  resultParts.push(`**处理文件**: ${status.result.file_path}`);
                }
                if (status.result.risk_level) {
                  const riskLevel = status.result.risk_level;
                  const riskEmoji = riskLevel === "high" ? "🔴" : riskLevel === "medium" ? "🟡" : "🟢";
                  resultParts.push(`**风险等级**: ${riskEmoji} ${riskLevel}`);
                }
                
                // 如果有其他结果数据，也显示出来
                if (resultParts.length > 0) {
                  resultText += "\n\n" + resultParts.join("\n\n");
                }
              }

              content = resultText;
            } else if (status.status === "failed") {
              // 工作流失败
              content = `❌ 工作流处理失败: ${status.error || status.message || "未知错误"}`;
            }
            // running 或 pending 状态下保持原消息不变（初始消息已经说明正在处理中）

            return { ...msg, content };
          }
          return msg;
        });
      });

      // 如果状态是 completed 或 failed，停止轮询
      if (status.status === "completed" || status.status === "failed") {
        const interval = pollingIntervalsRef.current.get(messageId);
        if (interval) {
          clearInterval(interval);
          pollingIntervalsRef.current.delete(messageId);
        }
        // 停止轮询后，滚动到底部以显示最新消息
        setTimeout(() => {
          const messagesContainer = document.querySelector('.overflow-y-auto');
          if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
          }
        }, 100);
      }
    } catch (error: any) {
      console.error("查询工作流状态失败:", error);
      // 错误时不要更新消息，保持原样
      // 可以添加错误重试逻辑，这里暂时不处理
    }
  };

  // 组件卸载时清理所有轮询
  useEffect(() => {
    return () => {
      pollingIntervalsRef.current.forEach((interval) => {
        clearInterval(interval);
      });
      pollingIntervalsRef.current.clear();
    };
  }, []);

  return (
    <div className="h-full flex flex-col">
      {/* Main Content */}
      <div className="flex-1 flex gap-6 p-6 overflow-hidden">
        {/* Left Panel - Upload */}
        <div className="w-80 rounded-lg border border-gray-200 shadow-sm overflow-hidden">
          <FileUpload
            onContractSelect={setSelectedContract}
            selectedContract={selectedContract}
            onFileUpload={handleFileUpload}
          />
        </div>

        {/* Center Panel - Chat */}
        <div className="flex-1 rounded-lg border border-gray-200 shadow-sm overflow-hidden flex flex-col">
          {/* Chat Header */}
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <div>
              <h2 className="text-gray-900">AI 助手</h2>
              {selectedContract && (
                <p className="text-gray-500">当前合同：{selectedContract.name}</p>
              )}
            </div>
            {workflowId && workflowId.trim() ? (
              <button
                onClick={() => {
                  console.log("打开工作流面板，workflowId:", workflowId);
                  setShowWorkflowPanel(true);
                }}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
              >
                <Workflow className="w-4 h-4" />
                <span>查看工作流进度</span>
              </button>
            ) : (
              <div className="text-xs text-gray-400" style={{ display: 'none' }}>
                {/* 调试：当前 workflowId = {workflowId || "null"} */}
              </div>
            )}
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.length === 0 && (
              <div className="text-center py-12">
                <Bot className="mx-auto mb-4 w-12 h-12 text-gray-300" />
                <p className="text-gray-500 mb-2">您好！我是智能合同处理助手</p>
                <p className="text-gray-400">您可以通过对话处理合同文件</p>
                <p className="text-gray-400 mt-2">
                  例如："帮我处理一下昨天上传的文件" 或 "解析 test_contract.pdf"
                </p>
              </div>
            )}

            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${
                  message.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                {message.role === "assistant" && (
                  <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                    <Bot className="w-5 h-5 text-blue-600" />
                  </div>
                )}

                <div
                  className={`max-w-[70%] rounded-lg px-4 py-3 ${
                    message.role === "user"
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 text-gray-900"
                  }`}
                >
                  {message.role === "assistant" ? (
                    <div className="prose prose-sm max-w-none dark:prose-invert">
                      <ReactMarkdown
                        components={{
                          h1: ({ ...props }: any) => (
                            <h1
                              className="text-lg font-bold mt-4 mb-2 text-gray-900"
                              {...props}
                            />
                          ),
                          h2: ({ ...props }: any) => (
                            <h2
                              className="text-base font-semibold mt-3 mb-2 text-gray-900"
                              {...props}
                            />
                          ),
                          h3: ({ ...props }: any) => (
                            <h3
                              className="text-sm font-semibold mt-2 mb-1 text-gray-900"
                              {...props}
                            />
                          ),
                          p: ({ ...props }: any) => (
                            <p
                              className="mb-2 text-gray-900 leading-relaxed"
                              {...props}
                            />
                          ),
                          ul: ({ ...props }: any) => (
                            <ul
                              className="list-disc list-inside mb-2 space-y-1 text-gray-900"
                              {...props}
                            />
                          ),
                          ol: ({ ...props }: any) => (
                            <ol
                              className="list-decimal list-inside mb-2 space-y-1 text-gray-900"
                              {...props}
                            />
                          ),
                          li: ({ ...props }: any) => (
                            <li className="ml-4 text-gray-900" {...props} />
                          ),
                          code: ({ inline, ...props }: any) =>
                            inline ? (
                              <code
                                className="bg-gray-200 px-1.5 py-0.5 rounded text-sm font-mono text-gray-800"
                                {...props}
                              />
                            ) : (
                              <code
                                className="block bg-gray-200 p-2 rounded text-sm font-mono text-gray-800 overflow-x-auto mb-2"
                                {...props}
                              />
                            ),
                          pre: ({ ...props }: any) => (
                            <pre
                              className="bg-gray-200 p-2 rounded text-sm font-mono text-gray-800 overflow-x-auto mb-2"
                              {...props}
                            />
                          ),
                          a: ({ ...props }: any) => (
                            <a
                              className="text-blue-600 hover:text-blue-800 underline"
                              {...props}
                            />
                          ),
                          strong: ({ ...props }: any) => (
                            <strong
                              className="font-semibold text-gray-900"
                              {...props}
                            />
                          ),
                          em: ({ ...props }: any) => (
                            <em className="italic text-gray-900" {...props} />
                          ),
                          blockquote: ({ ...props }: any) => (
                            <blockquote
                              className="border-l-4 border-gray-300 pl-3 italic text-gray-700 mb-2"
                              {...props}
                            />
                          ),
                          hr: ({ ...props }: any) => (
                            <hr className="my-3 border-gray-300" {...props} />
                          ),
                        }}
                      >
                        {message.content}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  )}
                  <p
                    className={`mt-1 text-xs ${
                      message.role === "user"
                        ? "text-blue-100"
                        : "text-gray-500"
                    }`}
                  >
                    {message.timestamp}
                  </p>
                </div>

                {message.role === "user" && (
                  <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0">
                    <User className="w-5 h-5 text-gray-600" />
                  </div>
                )}
              </div>
            ))}

            {isTyping && (
              <div className="flex gap-3 justify-start">
                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-5 h-5 text-blue-600" />
                </div>
                <div className="bg-gray-100 rounded-lg px-4 py-3">
                  <div className="flex gap-1">
                    <span
                      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0ms" }}
                    ></span>
                    <span
                      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: "150ms" }}
                    ></span>
                    <span
                      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: "300ms" }}
                    ></span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Chat Input */}
          <div className="p-6 border-t border-gray-200">
            <div className="flex gap-3">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={
                  selectedContract
                    ? "输入消息，例如：帮我处理一下这个合同"
                    : "输入消息，例如：帮我处理一下昨天上传的文件"
                }
                disabled={false}
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:bg-gray-50 disabled:text-gray-400"
              />
              <button
                onClick={handleSend}
                disabled={!input.trim()}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Workflow Panel - 默认打开，方便测试 */}
      {showWorkflowPanel && (
        <WorkflowPanel
          workflowId={workflowId}
          onClose={() => setShowWorkflowPanel(false)}
        />
      )}
    </div>
  );
};

export default HomePage;
