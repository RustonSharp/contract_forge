import { Row, Col } from 'antd'
import ContractUpload from '@/components/ContractUpload'
import ContractList from '@/components/ContractList'

export default function Dashboard() {
  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>工作台</h1>
      
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <ContractUpload />
        </Col>
        
        <Col span={24}>
          <ContractList filter="processing" />
        </Col>
        
        <Col span={24}>
          <ContractList filter="completed" />
        </Col>
      </Row>
    </div>
  )
}

