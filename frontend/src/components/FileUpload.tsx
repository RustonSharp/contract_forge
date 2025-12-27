import { Upload, FileText, X } from 'lucide-react';
import { useState } from 'react';

interface Contract {
  id: string;
  name: string;
  size: string;
  uploadTime: string;
}

interface FileUploadProps {
  onContractSelect?: (contract: Contract) => void;
  selectedContract?: Contract | null;
  onFileUpload?: (file: File) => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onContractSelect, selectedContract = null, onFileUpload }) => {
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  const handleFiles = (files: FileList) => {
    // 清除之前的错误信息
    setError(null);
    
    const file = files[0];
    
    // 验证文件格式 - 仅支持PDF、DOC、DOCX和JPEG、PNG图片格式
    const allowedTypes = [
      'application/pdf',                    // PDF
      'application/msword',                 // DOC
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // DOCX
      'image/jpeg',                         // JPEG
      'image/png'                           // PNG
    ];
    
    if (!allowedTypes.includes(file.type)) {
      setError('不支持的文件格式。请上传 PDF、DOC、DOCX 或图片文件（JPEG、PNG）。');
      return;
    }
    
    // 验证文件大小（例如：最大10MB）
    const maxSizeInBytes = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSizeInBytes) {
      setError('文件大小超出限制。最大支持10MB。');
      return;
    }
    
    const newContract: Contract = {
      id: Date.now().toString(),
      name: file.name,
      size: (file.size / 1024).toFixed(2) + ' KB',
      uploadTime: new Date().toLocaleString('zh-CN', { 
        month: '2-digit', 
        day: '2-digit', 
        hour: '2-digit', 
        minute: '2-digit' 
      })
    };
    
    setContracts(prev => [newContract, ...prev]);
    if (onContractSelect) {
      onContractSelect(newContract);
    }
    
    // 触发文件上传回调（用于自动开始审计）
    if (onFileUpload) {
      onFileUpload(file);
    }
  };

  const removeContract = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setContracts(prev => prev.filter(c => c.id !== id));
    if (selectedContract?.id === id) {
      if (onContractSelect) {
        onContractSelect(contracts[0] || null);
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
          }`}
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
            accept=".pdf,.doc,.docx,.jpeg,.jpg,.png" // 仅支持JPEG和PNG
          />
          <label htmlFor="file-upload" className="cursor-pointer">
            <Upload className="mx-auto mb-3 w-12 h-12 text-gray-400" />
            <p className="mb-1 text-gray-700">点击上传或拖拽文件至此</p>
            <p className="text-gray-500">支持 PDF、DOC、DOCX 和图片格式（JPEG、PNG）</p>
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
        <h3 className="mb-3 text-gray-700">已上传合同</h3>
        {contracts.length === 0 ? (
          <p className="text-center py-8 text-gray-400">暂无上传合同</p>
        ) : (
          <div className="space-y-2">
            {contracts.map((contract) => (
              <div
                key={contract.id}
                onClick={() => onContractSelect && onContractSelect(contract)}
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
                    <p className="text-gray-500">{contract.size} · {contract.uploadTime}</p>
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