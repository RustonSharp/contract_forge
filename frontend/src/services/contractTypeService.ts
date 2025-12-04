import api from './api'

/**
 * 合同类型数据接口
 */
export interface ContractType {
  id?: number
  type_code: string
  type_name: string
  description?: string | null
  default_workflow?: string
  is_active?: boolean
  sort_order?: number
  created_at?: string
  updated_at?: string
}

/**
 * 创建合同类型请求
 */
export interface ContractTypeCreate {
  type_code: string
  type_name: string
  description?: string | null
  default_workflow?: string
}

/**
 * API 响应格式
 */
interface ApiResponse<T> {
  success: boolean
  data?: T
  message?: string
  error?: string
}

/**
 * 合同类型 API 服务
 */
export const contractTypeService = {
  /**
   * 获取所有合同类型
   */
  getAllTypes: async (): Promise<ContractType[]> => {
    const response = await api.get<any, ApiResponse<ContractType[]>>(
      '/contract-type/all'
    )
    
    if (response.success && response.data) {
      return response.data
    }
    
    throw new Error(response.error || 'Failed to fetch contract types')
  },

  /**
   * 根据代码获取合同类型
   */
  getTypeByCode: async (typeCode: string): Promise<ContractType> => {
    const response = await api.get<any, ApiResponse<ContractType>>(
      `/contract-type/${typeCode}`
    )
    
    if (response.success && response.data) {
      return response.data
    }
    
    throw new Error(response.error || `Contract type '${typeCode}' not found`)
  },

  /**
   * 创建合同类型
   */
  createType: async (data: ContractTypeCreate): Promise<ContractType> => {
    const response = await api.post<any, ApiResponse<ContractType>>(
      '/contract-type/',
      data
    )
    
    if (response.success && response.data) {
      return response.data
    }
    
    throw new Error(response.error || 'Failed to create contract type')
  },
}

export default contractTypeService

