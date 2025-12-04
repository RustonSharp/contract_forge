import { Outlet, Link, useLocation } from 'react-router-dom'
import { Layout as AntLayout, Menu } from 'antd'
import {
  DashboardOutlined,
  FileTextOutlined,
  HistoryOutlined,
} from '@ant-design/icons'
import './styles.css'

const { Header, Content, Sider } = AntLayout

export default function Layout() {
  const location = useLocation()
  
  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: <Link to="/dashboard">工作台</Link>,
    },
    {
      key: '/history',
      icon: <HistoryOutlined />,
      label: <Link to="/history">历史记录</Link>,
    },
  ]
  
  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Header className="header">
        <div className="logo">
          <FileTextOutlined style={{ fontSize: 24, marginRight: 8 }} />
          <span>智能合同处理系统</span>
        </div>
        <div className="user-info">
          <span>欢迎，用户</span>
        </div>
      </Header>
      
      <AntLayout>
        <Sider width={200} className="site-layout-background">
          <Menu
            mode="inline"
            selectedKeys={[location.pathname]}
            items={menuItems}
            style={{ height: '100%', borderRight: 0 }}
          />
        </Sider>
        
        <AntLayout style={{ padding: '24px' }}>
          <Content
            style={{
              padding: 24,
              margin: 0,
              minHeight: 280,
              background: '#fff',
              borderRadius: 8,
            }}
          >
            <Outlet />
          </Content>
        </AntLayout>
      </AntLayout>
    </AntLayout>
  )
}

