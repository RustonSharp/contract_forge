import { useState, useEffect, useCallback } from 'react'
import { contractTypeService, ContractType } from '@/services/contractTypeService'

/**
 * 合同类型数据 Hook
 * 
 * 用法：
 *   const { types, loading, error, refresh } = useContractTypes()
 */
export const useContractTypes = () => {
  const [types, setTypes] = useState<ContractType[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 加载合同类型
  const loadTypes = useCallback(async () => {
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
  }, [])

  // 初始加载
  useEffect(() => {
    loadTypes()
  }, [loadTypes])

  return {
    types,
    loading,
    error,
    refresh: loadTypes,
  }
}

/**
 * 单个合同类型 Hook
 * 
 * 用法：
 *   const { type, loading, error } = useContractType('SALES')
 */
export const useContractType = (typeCode: string) => {
  const [type, setType] = useState<ContractType | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!typeCode) return

    const loadType = async () => {
      try {
        setLoading(true)
        setError(null)
        
        const data = await contractTypeService.getTypeByCode(typeCode)
        setType(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load contract type')
        console.error('Error loading contract type:', err)
      } finally {
        setLoading(false)
      }
    }

    loadType()
  }, [typeCode])

  return {
    type,
    loading,
    error,
  }
}

