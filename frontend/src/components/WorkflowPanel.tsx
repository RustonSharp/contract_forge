import React, { useState, useEffect, useCallback } from "react";
import { X, CheckCircle2, Circle, Loader2, AlertCircle } from "lucide-react";
import { contractApi } from "../api/client";
import type { WorkflowDefinitionResponse, WorkflowProgressResponse } from "../api/client";

interface WorkflowPanelProps {
  workflowId: string | null;
  configFile?: string;
  onClose: () => void;
}

const WorkflowPanel: React.FC<WorkflowPanelProps> = ({
  workflowId,
  configFile = "合同处理自动化流程.json",
  onClose,
}) => {
  const [definition, setDefinition] = useState<WorkflowDefinitionResponse | null>(null);
  const [progress, setProgress] = useState<WorkflowProgressResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 获取工作流定义
  const fetchDefinition = useCallback(async () => {
    try {
      const data = await contractApi.getWorkflowDefinition(configFile);
      setDefinition(data);
    } catch (err: any) {
      setError(`获取工作流定义失败: ${err.message}`);
      console.error("获取工作流定义失败:", err);
    }
  }, [configFile]);

  // 获取工作流进度
  const fetchProgress = useCallback(async () => {
    if (!workflowId) return;

    try {
      const data = await contractApi.getWorkflowProgress(workflowId);
      setProgress(data);
      setError(null);
    } catch (err: any) {
      setError(`获取工作流进度失败: ${err.message}`);
      console.error("获取工作流进度失败:", err);
    }
  }, [workflowId]);

  // 初始加载
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchDefinition(), workflowId ? fetchProgress() : Promise.resolve()]);
      setLoading(false);
    };
    loadData();
  }, [workflowId, fetchDefinition, fetchProgress]);

  // 轮询进度
  useEffect(() => {
    if (!workflowId) return;

    // 如果已完成或失败，停止轮询
    if (progress?.status === "completed" || progress?.status === "failed") {
      return;
    }

    // 每 2 秒轮询一次
    const interval = setInterval(() => {
      fetchProgress();
    }, 2000);

    return () => clearInterval(interval);
  }, [workflowId, progress?.status, fetchProgress]);

  // 获取节点状态
  const getNodeStatus = (nodeId: string, nodeName: string) => {
    if (!progress) return "pending";

    // 检查是否在已完成节点列表中（支持 ID 或名称匹配）
    const isCompleted = progress.completed_nodes.some(
      (completed) => completed === nodeId || completed === nodeName
    );
    if (isCompleted) {
      return "completed";
    }

    // 检查是否是当前执行节点（支持 ID 或名称匹配）
    if (progress.current_node === nodeId || progress.current_node === nodeName) {
      return "running";
    }

    // 如果工作流已完成或失败，所有未完成的节点都标记为 pending
    if (progress.status === "completed" || progress.status === "failed") {
      return "pending";
    }

    return "pending";
  };

  // 获取状态图标
  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="w-5 h-5 text-green-500" />;
      case "running":
        return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
      case "failed":
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Circle className="w-5 h-5 text-gray-400" />;
    }
  };

  // 获取状态颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-50 border-green-200";
      case "running":
        return "bg-blue-50 border-blue-200";
      case "failed":
        return "bg-red-50 border-red-200";
      default:
        return "bg-gray-50 border-gray-200";
    }
  };

  // 根据连接关系排序节点（简单的拓扑排序）
  const getOrderedNodes = () => {
    if (!definition) return [];

    const nodes = [...definition.nodes];
    const connections = definition.connections;

    // 创建节点名称到节点的映射
    const nodeMapByName = new Map<string, typeof nodes[0]>();
    nodes.forEach((node) => {
      nodeMapByName.set(node.name, node);
    });

    // 找到起始节点（通常是 webhook）
    const startNode = nodes.find((node) => 
      node.type.includes("webhook") || node.name.includes("触发")
    );

    if (!startNode) return nodes;

    // 简单的 BFS 排序
    const ordered: typeof nodes = [];
    const visited = new Set<string>();
    const queue: string[] = [startNode.name]; // 使用节点名称作为队列元素

    while (queue.length > 0) {
      const currentNodeName = queue.shift()!;
      if (visited.has(currentNodeName)) continue;

      const currentNode = nodeMapByName.get(currentNodeName);
      if (currentNode) {
        ordered.push(currentNode);
        visited.add(currentNodeName);

        // 找到连接的节点
        const nodeConnections = connections[currentNodeName];
        if (nodeConnections?.main) {
          nodeConnections.main.forEach((outputs: any[]) => {
            outputs.forEach((output: any) => {
              const nextNodeName = output.node;
              if (nextNodeName && !visited.has(nextNodeName) && nodeMapByName.has(nextNodeName)) {
                queue.push(nextNodeName);
              }
            });
          });
        }
      }
    }

    // 添加未访问的节点
    nodes.forEach((node) => {
      if (!visited.has(node.name)) {
        ordered.push(node);
      }
    });

    return ordered;
  };

  const orderedNodes = getOrderedNodes();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-end">
      {/* 背景遮罩 */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />

      {/* 面板 */}
      <div className="relative w-full max-w-2xl h-full bg-white shadow-xl flex flex-col animate-slide-in-right">
        {/* 头部 */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              {definition?.name || "工作流执行进度"}
            </h2>
            {progress && (
              <p className="text-sm text-gray-500 mt-1">
                状态: <span className="font-medium">{progress.status}</span>
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* 内容区域 */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
                <p className="text-red-600">{error}</p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {/* 工作流进度 */}
              {orderedNodes.map((node, index) => {
                const nodeStatus = getNodeStatus(node.id, node.name);
                return (
                  <div
                    key={node.id}
                    className={`border-2 rounded-lg p-4 transition-all ${getStatusColor(
                      nodeStatus
                    )}`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 mt-0.5">
                        {getStatusIcon(nodeStatus)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-medium text-gray-900">{node.name}</h3>
                          <span className="text-xs text-gray-500">#{index + 1}</span>
                        </div>
                        {node.notes && (
                          <p className="text-sm text-gray-600 mb-2">{node.notes}</p>
                        )}
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                          <span className="px-2 py-1 bg-white rounded border border-gray-200">
                            {node.type.replace("n8n-nodes-base.", "")}
                          </span>
                          <span className="capitalize">{nodeStatus}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}

              {/* 进度信息 */}
              {progress && (
                <div className="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <h4 className="font-medium text-gray-900 mb-2">执行信息</h4>
                  <div className="space-y-1 text-sm text-gray-600">
                    {progress.message && (
                      <p>
                        <span className="font-medium">消息:</span> {progress.message}
                      </p>
                    )}
                    {progress.file_path && (
                      <p>
                        <span className="font-medium">文件:</span> {progress.file_path}
                      </p>
                    )}
                    {progress.error && (
                      <p className="text-red-600">
                        <span className="font-medium">错误:</span> {progress.error}
                      </p>
                    )}
                    <p>
                      <span className="font-medium">创建时间:</span>{" "}
                      {new Date(progress.created_at).toLocaleString("zh-CN")}
                    </p>
                    <p>
                      <span className="font-medium">更新时间:</span>{" "}
                      {new Date(progress.updated_at).toLocaleString("zh-CN")}
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <style>{`
        @keyframes slide-in-right {
          from {
            transform: translateX(100%);
          }
          to {
            transform: translateX(0);
          }
        }
        .animate-slide-in-right {
          animation: slide-in-right 0.3s ease-out;
        }
      `}</style>
    </div>
  );
};

export default WorkflowPanel;

