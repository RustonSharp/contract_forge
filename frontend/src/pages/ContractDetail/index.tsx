import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Card, Descriptions, Tag, Progress, Timeline, Spin } from 'antd'
import { useContractStore } from '@/store/contractStore'
import { useContractProgress } from '@/hooks/useWebSocket'
import dayjs from 'dayjs'

export default function ContractDetail() {
  const { id } = useParams<{ id: string }>()
  const contract = useContractStore((state) =>
    state.contracts.find((c) => c.id === id)
  )
  const updateContract = useContractStore((state) => state.updateContract)
  
  // 订阅实时进度更新
  useContractProgress(
    id || '',
    (data) => {
      // 进度更新
      updateContract(id!, {
        progress: data.progress,
        currentStep: data.message,
      })
    },
    (data) => {
      // 完成
      updateContract(id!, {
        status: 'completed',
        progress: 100,
        completedTime: new Date().toISOString(),
        riskLevel: data.risk_level,
        reportUrl: data.report_url,
      })
    }
  )
  
  if (!contract) {
    return (
      <Card>
        <Spin tip="加载中..." />
      </Card>
    )
  }
  
  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>合同详情</h1>
      
      <Card title="基本信息" style={{ marginBottom: 16 }}>
        <Descriptions column={2}>
          <Descriptions.Item label="文件名">
            {contract.filename}
          </Descriptions.Item>
          <Descriptions.Item label="文件格式">
            {contract.fileFormat.toUpperCase()}
          </Descriptions.Item>
          <Descriptions.Item label="文件大小">
            {(contract.fileSize / 1024 / 1024).toFixed(2)} MB
          </Descriptions.Item>
          <Descriptions.Item label="上传时间">
            {dayjs(contract.uploadTime).format('YYYY-MM-DD HH:mm:ss')}
          </Descriptions.Item>
          <Descriptions.Item label="上传人">
            {contract.uploadedBy}
          </Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={contract.status === 'completed' ? 'success' : 'processing'}>
              {contract.status === 'completed' ? '已完成' : '处理中'}
            </Tag>
          </Descriptions.Item>
        </Descriptions>
      </Card>
      
      {contract.status === 'processing' && (
        <Card title="处理进度" style={{ marginBottom: 16 }}>
          <Progress
            percent={contract.progress}
            status="active"
            strokeColor={{ '0%': '#108ee9', '100%': '#87d068' }}
          />
          <p style={{ marginTop: 16, color: '#666' }}>
            当前步骤：{contract.currentStep || '初始化...'}
          </p>
        </Card>
      )}
      
      {contract.riskLevel && (
        <Card title="风险评估" style={{ marginBottom: 16 }}>
          <Descriptions column={1}>
            <Descriptions.Item label="风险等级">
              <Tag color={
                contract.riskLevel === 'low' ? 'success' :
                contract.riskLevel === 'medium' ? 'warning' : 'error'
              }>
                {contract.riskLevel === 'low' ? '低风险' :
                 contract.riskLevel === 'medium' ? '中风险' : '高风险'}
              </Tag>
            </Descriptions.Item>
          </Descriptions>
        </Card>
      )}
      
      <Card title="执行日志">
        <Timeline
          items={[
            {
              children: `${dayjs(contract.uploadTime).format('HH:mm:ss')} - 文件上传成功`,
              color: 'green',
            },
            {
              children: `处理中...`,
              color: contract.status === 'completed' ? 'green' : 'blue',
            },
            contract.completedTime && {
              children: `${dayjs(contract.completedTime).format('HH:mm:ss')} - 处理完成`,
              color: 'green',
            },
          ].filter(Boolean) as any}
        />
      </Card>
    </div>
  )
}

