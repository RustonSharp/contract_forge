/**
 * 合同类型 API 调用示例
 * 
 * 展示各种调用后端 API 的方式
 */

import { useState } from 'react'
import { contractTypeService, ContractTypeCreate } from '@/services/contractTypeService'
import { useContractTypes } from '@/hooks/useContractTypes'

// ============================================
// 示例 1: 使用自定义 Hook（推荐）
// ============================================
export const Example1_UseHook = () => {
  const { types, loading, error, refresh } = useContractTypes()

  if (loading) return <div>加载中...</div>
  if (error) return <div>错误: {error}</div>

  return (
    <div>
      <button onClick={refresh}>刷新</button>
      <ul>
        {types.map(type => (
          <li key={type.id}>{type.type_name}</li>
        ))}
      </ul>
    </div>
  )
}

// ============================================
// 示例 2: 直接调用 API 服务
// ============================================
export const Example2_DirectCall = () => {
  const [types, setTypes] = useState([])

  const fetchTypes = async () => {
    try {
      const data = await contractTypeService.getAllTypes()
      setTypes(data)
    } catch (error) {
      console.error('Failed to fetch:', error)
    }
  }

  return (
    <div>
      <button onClick={fetchTypes}>获取合同类型</button>
      {/* 渲染列表 */}
    </div>
  )
}

// ============================================
// 示例 3: 创建合同类型（带表单）
// ============================================
export const Example3_CreateType = () => {
  const [formData, setFormData] = useState<ContractTypeCreate>({
    type_code: '',
    type_name: '',
    description: '',
    default_workflow: 'standard_contract_processing',
  })
  const [submitting, setSubmitting] = useState(false)
  const [message, setMessage] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      setSubmitting(true)
      setMessage('')
      
      const created = await contractTypeService.createType(formData)
      
      setMessage(`✅ 创建成功: ${created.type_name}`)
      
      // 重置表单
      setFormData({
        type_code: '',
        type_name: '',
        description: '',
        default_workflow: 'standard_contract_processing',
      })
    } catch (error) {
      setMessage(`❌ 创建失败: ${error instanceof Error ? error.message : '未知错误'}`)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="类型代码"
        value={formData.type_code}
        onChange={(e) => setFormData({ ...formData, type_code: e.target.value })}
        required
      />
      
      <input
        type="text"
        placeholder="类型名称"
        value={formData.type_name}
        onChange={(e) => setFormData({ ...formData, type_name: e.target.value })}
        required
      />
      
      <textarea
        placeholder="描述（可选）"
        value={formData.description || ''}
        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
      />
      
      <button type="submit" disabled={submitting}>
        {submitting ? '创建中...' : '创建'}
      </button>
      
      {message && <p>{message}</p>}
    </form>
  )
}

// ============================================
// 示例 4: 获取单个合同类型
// ============================================
export const Example4_GetSingleType = () => {
  const [typeCode, setTypeCode] = useState('SALES')
  const [type, setType] = useState(null)
  const [loading, setLoading] = useState(false)

  const fetchType = async () => {
    try {
      setLoading(true)
      const data = await contractTypeService.getTypeByCode(typeCode)
      setType(data)
    } catch (error) {
      console.error('Failed to fetch type:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <input
        type="text"
        value={typeCode}
        onChange={(e) => setTypeCode(e.target.value)}
        placeholder="输入类型代码"
      />
      <button onClick={fetchType} disabled={loading}>
        {loading ? '查询中...' : '查询'}
      </button>
      
      {type && (
        <div>
          <h3>{type.type_name}</h3>
          <p>{type.description}</p>
        </div>
      )}
    </div>
  )
}

// ============================================
// 示例 5: 在下拉框中使用
// ============================================
export const Example5_SelectDropdown = () => {
  const { types, loading } = useContractTypes()
  const [selectedType, setSelectedType] = useState('')

  if (loading) return <div>加载选项中...</div>

  return (
    <select 
      value={selectedType}
      onChange={(e) => setSelectedType(e.target.value)}
    >
      <option value="">请选择合同类型</option>
      {types.map(type => (
        <option key={type.id} value={type.type_code}>
          {type.type_name}
        </option>
      ))}
    </select>
  )
}

// ============================================
// 示例 6: 带错误处理和重试
// ============================================
export const Example6_WithRetry = () => {
  const [types, setTypes] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [retryCount, setRetryCount] = useState(0)

  const fetchTypes = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const data = await contractTypeService.getAllTypes()
      setTypes(data)
      setRetryCount(0) // 成功后重置计数
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '未知错误'
      setError(errorMessage)
      
      // 自动重试（最多3次）
      if (retryCount < 3) {
        console.log(`重试 ${retryCount + 1}/3...`)
        setTimeout(() => {
          setRetryCount(prev => prev + 1)
        }, 2000) // 2秒后重试
      }
    } finally {
      setLoading(false)
    }
  }

  // 监听重试计数变化
  React.useEffect(() => {
    if (retryCount > 0) {
      fetchTypes()
    }
  }, [retryCount])

  return (
    <div>
      <button onClick={fetchTypes} disabled={loading}>
        {loading ? '加载中...' : '获取数据'}
      </button>
      
      {error && (
        <div>
          <p>❌ {error}</p>
          {retryCount < 3 && <p>正在重试 ({retryCount}/3)...</p>}
        </div>
      )}
      
      <ul>
        {types.map(type => (
          <li key={type.id}>{type.type_name}</li>
        ))}
      </ul>
    </div>
  )
}

// ============================================
// 示例 7: 缓存和防抖
// ============================================
export const Example7_WithCache = () => {
  const [types, setTypes] = useState([])
  const [lastFetch, setLastFetch] = useState<number | null>(null)
  const CACHE_DURATION = 5 * 60 * 1000 // 5分钟缓存

  const fetchTypes = async (force = false) => {
    // 检查缓存
    if (!force && lastFetch && Date.now() - lastFetch < CACHE_DURATION) {
      console.log('使用缓存数据')
      return
    }

    try {
      const data = await contractTypeService.getAllTypes()
      setTypes(data)
      setLastFetch(Date.now())
    } catch (error) {
      console.error('Failed to fetch:', error)
    }
  }

  React.useEffect(() => {
    fetchTypes()
  }, [])

  return (
    <div>
      <button onClick={() => fetchTypes(true)}>
        强制刷新
      </button>
      {lastFetch && (
        <p>上次更新: {new Date(lastFetch).toLocaleTimeString()}</p>
      )}
      {/* 渲染列表 */}
    </div>
  )
}

