/**
 * API Types - TypeScript definitions for backend API
 */

export type JobStatus = 'PENDING' | 'RUNNING' | 'SUCCEEDED' | 'FAILED'

export interface CreateJobRequest {
  files: File[]
  renda_mensal_declarada?: string
  gasto_dividas_declarado?: string
  product_id: string
}

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

export interface OfferApi {
  id: string
  product_id: string
  kind: string
  installment_count: number
  installment_value_cent: number
  total_value_cent: number
  entry_value_cent?: number | null
  entry_due_days?: number | null
  first_payment_days: number
  payment_method: string
  salary_liquid_used_cent: number
  percent_used: number
  text: string
  created_at: string
}

export interface LoanContractDetailApi {
  id: string
  lender_name: string
  contract_id: string | null
  parcela_cent: number | null
  parcelas_restantes: number | null
  valor_total_cent: number | null
  taxa_juros: string | null
  status: string
  cet_mensal: string | null
  cet_anual: string | null
  iof_cent: number | null
  valor_emprestado_cent: number | null
}

export interface ConsignadoLineDetailApi {
  descricao: string
  rubrica: string | null
  valor_cent: number
}

export interface INSSMarginDetailApi {
  base_calculo_cent: number | null
  max_comprometimento_cent: number | null
  total_comprometido_cent: number | null
  margem_emprestimo_cent: number | null
  margem_rmc_cent: number | null
  margem_rcc_cent: number | null
  cet_mensal: string | null
  cet_anual: string | null
  rmc_banco: string | null
  rmc_limite_cent: number | null
  rmc_reservado_cent: number | null
  evidence: Record<string, string> | null
}

export interface HistoricalContractDetailApi {
  id: string
  lender_name: string | null
  contract_id: string | null
  data_contratacao: string | null
  data_quitacao: string | null
  parcela_cent: number | null
  valor_emprestado_cent: number | null
  motivo_encerramento: string | null
}

export interface ContractCostDetailApi {
  contract_id: string | null
  lender_name: string | null
  parcela_cent: number | null
  parcelas_restantes: number | null
  valor_emprestado_cent: number | null
  total_a_pagar_cent: number | null
  custo_juros_cent: number | null
  percentual_juros_basis_points: number | null
}

export interface SavingsSimulationContractDetailApi {
  contract_key: string
  lender_name: string
  parcela_atual_cent: number
  parcela_nova_estimada_cent: number
  economia_mensal_cent: number
  economia_total_restante_cent: number
  parcelas_restantes: number
  taxa_atual_mensal_percent: string
  taxa_referencia_mensal_percent: string
}

export interface SavingsSimulationDetailApi {
  economia_mensal_total_cent: number
  economia_total_restante_cent: number
  taxa_referencia_mensal_percent: string
  disclaimer: string
  contratos: SavingsSimulationContractDetailApi[]
}

export interface ReportLayersApi {
  confirmado: string[]
  indicacao: string[]
  nao_disponivel: string[]
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
  offers: OfferApi[] | null
  loan_contracts: LoanContractDetailApi[] | null
  consignado_lines: ConsignadoLineDetailApi[] | null
  inss_margin: INSSMarginDetailApi | null
  historical_contracts: HistoricalContractDetailApi[] | null
  custo_juros_total_cent: number | null
  custo_juros_total_brl: number | null
  custo_juros_por_contrato: ContractCostDetailApi[] | null
  savings_simulation: SavingsSimulationDetailApi | null
  report_layers: ReportLayersApi | null
  provenance?: Record<string, unknown> | null
  calculation_methods?: Record<string, string> | null
  confidence_scores?: Record<string, number> | null
}

export interface ProductApi {
  id: string
  name: string
  base_value_cent: number
  installments: number[]
  payment_methods: string[]
  active: boolean
  created_at: string
}

export interface Offer {
  id: string
  product_id: string
  kind: string
  installment_count: number
  installment_value_cent: number
  total_value_cent: number
  entry_value_cent?: number | null
  entry_due_days?: number | null
  first_payment_days: number
  payment_method: string
  salary_liquid_used_cent: number
  percent_used: number
  text: string
  created_at: string
}

