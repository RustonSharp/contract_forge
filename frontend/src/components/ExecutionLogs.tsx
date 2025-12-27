import React, { useState, useEffect } from 'react';
import { Clock, CheckCircle2, XCircle, Info, Search, Download } from 'lucide-react';
import { contractApi } from '../api/client';

interface LogEntry {
  step?: string;
  message: string;
  timestamp: string;
  level?: 'info' | 'success' | 'error' | 'warning';
}

interface ExecutionLogsProps {
  taskId: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

const ExecutionLogs: React.FC<ExecutionLogsProps> = ({
  taskId,
  autoRefresh = true,
  refreshInterval = 2000
}) => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const fetchLogs = async () => {
    if (!taskId) return;
    
    setLoading(true);
    try {
      const response = await contractApi.getTaskLogs(taskId);
      if (response.status === 'success' && response.data) {
        setLogs(response.data.logs || []);
      }
    } catch (error) {
      console.error('Failed to fetch logs:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    
    if (autoRefresh) {
      const interval = setInterval(fetchLogs, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [taskId, autoRefresh, refreshInterval]);

  const filteredLogs = logs.filter(log =>
    log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
    log.step?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getLogIcon = (log: LogEntry) => {
    if (log.level === 'error') {
      return <XCircle className="w-4 h-4 text-red-600" />;
    } else if (log.level === 'success') {
      return <CheckCircle2 className="w-4 h-4 text-green-600" />;
    }
    return <Info className="w-4 h-4 text-blue-600" />;
  };

  const formatTime = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    } catch {
      return timestamp;
    }
  };

  const exportLogs = () => {
    const logText = filteredLogs.map(log =>
      `[${formatTime(log.timestamp)}] ${log.step || 'SYSTEM'}: ${log.message}`
    ).join('\n');
    
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `logs-${taskId}-${new Date().toISOString()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="h-full flex flex-col bg-white rounded-lg border border-gray-200">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">执行日志</h3>
        <div className="flex items-center gap-2">
          <button
            onClick={exportLogs}
            className="px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            导出
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="px-6 py-3 border-b border-gray-200">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="搜索日志..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Logs List */}
      <div className="flex-1 overflow-y-auto p-6">
        {loading && logs.length === 0 ? (
          <div className="text-center py-8 text-gray-500">加载中...</div>
        ) : filteredLogs.length === 0 ? (
          <div className="text-center py-8 text-gray-500">暂无日志</div>
        ) : (
          <div className="space-y-3">
            {filteredLogs.map((log, index) => (
              <div
                key={index}
                className="flex gap-3 p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
              >
                <div className="flex-shrink-0 mt-0.5">
                  {getLogIcon(log)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      {log.step && (
                        <span className="text-sm font-medium text-gray-900 mr-2">
                          [{log.step}]
                        </span>
                      )}
                      <span className="text-sm text-gray-700">{log.message}</span>
                    </div>
                    <div className="flex items-center gap-1 text-xs text-gray-500 flex-shrink-0">
                      <Clock className="w-3 h-3" />
                      {formatTime(log.timestamp)}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ExecutionLogs;

