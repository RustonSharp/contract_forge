import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import FileUpload from '../../components/FileUpload';
import FlowViewer from '../../components/FlowViewer';
import ExecutionLogs from '../../components/ExecutionLogs';
import { Send, Bot, User, Activity, FileCheck, CheckCircle2, Circle, Loader2, AlertCircle, FileText, RefreshCw } from 'lucide-react';

import {contractApi, type FlowState} from '../../api/client';

// 定义合同类型
interface Contract {
  id: string;
  name: string;
  size: string;
  uploadTime: string;
}

// 定义处理步骤类型
interface ProcessStep {
  id: string;
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  progress: number;
  description?: string;
}

// 定义消息类型
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

const HomePage: React.FC = () => {
  const [selectedContract, setSelectedContract] = useState<Contract | null>(null);
  const [processes, setProcesses] = useState<ProcessStep[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [flowState, setFlowState] = useState<FlowState | null>(null);
  const [activeTab, setActiveTab] = useState<'process' | 'flow' | 'logs'>('process');

  const processTemplates: Record<string, Omit<ProcessStep, 'id'>> = {
    parse: {
      name: '合同解析',
      status: 'pending',
      progress: 0,
      description: '提取合同文本和结构化信息'
    },
    extract: {
      name: '条款提取',
      status: 'pending',
      progress: 0,
      description: '识别并提取关键条款内容'
    },
    risk: {
      name: '风险评估',
      status: 'pending',
      progress: 0,
      description: '分析合同中的潜在法律风险'
    },
    compliance: {
      name: '合规性检查',
      status: 'pending',
      progress: 0,
      description: '对照法规要求进行合规审查'
    },
    summary: {
      name: '关键信息摘要',
      status: 'pending',
      progress: 0,
      description: '生成合同核心内容摘要'
    }
  };

  const handleTriggerProcess = (processType: string) => {
    const template = processTemplates[processType];
    if (!template) return;

    const newProcess: ProcessStep = {
      ...template,
      id: `${processType}-${Date.now()}`,
      status: 'processing'
    };

    setProcesses(prev => {
      // Check if this type of process already exists
      const existingIndex = prev.findIndex(p => p.name === template.name);
      if (existingIndex !== -1) {
        // Update existing process
        const updated = [...prev];
        updated[existingIndex] = { ...newProcess, progress: 0 };
        return updated;
      }
      // Add new process
      return [...prev, newProcess];
    });

    // Simulate progress
    let progress = 0;
    const interval = setInterval(() => {
      progress += Math.random() * 20;
      if (progress >= 100) {
        progress = 100;
        clearInterval(interval);
        
        setProcesses(prev =>
          prev.map(p =>
            p.id === newProcess.id
              ? { ...p, progress: 100, status: 'completed' }
              : p
          )
        );
      } else {
        setProcesses(prev =>
          prev.map(p =>
            p.id === newProcess.id
              ? { ...p, progress: Math.floor(progress) }
              : p
          )
        );
      }
    }, 800);
  };

  const processCommands = [
    { keywords: ['解析', '分析'], type: 'parse', response: '已开始解析合同内容，正在提取文本和结构信息...' },
    { keywords: ['条款', '提取'], type: 'extract', response: '已启动条款提取流程，正在识别关键条款...' },
    { keywords: ['风险', '评估'], type: 'risk', response: '已开始风险评估，正在分析潜在法律风险...' },
    { keywords: ['合规', '检查'], type: 'compliance', response: '已启动合规性检查，正在对照法规要求...' },
    { keywords: ['摘要', '总结'], type: 'summary', response: '已开始生成合同摘要，正在提炼关键信息...' }
  ];

  // 获取流程状态
  const fetchFlowState = async (taskId: string) => {
    try {
      const state = await contractApi.getFlowState(taskId);
      setFlowState(state);
      
      // 更新流程步骤显示
      if (state.steps) {
        const updatedProcesses: ProcessStep[] = state.steps.map(step => ({
          id: step.id,
          name: step.name,
          status: (step.status === 'completed' ? 'completed' : 
                 step.status === 'running' ? 'processing' : 
                 step.status === 'failed' ? 'error' : 'pending') as ProcessStep['status'],
          progress: step.progress || (step.status === 'completed' ? 100 : 0),
          description: step.name
        }));
        setProcesses(updatedProcesses);
      }
    } catch (error) {
      console.error('Failed to fetch flow state:', error);
    }
  };

  // 生成智能报告
  const handleGenerateReport = async () => {
    if (!currentTaskId) return;
    
    try {
      const response = await contractApi.generateReport({
        task_id: currentTaskId,
        template: 'detailed',
        format: 'markdown'
      });
      
      if (response.status === 'success' && response.data) {
        const reportContent = response.data.report || '';
        const summary = response.data.summary || '';
        
        const reportMessage: Message = {
          id: Date.now().toString(),
          role: 'assistant',
          content: `📄 智能报告已生成\n\n${summary}\n\n${reportContent}`,
          timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
        };
        
        setMessages(prev => [...prev, reportMessage]);
      }
    } catch (error) {
      console.error('Failed to generate report:', error);
    }
  };

  const simulateAIResponse = async (userMessage: string) => {
    setIsTyping(true);
    
    try {
      // 传递上下文信息（包含任务ID）
      const context = currentTaskId ? {
        task_id: currentTaskId,
        user_id: 'user-001',
        session_id: 'session-001'
      } : undefined;
      
      const response = await contractApi.chat(userMessage, context);
      
      // 新API返回格式：{ status, data: { response, suggested_actions, confidence } }
      const aiResponse = response.data?.response || response.response || '抱歉，我没有理解您的问题。';
      const suggestedActions = response.data?.suggested_actions || [];

      const aiMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: aiResponse,
        timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      };

      setMessages(prev => [...prev, aiMessage]);
      
      // 处理建议操作
      if (suggestedActions.length > 0) {
        // 可以在这里添加操作按钮
        console.log('Suggested actions:', suggestedActions);
      }
      
      // 检查是否触发了特定处理流程
      let triggeredProcess: string | null = null;
      for (const cmd of processCommands) {
        if (cmd.keywords.some(keyword => userMessage.includes(keyword))) {
          triggeredProcess = cmd.type;
          break;
        }
      }
      
      if (triggeredProcess) {
        handleTriggerProcess(triggeredProcess);
      }
      
      // 如果询问状态，刷新流程状态
      if (currentTaskId && (userMessage.includes('状态') || userMessage.includes('哪一步'))) {
        fetchFlowState(currentTaskId);
      }
      
    } catch (error: any) {
      console.error('Error calling backend API:', error);
      
      const errorMsg = error.response?.data?.detail || error.response?.data?.error_msg || '无法连接到后端服务器，请检查 Python 服务是否启动。';

      const aiMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `❌ 错误: ${errorMsg}`,
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, aiMessage]);
    } finally {
      setIsTyping(false);
    }
  };
  
  // 处理文件上传后的审计
  const handleFileUpload = async (file: File) => {
    try {
      // 默认使用 N8N 编排，除非明确设置为 false
      const useLegacyAudit = import.meta.env.VITE_USE_LEGACY_AUDIT === 'true';

      if (useLegacyAudit) {
        // 旧方式：后端 /audit 直接运行 LangGraph
        const response = await contractApi.auditContract(file);
        if (response.task_id) {
          setCurrentTaskId(response.task_id);
          // 开始轮询流程状态
          fetchFlowState(response.task_id);
          const interval = setInterval(() => {
            fetchFlowState(response.task_id);
          }, 2000);
          // 30秒后停止轮询
          setTimeout(() => clearInterval(interval), 30000);
        }
        return;
      }

      // 默认：使用 N8N 全编排工作流
      // 1) 上传文件到后端，获取 task_id 和 server-side file_path
      const prepared = await contractApi.uploadForOrchestration(file);
      if (prepared?.task_id && prepared?.file_path) {
        setCurrentTaskId(prepared.task_id);
        // 2) 触发 N8N 全编排工作流
        await contractApi.triggerN8nWorkflow(prepared.file_path, prepared.task_id);
        // 3) 轮询流程状态（由 N8N 调用 /steps/* 写入 task_states）
        fetchFlowState(prepared.task_id);
        const interval = setInterval(() => {
          fetchFlowState(prepared.task_id);
        }, 2000);
        setTimeout(() => clearInterval(interval), 30000);
      }
    } catch (error) {
      console.error('Failed to upload and audit contract:', error);
    }
  };

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMessage]);
    simulateAIResponse(input);
    setInput('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const getStatusIcon = (step: ProcessStep) => {
    switch (step.status) {
      case 'completed':
        return <CheckCircle2 className="w-5 h-5 text-green-600" />;
      case 'processing':
        return <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-600" />;
      default:
        return <Circle className="w-5 h-5 text-gray-300" />;
    }
  };

  const getStatusColor = (step: ProcessStep) => {
    switch (step.status) {
      case 'completed':
        return 'border-green-200 bg-green-50';
      case 'processing':
        return 'border-blue-200 bg-blue-50';
      case 'error':
        return 'border-red-200 bg-red-50';
      default:
        return 'border-gray-200 bg-white';
    }
  };

  const getProgressColor = (step: ProcessStep) => {
    switch (step.status) {
      case 'completed':
        return 'bg-green-600';
      case 'processing':
        return 'bg-blue-600';
      case 'error':
        return 'bg-red-600';
      default:
        return 'bg-gray-300';
    }
  };

  const activeProcesses = processes.filter(p => p.status !== 'pending');
  const completedCount = processes.filter(p => p.status === 'completed').length;

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
            <p className="text-gray-500">Contract Processing Automation System</p>
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
                <p className="text-gray-400">上传合同后，您可以通过对话触发不同的处理流程</p>
              </div>
            )}
            
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {message.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                    <Bot className="w-5 h-5 text-blue-600" />
                  </div>
                )}
                
                <div className={`max-w-[70%] rounded-lg px-4 py-3 ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}>
                  {message.role === 'assistant' ? (
                    <div className="prose prose-sm max-w-none dark:prose-invert">
                      <ReactMarkdown
                        components={{
                          // 自定义标题样式
                          h1: ({...props}: any) => <h1 className="text-lg font-bold mt-4 mb-2 text-gray-900" {...props} />,
                          h2: ({...props}: any) => <h2 className="text-base font-semibold mt-3 mb-2 text-gray-900" {...props} />,
                          h3: ({...props}: any) => <h3 className="text-sm font-semibold mt-2 mb-1 text-gray-900" {...props} />,
                          // 段落样式
                          p: ({...props}: any) => <p className="mb-2 text-gray-900 leading-relaxed" {...props} />,
                          // 列表样式
                          ul: ({...props}: any) => <ul className="list-disc list-inside mb-2 space-y-1 text-gray-900" {...props} />,
                          ol: ({...props}: any) => <ol className="list-decimal list-inside mb-2 space-y-1 text-gray-900" {...props} />,
                          li: ({...props}: any) => <li className="ml-4 text-gray-900" {...props} />,
                          // 代码块样式
                          code: ({inline, ...props}: any) => 
                            inline ? (
                              <code className="bg-gray-200 px-1.5 py-0.5 rounded text-sm font-mono text-gray-800" {...props} />
                            ) : (
                              <code className="block bg-gray-200 p-2 rounded text-sm font-mono text-gray-800 overflow-x-auto mb-2" {...props} />
                            ),
                          pre: ({...props}: any) => <pre className="bg-gray-200 p-2 rounded text-sm font-mono text-gray-800 overflow-x-auto mb-2" {...props} />,
                          // 链接样式
                          a: ({...props}: any) => <a className="text-blue-600 hover:text-blue-800 underline" {...props} />,
                          // 强调样式
                          strong: ({...props}: any) => <strong className="font-semibold text-gray-900" {...props} />,
                          em: ({...props}: any) => <em className="italic text-gray-900" {...props} />,
                          // 引用样式
                          blockquote: ({...props}: any) => <blockquote className="border-l-4 border-gray-300 pl-3 italic text-gray-700 mb-2" {...props} />,
                          // 水平线
                          hr: ({...props}: any) => <hr className="my-3 border-gray-300" {...props} />,
                        }}
                      >
                        {message.content}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  )}
                  <p className={`mt-1 text-xs ${
                    message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                  }`}>
                    {message.timestamp}
                  </p>
                </div>

                {message.role === 'user' && (
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
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
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
                placeholder={selectedContract ? "输入消息，例如：请帮我分析这份合同的风险" : "请先上传合同..."}
                disabled={!selectedContract}
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:bg-gray-50 disabled:text-gray-400"
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || !selectedContract}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Right Panel - Progress/Flow/Logs */}
        <div className="w-96 rounded-lg border border-gray-200 shadow-sm overflow-hidden flex flex-col">
          {/* Tab Header */}
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-gray-700" />
                <h2 className="text-gray-900">处理流程</h2>
              </div>
              {currentTaskId && (
                <button
                  onClick={() => currentTaskId && fetchFlowState(currentTaskId)}
                  className="p-1.5 hover:bg-gray-100 rounded transition-colors"
                  title="刷新状态"
                >
                  <RefreshCw className="w-4 h-4 text-gray-600" />
                </button>
              )}
            </div>
            
            {/* Tabs */}
            <div className="flex gap-2 mt-3">
              <button
                onClick={() => setActiveTab('process')}
                className={`px-3 py-1.5 text-sm rounded transition-colors ${
                  activeTab === 'process' 
                    ? 'bg-blue-100 text-blue-700 font-medium' 
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                步骤
              </button>
              <button
                onClick={() => setActiveTab('flow')}
                className={`px-3 py-1.5 text-sm rounded transition-colors ${
                  activeTab === 'flow' 
                    ? 'bg-blue-100 text-blue-700 font-medium' 
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                流程图
              </button>
              <button
                onClick={() => setActiveTab('logs')}
                className={`px-3 py-1.5 text-sm rounded transition-colors ${
                  activeTab === 'logs' 
                    ? 'bg-blue-100 text-blue-700 font-medium' 
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                日志
              </button>
            </div>
            
            {activeProcesses.length > 0 && activeTab === 'process' && (
              <p className="text-gray-500 mt-2 text-sm">
                已完成 {completedCount} / {activeProcesses.length} 个流程
              </p>
            )}
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-y-auto">
            {activeTab === 'process' && (
              <div className="p-6">
                {processes.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="mx-auto mb-4 w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center">
                      <Activity className="w-8 h-8 text-gray-400" />
                    </div>
                    <p className="text-gray-500 mb-2">暂无处理流程</p>
                    <p className="text-gray-400 text-sm">上传合同后开始处理</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {processes.map((process) => (
                      <div key={process.id} className={`p-4 rounded-lg border transition-all ${getStatusColor(process)}`}>
                        <div className="flex items-start gap-3 mb-3">
                          {getStatusIcon(process)}
                          <div className="flex-1">
                            <h4 className="text-gray-900">{process.name}</h4>
                            {process.description && (
                              <p className="text-gray-600 mt-1 text-sm">{process.description}</p>
                            )}
                          </div>
                        </div>

                        {/* Progress Bar */}
                        {process.status !== 'pending' && (
                          <div className="space-y-1">
                            <div className="flex justify-between items-center text-gray-600 text-sm">
                              <span>进度</span>
                              <span>{process.progress}%</span>
                            </div>
                            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                              <div
                                className={`h-full transition-all duration-500 ${getProgressColor(process)}`}
                                style={{ width: `${process.progress}%` }}
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
            
            {activeTab === 'flow' && (
              <div className="p-6">
                {flowState && flowState.graph_data ? (
                  <FlowViewer
                    nodes={flowState.graph_data.nodes}
                    edges={flowState.graph_data.edges}
                    currentStep={flowState.current_step}
                  />
                ) : currentTaskId ? (
                  <div className="text-center py-12">
                    <Loader2 className="mx-auto mb-4 w-8 h-8 text-gray-400 animate-spin" />
                    <p className="text-gray-500">加载流程图中...</p>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <p className="text-gray-500">暂无流程数据</p>
                    <p className="text-gray-400 text-sm mt-2">上传合同后查看流程图</p>
                  </div>
                )}
              </div>
            )}
            
            {activeTab === 'logs' && (
              <div className="h-full">
                {currentTaskId ? (
                  <ExecutionLogs taskId={currentTaskId} autoRefresh={true} />
                ) : (
                  <div className="text-center py-12 px-6">
                    <p className="text-gray-500">暂无日志</p>
                    <p className="text-gray-400 text-sm mt-2">上传合同后查看执行日志</p>
                  </div>
                )}
              </div>
            )}
          </div>
          
          {/* Generate Report Button */}
          {currentTaskId && flowState?.status === 'completed' && (
            <div className="px-6 py-4 border-t border-gray-200">
              <button
                onClick={handleGenerateReport}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
              >
                <FileText className="w-4 h-4" />
                生成智能报告
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default HomePage;