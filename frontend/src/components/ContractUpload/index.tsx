import { useState } from 'react'
import { Upload, Button, Card, message, Select, InputNumber } from 'antd'
import { UploadOutlined, InboxOutlined } from '@ant-design/icons'
import { useDropzone } from 'react-dropzone'
import { contractService } from '@/services/contractService'
import { useContractStore } from '@/store/contractStore'
import { useContractTypes } from '@/hooks/useContractTypes'
import './styles.css'

const { Dragger } = Upload

export default function ContractUpload() {
  const [uploading, setUploading] = useState(false)
  const [contractType, setContractType] = useState<string>()
  const [amount, setAmount] = useState<number>()
  const addContract = useContractStore((state) => state.addContract)
  
  // 从后端获取合同类型
  const { types, loading: typesLoading } = useContractTypes()
  
  const handleUpload = async (file: File) => {
    try {
      setUploading(true)
      
      // 调用上传 API
      const result = await contractService.uploadContract(file, {
        contractType,
        amount,
      })
      
      // 添加到状态
      addContract({
        id: result.execution_id,
        filename: file.name,
        fileFormat: file.name.split('.').pop() || '',
        fileSize: file.size,
        status: 'processing',
        progress: 0,
        uploadTime: new Date().toISOString(),
        uploadedBy: '当前用户',
      })
      
      message.success(`${file.name} 上传成功！`)
      message.info(`使用工作流：${result.workflow_used}`)
    } catch (error) {
      message.error(`${file.name} 上传失败`)
      console.error('Upload error:', error)
    } finally {
      setUploading(false)
    }
  }
  
  return (
    <Card title="上传合同">
      <div className="upload-options">
        <div className="option-item">
          <label>合同类型（可选）：</label>
          <Select
            style={{ width: 200 }}
            placeholder="选择合同类型"
            value={contractType}
            onChange={setContractType}
            loading={typesLoading}
            options={types
              .filter(type => type.is_active) // 只显示启用的类型
              .map(type => ({
                value: type.type_code,
                label: type.type_name,
              }))
            }
          />
        </div>
        
        <div className="option-item">
          <label>合同金额（可选）：</label>
          <InputNumber
            style={{ width: 200 }}
            placeholder="输入金额"
            value={amount}
            onChange={(value) => setAmount(value || undefined)}
            min={0}
            addonAfter="万元"
          />
        </div>
      </div>
      
      <Dragger
        name="file"
        multiple={false}
        accept=".pdf,.docx,.doc,.jpg,.jpeg,.png"
        beforeUpload={(file) => {
          handleUpload(file)
          return false // 阻止自动上传
        }}
        disabled={uploading}
      >
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">
          点击或拖拽文件到这里上传
        </p>
        <p className="ant-upload-hint">
          支持格式：PDF, DOCX, JPG, PNG（最大 50MB）
        </p>
      </Dragger>
      
      <div className="upload-tip">
        💡 提示：系统将根据合同信息自动选择最合适的处理流程
      </div>
    </Card>
  )
}

