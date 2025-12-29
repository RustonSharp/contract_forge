import React, { useState, useEffect } from 'react';
import { Clock, CheckCircle2, XCircle, Info, Search, Download, AlertTriangle } from 'lucide-react';
import { contractApi } from '../api/client';

interface LogEntry {
  step?: string;
  message: string;
  timestamp: string;
  level?: 'info' | 'success' | 'error' | 'warning' | 'warn';
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

  const levelColor = (level?: string) => {
    if (!level) return 'border-gray-200';
    const lv = level.toLowerCase();
    if (lv === 'error') return 'border-red-200 bg-red-50';
    if (lv === 'warning' || lv === 'warn') return 'border-amber-200 bg-amber-50';
    if (lv === 'success') return 'border-green-200 bg-green-50';
    if (lv === 'info') return 'border-blue-200 bg-blue-50';
    return 'border-gray-200';
  };

  const levelTag = (level?: string) => {
    if (!level) return null;
    const lv = level.toLowerCase();
    const base = "px-2 py-0.5 rounded-full text-xs font-medium";
    if (lv === 'error') return <span className={`${base} bg-red-100 text-red-700`}>错误</span>;
    if (lv === 'warning' || lv === 'warn') return <span className={`${base} bg-amber-100 text-amber-700`}>警告</span>;
    if (lv === 'success') return <span className={`${base} bg-green-100 text-green-700`}>成功</span>;
    return <span className={`${base} bg-blue-100 text-blue-700`}>信息</span>;
  };

  const getLogIcon = (log: LogEntry) => {
    if (log.level === 'error') {
      return <XCircle className="w-4 h-4 text-red-600" />;
    } else if (log.level === 'success') {
      return <CheckCircle2 className="w-4 h-4 text-green-600" />;
    } else if (log.level === 'warning' || log.level === 'warn') {
      return <AlertTriangle className="w-4 h-4 text-amber-500" />;
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
                className={`flex gap-3 p-3 rounded-lg border hover:bg-gray-50 transition-colors ${levelColor(log.level)}`}
              >
                <div className="flex-shrink-0 mt-0.5">
                  {getLogIcon(log)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        {log.step && (
                          <span className="text-xs font-medium text-gray-700">
                            [{log.step}]
                          </span>
                        )}
                        {levelTag(log.level)}
                      </div>
                      <span className="text-sm text-gray-800">{log.message}</span>
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

