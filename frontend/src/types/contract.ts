// 合同类型定义

export type ContractStatus = 'pending' | 'processing' | 'completed' | 'failed'
export type RiskLevel = 'low' | 'medium' | 'high'

export interface Contract {
  id: string
  filename: string
  fileFormat: string
  fileSize: number
  status: ContractStatus
  progress: number
  currentStep?: string
  riskLevel?: RiskLevel
  uploadTime: string
  completedTime?: string
  uploadedBy: string
  reportUrl?: string
}

export interface ContractDetail extends Contract {
  parsedText?: string
  regulations?: Regulation[]
  riskAssessment?: RiskAssessment
  workflow?: WorkflowExecution
}

export interface Regulation {
  id: string
  title: string
  content: string
  relevanceScore: number
}

export interface RiskAssessment {
  riskLevel: RiskLevel
  riskScore: number
  conflicts: Conflict[]
  summary: string
  suggestions: string[]
}

export interface Conflict {
  type: string
  contractClause: string
  regulation: string
  severity: RiskLevel
  suggestion: string
}

export interface WorkflowExecution {
  executionId: string
  workflowName: string
  steps: WorkflowStep[]
  startTime: string
  endTime?: string
}

export interface WorkflowStep {
  name: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  startTime?: string
  endTime?: string
  duration?: number
  message?: string
}

