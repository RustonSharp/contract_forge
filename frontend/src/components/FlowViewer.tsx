import React from 'react';
import { CheckCircle2, Circle, Loader2, AlertCircle, ArrowRight } from 'lucide-react';

interface FlowNode {
  id: string;
  label: string;
  status: string;
}

interface FlowEdge {
  from: string;
  to: string;
}

interface FlowViewerProps {
  nodes: FlowNode[];
  edges: FlowEdge[];
  currentStep?: string;
}

const FlowViewer: React.FC<FlowViewerProps> = ({ nodes, edges, currentStep }) => {
  const getNodeStatus = (nodeId: string) => {
    const node = nodes.find(n => n.id === nodeId);
    return node?.status || 'pending';
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-5 h-5 text-green-600" />;
      case 'running':
        return <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />;
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-600" />;
      default:
        return <Circle className="w-5 h-5 text-gray-300" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-50 border-green-200 text-green-900';
      case 'running':
        return 'bg-blue-50 border-blue-200 text-blue-900';
      case 'failed':
        return 'bg-red-50 border-red-200 text-red-900';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-600';
    }
  };

  // 构建节点映射
  const nodeMap = new Map(nodes.map(n => [n.id, n]));

  return (
    <div className="p-6 bg-white rounded-lg border border-gray-200">
      <h3 className="text-lg font-semibold mb-4 text-gray-900">流程执行图</h3>
      <div className="flex flex-col gap-4">
        {nodes.map((node, index) => {
          const status = getNodeStatus(node.id);
          const isCurrent = currentStep === node.id;
          const nextEdge = edges.find(e => e.from === node.id);
          
          return (
            <div key={node.id} className="flex items-center gap-4">
              {/* 节点 */}
              <div
                className={`flex items-center gap-3 px-4 py-3 rounded-lg border-2 transition-all ${
                  getStatusColor(status)
                } ${isCurrent ? 'ring-2 ring-blue-500 ring-offset-2' : ''}`}
              >
                {getStatusIcon(status)}
                <span className="font-medium">{node.label}</span>
              </div>

              {/* 箭头 */}
              {nextEdge && index < nodes.length - 1 && (
                <ArrowRight className="w-6 h-6 text-gray-400 flex-shrink-0" />
              )}
            </div>
          );
        })}
      </div>

      {/* 图例 */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="flex gap-4 text-sm">
          <div className="flex items-center gap-2">
            <Circle className="w-4 h-4 text-gray-300" />
            <span className="text-gray-600">待执行</span>
          </div>
          <div className="flex items-center gap-2">
            <Loader2 className="w-4 h-4 text-blue-600" />
            <span className="text-gray-600">执行中</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-green-600" />
            <span className="text-gray-600">已完成</span>
          </div>
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-600" />
            <span className="text-gray-600">失败</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FlowViewer;
