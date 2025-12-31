import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import FileUpload from "../../components/FileUpload";
import {
  Send,
  Bot,
  User,
  Activity,
  FileCheck,
  CheckCircle2,
  Circle,
  Loader2,
  AlertCircle,
} from "lucide-react";

import {
  contractApi,
  type ChatMessage,
  type ChatResponse,
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
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-8 py-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg flex items-center justify-center">
            <FileCheck className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-gray-900">智能合同处理自动化系统</h1>
            <p className="text-gray-500">
              Contract Processing Automation System
            </p>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex gap-6 p-6 overflow-hidden">
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
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-gray-900">AI 助手</h2>
            {selectedContract && (
              <p className="text-gray-500">当前合同：{selectedContract.name}</p>
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
      </main>
    </div>
  );
};

export default HomePage;
