import { Row, Col, Card, Tag, Spin } from 'antd'
import ContractUpload from '@/components/ContractUpload'
import ContractList from '@/components/ContractList'
import { useContractTypes } from '@/hooks/useContractTypes'

export default function Dashboard() {
  const { types, loading, error } = useContractTypes()
  
  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>工作台</h1>
      
      <Row gutter={[16, 16]}>
        {/* 合同类型概览卡片 */}
        <Col span={24}>
          <Card 
            title="📋 支持的合同类型" 
            size="small"
            extra={
              <span style={{ fontSize: '12px', color: '#999' }}>
                共 {types.filter(t => t.is_active).length} 种类型
              </span>
            }
          >
            {loading && <Spin />}
            {error && <span style={{ color: '#ff4d4f' }}>加载失败: {error}</span>}
            {!loading && !error && (
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {types
                  .filter(type => type.is_active)
                  .sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0))
                  .map(type => (
                    <Tag 
                      key={type.id} 
                      color="blue"
                      style={{ margin: 0 }}
                    >
                      {type.type_name}
                    </Tag>
                  ))
                }
              </div>
            )}
          </Card>
        </Col>
        
        {/* 上传组件 */}
        <Col span={24}>
          <ContractUpload />
        </Col>
        
        {/* 处理中的合同 */}
        <Col span={24}>
          <ContractList filter="processing" />
        </Col>
        
        {/* 已完成的合同 */}
        <Col span={24}>
          <ContractList filter="completed" />
        </Col>
      </Row>
    </div>
  )
}

