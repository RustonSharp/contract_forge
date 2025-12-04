import { Card, List, Progress, Tag, Button } from 'antd'
import { EyeOutlined, DownloadOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useContractStore } from '@/store/contractStore'
import { Contract, ContractStatus, RiskLevel } from '@/types/contract'
import dayjs from 'dayjs'
import './styles.css'

// 状态标签
const statusConfig: Record<ContractStatus, { color: string; text: string }> = {
  pending: { color: 'default', text: '等待中' },
  processing: { color: 'processing', text: '处理中' },
  completed: { color: 'success', text: '已完成' },
  failed: { color: 'error', text: '失败' },
}

// 风险等级标签
const riskConfig: Record<RiskLevel, { color: string; text: string }> = {
  low: { color: 'success', text: '低风险' },
  medium: { color: 'warning', text: '中风险' },
  high: { color: 'error', text: '高风险' },
}

interface Props {
  filter?: ContractStatus
}

export default function ContractList({ filter }: Props) {
  const navigate = useNavigate()
  const contracts = useContractStore((state) => state.contracts)
  
  // 过滤合同
  const filteredContracts = filter
    ? contracts.filter((c) => c.status === filter)
    : contracts
  
  return (
    <Card title={`合同列表 (${filteredContracts.length})`}>
      <List
        dataSource={filteredContracts}
        renderItem={(contract: Contract) => (
          <List.Item
            key={contract.id}
            actions={[
              <Button
                type="link"
                icon={<EyeOutlined />}
                onClick={() => navigate(`/contract/${contract.id}`)}
              >
                查看详情
              </Button>,
            ]}
          >
            <List.Item.Meta
              title={
                <div className="contract-title">
                  <span>{contract.filename}</span>
                  <div className="contract-tags">
                    <Tag color={statusConfig[contract.status].color}>
                      {statusConfig[contract.status].text}
                    </Tag>
                    {contract.riskLevel && (
                      <Tag color={riskConfig[contract.riskLevel].color}>
                        {riskConfig[contract.riskLevel].text}
                      </Tag>
                    )}
                  </div>
                </div>
              }
              description={
                <div className="contract-info">
                  <div>
                    上传时间：{dayjs(contract.uploadTime).format('YYYY-MM-DD HH:mm:ss')}
                  </div>
                  <div>
                    上传人：{contract.uploadedBy}
                  </div>
                  {contract.status === 'processing' && (
                    <div className="progress-section">
                      <Progress
                        percent={contract.progress}
                        status="active"
                        size="small"
                      />
                      <span className="progress-text">{contract.currentStep}</span>
                    </div>
                  )}
                </div>
              }
            />
          </List.Item>
        )}
      />
    </Card>
  )
}

