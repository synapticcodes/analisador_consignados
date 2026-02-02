/**
 * API Types - TypeScript definitions for backend API
 */

// =============================================
// Job Status
// =============================================
export type JobStatus = 'PENDING' | 'RUNNING' | 'SUCCEEDED' | 'FAILED'

// =============================================
// API Request Types
// =============================================
export interface CreateJobRequest {
  files: File[]
  renda_mensal_declarada?: string
  gasto_dividas_declarado?: string
}

// =============================================
// API Response Types
// =============================================
export interface AnalysisJobResponse {
  id: string
  status: JobStatus
  competencia_alvo: string | null
  created_at: string
  updated_at: string
  completed_at: string | null
  error_code: string | null
  error_message: string | null
}

export interface EvidenceApi {
  file_id: string
  page: number
  text: string
}

export interface MonetaryFieldApi {
  value: number | null
  currency: string
  source: string | null
  evidence: EvidenceApi | null
  method: string | null
}

export interface FinalResultResponseApi {
  job_id: string
  competencia_alvo: string
  salario_bruto: MonetaryFieldApi
  salario_liquido: MonetaryFieldApi
  total_descontos: MonetaryFieldApi
  divida_mensal: MonetaryFieldApi
  divida_mensal_reduzida: MonetaryFieldApi
  consignado_mensal: MonetaryFieldApi
  divida_total_consignada: MonetaryFieldApi
  divida_total_reduzida: MonetaryFieldApi
  parcelas_restantes_total: number | null
  alerts: string[] | null
}

export interface FinalResultResponse {
  job_id: string
  competencia_alvo: string

  // 9 Outputs principais (em centavos)
  salario_bruto_cent: number | null
  salario_liquido_cent: number | null
  total_descontos_cent: number | null
  divida_mensal_cent: number | null
  divida_mensal_reduzida_cent: number | null
  consignado_mensal_cent: number | null
  divida_total_consignada_cent: number | null
  divida_total_reduzida_cent: number | null
  parcelas_restantes_total: number | null

  // Provenance & Alertas
  provenance?: Record<string, any> | null
  alerts?: Alert[] | null

  // Metadata
  calculation_methods?: Record<string, string> | null
  confidence_scores?: Record<string, number> | null

  created_at?: string
}

export interface Alert {
  type: string
  severity: 'INFO' | 'WARNING' | 'ERROR'
  message: string
  field?: string
  details?: Record<string, any>
}

// =============================================
// Helper Functions
// =============================================

/**
 * Converte centavos para formato BRL
 */
export function formatCurrency(centavos: number | null): string {
  if (centavos === null || centavos === undefined) {
    return 'R$ --'
  }

  const reais = centavos / 100
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(reais)
}

/**
 * Converte formato BRL para string centavos
 */
export function parseCurrency(value: string): string {
  // Remove R$, espaços, pontos (milhares) e converte vírgula (decimal) para ponto
  const cleaned = value
    .replace(/R\$/g, '')
    .replace(/\s/g, '')
    .replace(/\./g, '')
    .replace(/,/g, '.')

  const number = parseFloat(cleaned)

  if (isNaN(number)) {
    throw new Error('Valor inválido')
  }

  return number.toFixed(2)
}

/**
 * Formata data ISO para formato brasileiro
 */
export function formatDate(isoDate: string): string {
  return new Date(isoDate).toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/**
 * Formata competência YYYY-MM para formato brasileiro
 */
export function formatCompetencia(competencia: string | null): string {
  if (!competencia) return '--'

  const [year, month] = competencia.split('-')
  const monthNames = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
  ]

  const monthIndex = parseInt(month) - 1
  return `${monthNames[monthIndex]} ${year}`
}

/**
 * Retorna cor do status
 */
export function getStatusColor(status: JobStatus): string {
  switch (status) {
    case 'PENDING':
      return 'bg-yellow-100 text-yellow-800 border-yellow-200'
    case 'RUNNING':
      return 'bg-blue-100 text-blue-800 border-blue-200'
    case 'SUCCEEDED':
      return 'bg-green-100 text-green-800 border-green-200'
    case 'FAILED':
      return 'bg-red-100 text-red-800 border-red-200'
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200'
  }
}

/**
 * Retorna label do status em português
 */
export function getStatusLabel(status: JobStatus): string {
  switch (status) {
    case 'PENDING':
      return 'Aguardando'
    case 'RUNNING':
      return 'Processando'
    case 'SUCCEEDED':
      return 'Concluído'
    case 'FAILED':
      return 'Erro'
    default:
      return status
  }
}
