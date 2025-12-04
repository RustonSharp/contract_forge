import { useState, useEffect } from 'react'
import { contractTypeService, ContractType } from '@/services/contractTypeService'
import './styles.css'

/**
 * 合同类型列表组件
 */
const ContractTypeList = () => {
  const [types, setTypes] = useState<ContractType[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 加载合同类型列表
  const loadTypes = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const data = await contractTypeService.getAllTypes()
      setTypes(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load contract types')
      console.error('Error loading contract types:', err)
    } finally {
      setLoading(false)
    }
  }

  // 组件挂载时加载数据
  useEffect(() => {
    loadTypes()
  }, [])

  // 渲染加载状态
  if (loading) {
    return (
      <div className="contract-type-list loading">
        <div className="spinner"></div>
        <p>加载中...</p>
      </div>
    )
  }

  // 渲染错误状态
  if (error) {
    return (
      <div className="contract-type-list error">
        <p className="error-message">❌ {error}</p>
        <button onClick={loadTypes}>重试</button>
      </div>
    )
  }

  // 渲染列表
  return (
    <div className="contract-type-list">
      <div className="header">
        <h2>合同类型列表</h2>
        <button onClick={loadTypes} className="refresh-btn">
          🔄 刷新
        </button>
      </div>

      <div className="type-grid">
        {types.map((type) => (
          <div 
            key={type.id} 
            className={`type-card ${type.is_active ? 'active' : 'inactive'}`}
          >
            <div className="type-header">
              <h3>{type.type_name}</h3>
              <span className="type-code">{type.type_code}</span>
            </div>
            
            {type.description && (
              <p className="description">{type.description}</p>
            )}
            
            <div className="type-footer">
              <span className="workflow">
                📋 {type.default_workflow}
              </span>
              <span className={`status ${type.is_active ? 'active' : 'inactive'}`}>
                {type.is_active ? '✅ 启用' : '❌ 禁用'}
              </span>
            </div>
          </div>
        ))}
      </div>

      {types.length === 0 && (
        <div className="empty-state">
          <p>暂无合同类型</p>
        </div>
      )}
    </div>
  )
}

export default ContractTypeList

