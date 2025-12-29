import { Upload, FileText, X, Loader2 } from 'lucide-react';
import { useState, useEffect } from 'react';
import { contractApi, type FileInfo } from '../api/client';

interface Contract {
  id: string;
  name: string;
  size: string;
  uploadTime: string;
  fileInfo?: FileInfo;
}

interface FileUploadProps {
  onContractSelect?: (contract: Contract | null) => void;
  selectedContract?: Contract | null;
  onFileUpload?: (file: File) => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onContractSelect, selectedContract = null, onFileUpload }) => {
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(false);

  // 加载已上传的文件列表
  useEffect(() => {
    loadFiles();
  }, []);

  const loadFiles = async () => {
    setLoading(true);
    try {
      const response = await contractApi.listFiles();
      if (response.success && response.files) {
        const fileContracts: Contract[] = response.files.map((file: FileInfo) => ({
          id: file.file_path,
          name: file.file_name,
          size: `${(file.file_size / 1024).toFixed(2)} KB`,
          uploadTime: file.upload_date,
          fileInfo: file,
        }));
        setContracts(fileContracts);
        
        // 默认不选中任何合同（已移除自动选择第一个的逻辑）
      }
    } catch (error) {
      console.error('Failed to load files:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files);
    }
  };

  const handleFiles = async (files: FileList) => {
    setError(null);
    const file = files[0];
    
    // 验证文件格式
    const allowedTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'image/jpeg',
      'image/png'
    ];
    
    if (!allowedTypes.includes(file.type)) {
      setError('不支持的文件格式。请上传 PDF、DOC、DOCX 或图片文件（JPEG、PNG）。');
      return;
    }
    
    // 验证文件大小（最大10MB）
    const maxSizeInBytes = 10 * 1024 * 1024;
    if (file.size > maxSizeInBytes) {
      setError('文件大小超出限制。最大支持10MB。');
      return;
    }
    
    // 上传文件
    setUploading(true);
    try {
      const response = await contractApi.uploadFile(file);
      
      if (response.success && response.file_info) {
        const fileInfo = response.file_info;
    const newContract: Contract = {
          id: fileInfo.file_path,
          name: fileInfo.file_name,
          size: `${(fileInfo.file_size / 1024).toFixed(2)} KB`,
          uploadTime: fileInfo.upload_date,
          fileInfo: fileInfo,
    };
    
    setContracts(prev => [newContract, ...prev]);
        
    if (onContractSelect) {
      onContractSelect(newContract);
    }
    
        // 触发文件上传回调
    if (onFileUpload) {
      onFileUpload(file);
        }
      } else {
        setError(response.error || '文件上传失败');
      }
    } catch (error: any) {
      console.error('Upload error:', error);
      setError(error.response?.data?.detail || error.message || '文件上传失败');
    } finally {
      setUploading(false);
    }
  };

  const removeContract = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setContracts(prev => prev.filter(c => c.id !== id));
    if (selectedContract?.id === id) {
      if (onContractSelect) {
        onContractSelect(contracts.find(c => c.id !== id) || null);
      }
    }
  };

  return (
    <div className="h-full flex flex-col bg-white p-6">
      {/* Upload Area */}
      <div className="mb-6">
        <h2 className="mb-4 text-gray-900">上传合同文件</h2>
        <div
          className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
          } ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            id="file-upload"
            className="hidden"
            onChange={handleChange}
            accept=".pdf,.doc,.docx,.jpeg,.jpg,.png"
            disabled={uploading}
          />
          <label htmlFor="file-upload" className={`cursor-pointer ${uploading ? 'pointer-events-none' : ''}`}>
            {uploading ? (
              <>
                <Loader2 className="mx-auto mb-3 w-12 h-12 text-blue-500 animate-spin" />
                <p className="mb-1 text-gray-700">上传中...</p>
              </>
            ) : (
              <>
            <Upload className="mx-auto mb-3 w-12 h-12 text-gray-400" />
            <p className="mb-1 text-gray-700">点击上传或拖拽文件至此</p>
            <p className="text-gray-500">支持 PDF、DOC、DOCX 和图片格式（JPEG、PNG）</p>
              </>
            )}
          </label>
        </div>
        
        {/* Error Message */}
        {error && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg">
            {error}
          </div>
        )}
      </div>

      {/* Contract List */}
      <div className="flex-1 overflow-y-auto">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-gray-700">已上传合同</h3>
          <button
            onClick={loadFiles}
            disabled={loading}
            className="text-sm text-blue-600 hover:text-blue-700 disabled:text-gray-400"
          >
            {loading ? '加载中...' : '刷新'}
          </button>
        </div>
        {loading && contracts.length === 0 ? (
          <div className="text-center py-8">
            <Loader2 className="mx-auto mb-2 w-6 h-6 text-gray-400 animate-spin" />
            <p className="text-gray-400">加载中...</p>
          </div>
        ) : contracts.length === 0 ? (
          <p className="text-center py-8 text-gray-400">暂无上传合同</p>
        ) : (
          <div className="space-y-2">
            {contracts.map((contract) => (
              <div
                key={contract.id}
                onClick={() => {
                  if (onContractSelect) {
                    // 如果点击的是已选中的合同，则取消选中
                    if (selectedContract?.id === contract.id) {
                      onContractSelect(null);
                    } else {
                      onContractSelect(contract);
                    }
                  }
                }}
                className={`group p-4 rounded-lg border cursor-pointer transition-all ${
                  selectedContract?.id === contract.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-start gap-3">
                  <FileText className={`w-5 h-5 flex-shrink-0 mt-0.5 ${
                    selectedContract?.id === contract.id ? 'text-blue-600' : 'text-gray-400'
                  }`} />
                  <div className="flex-1 min-w-0">
                    <p className="truncate text-gray-900">{contract.name}</p>
                    <p className="text-gray-500 text-sm">{contract.size} · {contract.uploadTime}</p>
                  </div>
                  <button
                    onClick={(e) => removeContract(contract.id, e)}
                    className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-gray-200 rounded"
                  >
                    <X className="w-4 h-4 text-gray-500" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default FileUpload;
