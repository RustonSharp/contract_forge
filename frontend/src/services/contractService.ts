import api from './api'
import { Contract, ContractDetail } from '@/types/contract'

// 合同相关的 API 服务

export const contractService = {
  // 上传合同
  uploadContract: async (file: File, options?: {
    contractType?: string
    amount?: number
    urgency?: string
  }) => {
    const formData = new FormData()
    formData.append('file', file)
    
    if (options?.contractType) {
      formData.append('contract_type', options.contractType)
    }
    if (options?.amount) {
      formData.append('amount', options.amount.toString())
    }
    if (options?.urgency) {
      formData.append('urgency', options.urgency)
    }
    
    return api.post<any, { execution_id: string; workflow_used: string }>(
      '/contract/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )
  },
  
  // 获取合同列表
  getContracts: async () => {
    return api.get<any, Contract[]>('/contracts')
  },
  
  // 获取合同详情
  getContractDetail: async (id: string) => {
    return api.get<any, ContractDetail>(`/contract/${id}`)
  },
  
  // 获取合同状态
  getContractStatus: async (executionId: string) => {
    return api.get<any, {
      status: string
      progress: number
      current_step: string
    }>(`/contract/status/${executionId}`)
  },
}