export interface Alert {
  type: string
  severity: 'INFO' | 'WARNING' | 'ERROR'
  message: string
  field?: string
  details?: Record<string, unknown>
}

export interface LoanContractDetail {
  id: string
  lender_name: string
  contract_id: string | null
  parcela_cent: number | null
  parcelas_restantes: number | null
  valor_total_cent: number | null
  taxa_juros: string | null
  status: string
  cet_mensal: string | null
  cet_anual: string | null
  iof_cent: number | null
  valor_emprestado_cent: number | null
}

export interface ConsignadoLineDetail {
  descricao: string
  rubrica: string | null
  valor_cent: number
}

export interface INSSMarginDetail {
  base_calculo_cent: number | null
  max_comprometimento_cent: number | null
  total_comprometido_cent: number | null
  margem_emprestimo_cent: number | null
  margem_rmc_cent: number | null
  margem_rcc_cent: number | null
  cet_mensal: string | null
  cet_anual: string | null
  rmc_banco: string | null
  rmc_limite_cent: number | null
  rmc_reservado_cent: number | null
  evidence: Record<string, string> | null
}

export interface HistoricalContractDetail {
  id: string
  lender_name: string | null
  contract_id: string | null
  data_contratacao: string | null
  data_quitacao: string | null
  parcela_cent: number | null
  valor_emprestado_cent: number | null
  motivo_encerramento: string | null
}

export interface ContractCostDetail {
  contract_id: string | null
  lender_name: string | null
  parcela_cent: number | null
  parcelas_restantes: number | null
  valor_emprestado_cent: number | null
  total_a_pagar_cent: number | null
  custo_juros_cent: number | null
  percentual_juros_basis_points: number | null
}

export interface SavingsSimulationContractDetail {
  contract_key: string
  lender_name: string
  parcela_atual_cent: number
  parcela_nova_estimada_cent: number
  economia_mensal_cent: number
  economia_total_restante_cent: number
  parcelas_restantes: number
  taxa_atual_mensal_percent: string
  taxa_referencia_mensal_percent: string
}

export interface SavingsSimulationDetail {
  economia_mensal_total_cent: number
  economia_total_restante_cent: number
  taxa_referencia_mensal_percent: string
  disclaimer: string
  contratos: SavingsSimulationContractDetail[]
}

export interface ReportLayers {
  confirmado: string[]
  indicacao: string[]
  nao_disponivel: string[]
}

export interface FinalResultResponse {
  job_id: string
  competencia_alvo: string
  salario_bruto_cent: number | null
  salario_liquido_cent: number | null
  total_descontos_cent: number | null
  divida_mensal_cent: number | null
  divida_mensal_reduzida_cent: number | null
  consignado_mensal_cent: number | null
  divida_total_consignada_cent: number | null
  divida_total_reduzida_cent: number | null
  parcelas_restantes_total: number | null
  alerts?: Alert[] | null
  offers?: Offer[] | null
  loan_contracts?: LoanContractDetail[] | null
  consignado_lines?: ConsignadoLineDetail[] | null
  inss_margin?: INSSMarginDetail | null
  historical_contracts?: HistoricalContractDetail[] | null
  custo_juros_total_cent?: number | null
  custo_juros_total_brl?: number | null
  custo_juros_por_contrato?: ContractCostDetail[] | null
  savings_simulation?: SavingsSimulationDetail | null
  report_layers?: ReportLayers | null
  provenance?: Record<string, unknown> | null
  calculation_methods?: Record<string, string> | null
  confidence_scores?: Record<string, number> | null
  created_at?: string
}

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

export function parseCurrency(value: string): string {
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

export function formatDate(isoDate: string): string {
  const date = new Date(isoDate)
  if (Number.isNaN(date.getTime())) {
    return '--'
  }

  return date.toLocaleString('pt-BR', {
    timeZone: 'America/Sao_Paulo',
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

export function formatCompetencia(competencia: string | null): string {
  if (!competencia) return '--'

  const [year, month] = competencia.split('-')
  const monthNames = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
  ]

  const monthIndex = parseInt(month) - 1
  return `${monthNames[monthIndex]} ${year}`
}

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
