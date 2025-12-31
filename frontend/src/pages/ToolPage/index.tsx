import React, { useState, useEffect } from "react";
import { contractApi, type ToolInfo } from "../../api/client";
import {
  Wrench,
  X,
  Loader2,
  AlertCircle,
  Code,
  FileText,
  Tag,
} from "lucide-react";

const ToolPage: React.FC = () => {
  const [tools, setTools] = useState<ToolInfo[]>([]);
  const [selectedTool, setSelectedTool] = useState<ToolInfo | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // 加载工具列表
  useEffect(() => {
    const fetchTools = async () => {
      try {
        setLoading(true);
        setError(null);
        const toolsList = await contractApi.listTools();
        setTools(toolsList || []);
      } catch (err: any) {
        console.error("获取工具列表失败:", err);
        setError(
          err.response?.data?.detail || err.message || "获取工具列表失败"
        );
      } finally {
        setLoading(false);
      }
    };

    fetchTools();
  }, []);

  // 显示工具详细信息
  const handleToolClick = (toolName: string) => {
    // 从已加载的工具列表中查找
    const toolInfo = tools.find((tool) => tool.name === toolName);
    if (toolInfo) {
      setSelectedTool(toolInfo);
      setError(null);
    } else {
      setError(`未找到工具: ${toolName}`);
    }
  };

  // 关闭弹窗
  const handleCloseModal = () => {
    setSelectedTool(null);
    setError(null);
  };

  return (
    <div className="max-w-6xl mx-auto p-8">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg flex items-center justify-center">
            <Wrench className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">工具列表</h1>
            <p className="text-gray-500">查看所有可用的工具及其详细信息</p>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
            <span className="ml-3 text-gray-600">加载工具列表...</span>
          </div>
        ) : tools.length === 0 ? (
          <div className="text-center py-12">
            <Wrench className="mx-auto mb-4 w-12 h-12 text-gray-300" />
            <p className="text-gray-500">暂无可用工具</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {tools.map((tool) => (
              <button
                key={tool.name}
                onClick={() => handleToolClick(tool.name)}
                className="p-4 bg-gray-50 hover:bg-blue-50 border border-gray-200 hover:border-blue-300 rounded-lg transition-all text-left group"
              >
                <div className="flex items-center gap-3 mb-2">
                  <Code className="w-5 h-5 text-gray-400 group-hover:text-blue-600 transition-colors" />
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                      {tool.display_name || tool.name}
                    </h3>
                    {tool.category && (
                      <span className="inline-block mt-1 px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">
                        {tool.category}
                      </span>
                    )}
                  </div>
                </div>
                <p className="text-sm text-gray-500 line-clamp-2">
                  {tool.description}
                </p>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* 工具详情弹窗 */}
      {selectedTool && (
        <div
          className="fixed inset-0 bg-opacity-0 backdrop-blur-[1px] flex items-center justify-center z-50 p-4"
          onClick={handleCloseModal}
        >
          <div
            className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* 弹窗头部 */}
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between bg-gradient-to-r from-blue-600 to-blue-700">
              <div className="flex items-center gap-3">
                <Wrench className="w-6 h-6 text-white" />
                <h2 className="text-xl font-bold text-white">
                  {selectedTool.display_name}
                </h2>
              </div>
              <button
                onClick={handleCloseModal}
                className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-blue-800 transition-colors text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* 弹窗内容 */}
            <div className="flex-1 overflow-y-auto p-6">
              <div className="space-y-6">
                {/* 基本信息 */}
                <section>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                    <FileText className="w-5 h-5 text-blue-600" />
                    基本信息
                  </h3>
                  <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                    <div>
                      <span className="text-sm font-medium text-gray-500">
                        工具名称
                      </span>
                      <p className="text-gray-900 font-mono mt-1">
                        {selectedTool.name}
                      </p>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-500">
                        显示名称
                      </span>
                      <p className="text-gray-900 mt-1">
                        {selectedTool.display_name}
                      </p>
                    </div>
                    {selectedTool.category && (
                      <div className="flex items-center gap-2">
                        <Tag className="w-4 h-4 text-gray-400" />
                        <span className="text-sm font-medium text-gray-500">
                          分类:
                        </span>
                        <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-sm">
                          {selectedTool.category}
                        </span>
                      </div>
                    )}
                    {selectedTool.version && (
                      <div>
                        <span className="text-sm font-medium text-gray-500">
                          版本
                        </span>
                        <p className="text-gray-900 mt-1">
                          v{selectedTool.version}
                        </p>
                      </div>
                    )}
                  </div>
                </section>

                {/* 描述 */}
                <section>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                    <FileText className="w-5 h-5 text-blue-600" />
                    描述
                  </h3>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-gray-700 leading-relaxed">
                      {selectedTool.description}
                    </p>
                  </div>
                </section>

                {/* 参数列表 */}
                {selectedTool.parameters &&
                  selectedTool.parameters.length > 0 && (
                    <section>
                      <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                        <Code className="w-5 h-5 text-blue-600" />
                        参数列表
                      </h3>
                      <div className="space-y-3">
                        {selectedTool.parameters.map((param, index) => (
                          <div
                            key={index}
                            className="bg-gray-50 rounded-lg p-4 border-l-4 border-blue-500"
                          >
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <code className="text-blue-600 font-semibold text-sm">
                                  {param.name}
                                </code>
                                <span className="px-2 py-0.5 bg-gray-200 text-gray-700 rounded text-xs font-mono">
                                  {param.type}
                                </span>
                                {param.required && (
                                  <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded text-xs font-medium">
                                    必需
                                  </span>
                                )}
                                {!param.required && (
                                  <span className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs font-medium">
                                    可选
                                  </span>
                                )}
                              </div>
                            </div>
                            <p className="text-sm text-gray-700 mt-2">
                              {param.description}
                            </p>
                            {param.default !== undefined && (
                              <div className="mt-2 text-xs text-gray-500">
                                <span className="font-medium">默认值: </span>
                                <code className="bg-gray-200 px-1.5 py-0.5 rounded">
                                  {typeof param.default === "object"
                                    ? JSON.stringify(param.default)
                                    : String(param.default)}
                                </code>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </section>
                  )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ToolPage;
