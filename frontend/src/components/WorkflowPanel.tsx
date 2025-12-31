import React, { useState, useEffect, useCallback } from "react";
import { X, CheckCircle2, Circle, Loader2, AlertCircle } from "lucide-react";
import { contractApi } from "../api/client";
import type {
  WorkflowDefinitionResponse,
  WorkflowProgressResponse,
} from "../api/client";

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
  const [definition, setDefinition] =
    useState<WorkflowDefinitionResponse | null>(null);
  const [progress, setProgress] = useState<WorkflowProgressResponse | null>(
    null
  );
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
    if (!workflowId) return false; // 返回 false 表示应该停止轮询

    try {
      const data = await contractApi.getWorkflowProgress(workflowId);
      setProgress(data);
      setError(null);
      return true; // 返回 true 表示可以继续轮询
    } catch (err: any) {
      // 如果是 404 错误，说明工作流记录不存在，停止轮询但不显示错误（允许查看定义）
      if (err.response?.status === 404) {
        console.warn("工作流记录不存在:", workflowId, "- 可能尚未开始执行");
        // 不设置错误，允许用户查看工作流定义
        return false; // 返回 false 表示应该停止轮询
      }
      // 其他错误，显示错误信息但继续尝试
      setError(`获取工作流进度失败: ${err.message}`);
      console.error("获取工作流进度失败:", err);
      return true; // 继续轮询，可能只是临时错误
    }
  }, [workflowId]);

  // 初始加载
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([
        fetchDefinition(),
        workflowId ? fetchProgress() : Promise.resolve(),
      ]);
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

    // 如果进度为 null 且没有错误，可能是 404（记录不存在），停止轮询
    if (!progress && !error) {
      // 等待一次轮询后再决定
    }

    // 每 2 秒轮询一次
    const interval = setInterval(async () => {
      const shouldContinue = await fetchProgress();
      // 如果 fetchProgress 返回 false，说明应该停止轮询（如 404 错误）
      if (!shouldContinue) {
        clearInterval(interval);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [workflowId, progress?.status, error, fetchProgress]);

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
    if (
      progress.current_node === nodeId ||
      progress.current_node === nodeName
    ) {
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

  // 节点树形结构（支持分支）
  type WorkflowNode = WorkflowDefinitionResponse["nodes"][0];
  interface TreeNode {
    node: WorkflowNode;
    children?: TreeNode[]; // 子节点（单一路径）
    branches?: TreeNode[][]; // 分支（多个路径）
    isBranchNode?: boolean; // 是否是分支节点
    mergeNode?: TreeNode; // 合并节点（如果分支合并）
  }

  // 检查分支是否合并（基于连接关系）
  const checkBranchMerge = (
    branches: TreeNode[][],
    connections: Record<string, any>,
    nodeMapByName: Map<string, WorkflowNode>
  ): TreeNode | null => {
    if (!branches || branches.length < 2 || !definition) return null;

    // 获取所有分支的最后一个节点名称
    const lastNodeNames = branches
      .map((branch) => {
        if (branch.length === 0) return null;
        const lastNode = branch[branch.length - 1];
        return lastNode.node.name;
      })
      .filter(Boolean) as string[];

    if (lastNodeNames.length < 2) return null;

    // 检查这些节点的连接关系，看是否都指向同一个节点
    // 收集每个分支的最后一个节点指向的所有有效目标节点
    const branchTargets: string[][] = [];
    lastNodeNames.forEach((nodeName) => {
      const nodeConnections = connections[nodeName];
      const targets: string[] = [];
      if (nodeConnections?.main) {
        nodeConnections.main.forEach((outputs: any[]) => {
          outputs.forEach((output: any) => {
            const target = output.node;
            if (
              target &&
              !target.includes("更新状态") &&
              !target.includes("更新工作流状态") &&
              nodeMapByName.has(target) // 确保目标节点存在于节点映射中
            ) {
              targets.push(target);
            }
          });
        });
      }
      branchTargets.push(targets);
    });

    // 只有当所有分支的最后一个节点都指向同一个有效节点时，才认为是合并
    // 1. 所有分支都必须有至少一个目标节点
    if (branchTargets.some((targets) => targets.length === 0)) {
      return null; // 有些分支没有指向任何有效节点，不是合并
    }

    // 2. 所有分支的目标节点集合必须完全相同，且只有一个目标节点
    const firstBranchTargets = new Set(branchTargets[0]);
    const allTargetsSame = branchTargets.every((targets) => {
      if (targets.length !== firstBranchTargets.size) return false;
      return targets.every((target) => firstBranchTargets.has(target));
    });

    // 3. 如果所有分支都指向同一个节点（且只有一个目标节点），说明合并了
    if (allTargetsSame && firstBranchTargets.size === 1) {
      const mergeNodeName = Array.from(firstBranchTargets)[0];
      const mergeNode = nodeMapByName.get(mergeNodeName);
      if (mergeNode) {
        return {
          node: mergeNode,
          children: undefined,
          branches: undefined,
        };
      }
    }

    return null;
  };

  // 根据连接关系构建节点树（支持分支）
  const buildNodeTree = (): TreeNode | null => {
    if (!definition) return null;

    const nodes = [...definition.nodes];
    const connections = definition.connections;

    // 创建节点名称到节点的映射
    const nodeMapByName = new Map<string, (typeof nodes)[0]>();
    nodes.forEach((node) => {
      nodeMapByName.set(node.name, node);
    });

    // 找到起始节点（通常是 webhook）
    const startNode = nodes.find(
      (node) => node.type.includes("webhook") || node.name.includes("触发")
    );

    if (!startNode) {
      // 如果没有起始节点，返回第一个节点作为根节点
      const firstNode = nodes[0];
      return firstNode ? { node: firstNode } : null;
    }

    // 使用路径跟踪来防止循环引用
    const buildTree = (
      nodeName: string,
      path: string[] = []
    ): TreeNode | null => {
      // 防止循环引用（检查当前路径）
      if (path.includes(nodeName)) {
        console.warn(`检测到循环引用: ${nodeName}，路径: ${path.join(" -> ")}`);
        return null;
      }
      const currentPath = [...path, nodeName];

      const currentNode = nodeMapByName.get(nodeName);
      if (!currentNode) {
        console.warn(`节点不存在: ${nodeName}`);
        return null;
      }

      const nodeConnections = connections[nodeName];
      if (!nodeConnections?.main || nodeConnections.main.length === 0) {
        // 叶子节点
        return { node: currentNode };
      }

      // 检查是否有多个分支（Switch 节点）
      const hasMultipleBranches = nodeConnections.main.length > 1;

      if (hasMultipleBranches) {
        // 分支节点：构建所有分支
        const branches: TreeNode[][] = [];
        nodeConnections.main.forEach((outputs: any[], branchIdx: number) => {
          const branch: TreeNode[] = [];
          outputs.forEach((output: any) => {
            const nextNodeName = output.node;
            if (nextNodeName && nodeMapByName.has(nextNodeName)) {
              const childTree = buildTree(nextNodeName, currentPath);
              if (childTree) {
                branch.push(childTree);
              }
            } else if (nextNodeName) {
              console.warn(`分支 ${branchIdx} 中的节点不存在: ${nextNodeName}`);
            }
          });
          if (branch.length > 0) {
            branches.push(branch);
          }
        });

        // 检查分支是否合并
        const mergeNodeInfo =
          branches.length > 0
            ? checkBranchMerge(branches, connections, nodeMapByName)
            : null;

        // 如果检测到合并，构建合并节点的完整树
        let mergeNode: TreeNode | undefined = undefined;
        if (mergeNodeInfo && mergeNodeInfo.node.name) {
          const mergeNodeName = mergeNodeInfo.node.name;
          // 检查是否已经在当前路径中（防止循环）
          if (!currentPath.includes(mergeNodeName)) {
            const mergeTree = buildTree(mergeNodeName, currentPath);
            if (mergeTree) {
              mergeNode = mergeTree;
            }
          }
        }

        return {
          node: currentNode,
          branches: branches.length > 0 ? branches : undefined,
          isBranchNode: true,
          mergeNode: mergeNode,
        };
      } else {
        // 单一路径：构建子节点
        const children: TreeNode[] = [];
        nodeConnections.main.forEach((outputs: any[]) => {
          outputs.forEach((output: any) => {
            const nextNodeName = output.node;
            if (nextNodeName && nodeMapByName.has(nextNodeName)) {
              const childTree = buildTree(nextNodeName, currentPath);
              if (childTree) {
                children.push(childTree);
              }
            } else if (nextNodeName) {
              console.warn(`子节点不存在: ${nextNodeName}`);
            }
          });
        });

        return {
          node: currentNode,
          children: children.length > 0 ? children : undefined,
        };
      }
    };

    return buildTree(startNode.name);
  };

  const nodeTree = buildNodeTree();

  // 调试：打印树结构
  useEffect(() => {
    if (nodeTree) {
      console.log("工作流树结构:", JSON.stringify(nodeTree, null, 2));
    } else {
      console.warn("无法构建工作流树");
    }
  }, [nodeTree]);

  // 渲染节点树
  const renderNode = (
    treeNode: TreeNode,
    level: number = 0,
    isInBranch: boolean = false
  ): React.ReactNode => {
    const { node, children, branches, isBranchNode, mergeNode } = treeNode;
    const nodeStatus = getNodeStatus(node.id, node.name);
    const hasChildren =
      (children && children.length > 0) || (branches && branches.length > 0);

    return (
      <div key={node.id} className="relative w-full">
        {/* 节点卡片 */}
        <div
          className={`border-2 rounded-lg p-4 transition-all ${getStatusColor(
            nodeStatus
          )} ${isInBranch ? "" : ""}`}
        >
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 mt-0.5">
              {getStatusIcon(nodeStatus)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="font-medium text-gray-900">{node.name}</h3>
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

        {/* 箭头连接线 - 只在有子节点时显示 */}
        {hasChildren && !isBranchNode && (
          <div className="flex justify-center my-3">
            <div className="relative flex flex-col items-center">
              <div className="w-0.5 h-8 bg-gray-300"></div>
              <svg
                className="w-6 h-6 text-gray-400 -mt-1"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </div>
          </div>
        )}

        {/* 子节点或分支 */}
        {isBranchNode && branches ? (
          // 分支显示：使用Grid布局，每个分支占50%宽度
          <div className="mt-4">
            {/* 分支箭头 - 从节点到分支 */}
            <div className="flex justify-center my-3">
              <div className="relative flex flex-col items-center">
                <div className="w-0.5 h-8 bg-gray-300"></div>
                <svg
                  className="w-6 h-6 text-gray-400 -mt-1"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
              </div>
            </div>

            {/* 分支容器 - 使用Grid并排显示 */}
            <div
              className={`grid gap-4 ${
                branches.length === 2
                  ? "grid-cols-2"
                  : branches.length === 3
                  ? "grid-cols-3"
                  : "grid-cols-2"
              }`}
            >
              {branches.map((branch, branchIndex) => (
                <div
                  key={branchIndex}
                  className="relative flex flex-col items-center"
                >
                  {/* 分支标签 */}
                  <div className="w-full mb-3">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-px bg-gray-300"></div>
                      <span className="text-xs font-medium text-blue-600 px-3 py-1 bg-blue-50 rounded-full border border-blue-200 whitespace-nowrap">
                        分支 {branchIndex + 1}
                      </span>
                      <div className="flex-1 h-px bg-gray-300"></div>
                    </div>
                  </div>

                  {/* 分支节点 - 垂直排列 */}
                  <div className="w-full space-y-4">
                    {branch.map((childNode, childIndex) => (
                      <div key={childNode.node.id} className="relative w-full">
                        {renderNode(childNode, level + 1, true)}
                        {/* 分支内的箭头 */}
                        {childIndex < branch.length - 1 && (
                          <div className="flex justify-center my-3">
                            <div className="relative flex flex-col items-center">
                              <div className="w-0.5 h-8 bg-gray-300"></div>
                              <svg
                                className="w-6 h-6 text-gray-400 -mt-1"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M19 9l-7 7-7-7"
                                />
                              </svg>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* 合并节点 - 如果分支合并 */}
            {mergeNode && (
              <>
                {/* 合并箭头 - 从分支到合并点 */}
                <div className="flex justify-center my-3">
                  <div className="relative flex flex-col items-center">
                    <div className="w-0.5 h-8 bg-gray-300"></div>
                    <svg
                      className="w-6 h-6 text-gray-400 -mt-1"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 9l-7 7-7-7"
                      />
                    </svg>
                  </div>
                </div>
                {/* 渲染合并节点 */}
                {renderNode(mergeNode, level, false)}
              </>
            )}
          </div>
        ) : children ? (
          // 单一路径：垂直显示
          <div className="mt-4 space-y-4">
            {children.map((childNode, childIndex) => (
              <div key={childNode.node.id} className="relative">
                {renderNode(childNode, level + 1, isInBranch)}
                {/* 箭头 */}
                {childIndex < children.length - 1 && (
                  <div className="flex justify-center my-3">
                    <div className="relative flex flex-col items-center">
                      <div className="w-0.5 h-8 bg-gray-300"></div>
                      <svg
                        className="w-6 h-6 text-gray-400 -mt-1"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M19 9l-7 7-7-7"
                        />
                      </svg>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : null}
      </div>
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-end">
      {/* 背景遮罩 - 毛玻璃效果 */}
      <div
        className="absolute inset-0 backdrop-blur-sm bg-black/20 transition-opacity"
        onClick={onClose}
      />

      {/* 面板 - 更宽的宽度 */}
      <div className="relative w-full max-w-4xl h-full bg-white shadow-xl flex flex-col animate-slide-in-right">
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
              {/* 工作流进度 - 树形结构 */}
              {nodeTree ? (
                <div className="space-y-4">{renderNode(nodeTree)}</div>
              ) : (
                <div className="text-center text-gray-500 py-8">
                  无法构建工作流树结构
                  {definition && (
                    <div className="mt-4 text-xs text-gray-400">
                      节点数: {definition.nodes.length}, 连接数:{" "}
                      {Object.keys(definition.connections).length}
                    </div>
                  )}
                </div>
              )}

              {/* 进度信息 */}
              {progress && (
                <div className="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <h4 className="font-medium text-gray-900 mb-2">执行信息</h4>
                  <div className="space-y-1 text-sm text-gray-600">
                    {progress.message && (
                      <p>
                        <span className="font-medium">消息:</span>{" "}
                        {progress.message}
                      </p>
                    )}
                    {progress.file_path && (
                      <p>
                        <span className="font-medium">文件:</span>{" "}
                        {progress.file_path}
                      </p>
                    )}
                    {progress.error && (
                      <p className="text-red-600">
                        <span className="font-medium">错误:</span>{" "}
                        {progress.error}
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
