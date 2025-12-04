import { create } from 'zustand'
import { Contract } from '@/types/contract'

// Zustand Store - 简单的状态管理
interface ContractStore {
  // 状态
  contracts: Contract[]
  selectedContract: Contract | null
  
  // 操作
  addContract: (contract: Contract) => void
  updateContract: (id: string, updates: Partial<Contract>) => void
  removeContract: (id: string) => void
  selectContract: (id: string) => void
  clearSelection: () => void
}

export const useContractStore = create<ContractStore>((set) => ({
  // 初始状态
  contracts: [],
  selectedContract: null,
  
  // 添加合同
  addContract: (contract) =>
    set((state) => ({
      contracts: [contract, ...state.contracts],
    })),
  
  // 更新合同
  updateContract: (id, updates) =>
    set((state) => ({
      contracts: state.contracts.map((c) =>
        c.id === id ? { ...c, ...updates } : c
      ),
      // 如果更新的是当前选中的合同，也更新选中状态
      selectedContract:
        state.selectedContract?.id === id
          ? { ...state.selectedContract, ...updates }
          : state.selectedContract,
    })),
  
  // 删除合同
  removeContract: (id) =>
    set((state) => ({
      contracts: state.contracts.filter((c) => c.id !== id),
      selectedContract:
        state.selectedContract?.id === id ? null : state.selectedContract,
    })),
  
  // 选中合同
  selectContract: (id) =>
    set((state) => ({
      selectedContract: state.contracts.find((c) => c.id === id) || null,
    })),
  
  // 清除选择
  clearSelection: () =>
    set({
      selectedContract: null,
    }),
}))

