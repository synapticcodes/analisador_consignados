import {
  formatCurrency,
  type ConsignadoLineDetail,
  type LoanContractDetail,
} from '@/types/api'
import {
  inferInstitution,
  BANK_MATCHERS,
  GENERIC_TOKENS,
} from './pdf-utils'

// Re-export for backward compatibility
export { inferInstitution, BANK_MATCHERS, GENERIC_TOKENS }

type DebtMapSectionProps = {
  contracts: LoanContractDetail[]
  consignadoLines: ConsignadoLineDetail[]
  salarioLiquidoCent?: number | null
  beneficioBrutoCent?: number | null
  totalDescontosCent?: number | null
  consignadoMensalCent?: number | null
  rowOffset?: number
  rowLimit?: number
  title?: string
  showReconciliationOverride?: boolean
}

export type DebtMapRow = {
  lender: string
  totalCent: number
}

export type DebtMapData = {
  rows: DebtMapRow[]
  maxCent: number
  consignadoBaseCent: number
  totalDescontosCent: number | null
  outrosDescontosCent: number | null
  showReconciliation: boolean
}

function getRateColor(rate: number | null): string {
  if (rate === null) return 'text-slate-500'
  if (rate <= 20) return 'text-emerald-700'
  if (rate <= 35) return 'text-amber-700'
  return 'text-red-700'
}

function getCommitmentLabel(
  totalCent: number,
  salarioLiquidoCent: number | null | undefined,
  beneficioBrutoCent: number | null | undefined
): { text: string; percent: number | null } {
  if (salarioLiquidoCent && salarioLiquidoCent > 0) {
    const percent = (totalCent / salarioLiquidoCent) * 100
    const formatted = percent.toFixed(1).replace('.', ',')
    return {
      text: `Comprometimento do salário: ${formatted}%`,
      percent,
    }
  }

  if (beneficioBrutoCent && beneficioBrutoCent > 0) {
    const percent = (totalCent / beneficioBrutoCent) * 100
    const formatted = percent.toFixed(1).replace('.', ',')
    return {
      text: `Comprometimento do benefício: ${formatted}%`,
      percent,
    }
  }

  return {
    text: 'Comprometimento do benefício: N/D',
    percent: null,
  }
}

function getConsignadoShareLabel(
  totalCent: number,
  consignadoBaseCent: number
): { text: string; percent: number | null } {
  if (!consignadoBaseCent || consignadoBaseCent <= 0) {
    return {
      text: 'Participação no consignado identificado: N/D',
      percent: null,
    }
  }

  const percent = (totalCent / consignadoBaseCent) * 100
  const formatted = percent.toFixed(1).replace('.', ',')
  return {
    text: `Participação no consignado identificado: ${formatted}%`,
    percent,
  }
}

export function buildDebtMapData(params: {
  contracts: LoanContractDetail[]
  consignadoLines: ConsignadoLineDetail[]
  consignadoMensalCent?: number | null
  totalDescontosCent?: number | null
}): DebtMapData {
  const grouped = new Map<string, DebtMapRow>()
  const consignadoFromLinesCent = params.consignadoLines.reduce(
    (acc, item) => acc + item.valor_cent,
    0
  )
  const consignadoBaseCent = params.consignadoMensalCent ?? consignadoFromLinesCent
  const showReconciliation =
    params.totalDescontosCent !== null &&
    params.totalDescontosCent !== undefined &&
    params.totalDescontosCent > 0
  const outrosDescontosCent = showReconciliation
    ? Math.max((params.totalDescontosCent ?? 0) - consignadoBaseCent, 0)
    : null

  for (const item of params.contracts) {
    const lender = item.lender_name || 'Banco não identificado'
    if (!grouped.has(lender)) {
      grouped.set(lender, { lender, totalCent: 0 })
    }
    const row = grouped.get(lender)!
    row.totalCent += item.parcela_cent ?? 0
  }

  for (const line of params.consignadoLines) {
    const lender = inferInstitution(line)
    if (!grouped.has(lender)) {
      grouped.set(lender, { lender, totalCent: 0 })
    }
    const row = grouped.get(lender)!
    row.totalCent += line.valor_cent
  }

  const rows = Array.from(grouped.values()).sort((a, b) => b.totalCent - a.totalCent)
  return {
    rows,
    maxCent: rows[0]?.totalCent ?? 1,
    consignadoBaseCent,
    totalDescontosCent: params.totalDescontosCent ?? null,
    outrosDescontosCent,
    showReconciliation,
  }
}

export function DebtMapSection({
  contracts,
  consignadoLines,
  salarioLiquidoCent = null,
  beneficioBrutoCent = null,
  totalDescontosCent = null,
  consignadoMensalCent = null,
  rowOffset = 0,
  rowLimit,
  title = 'Mapa de Dívidas por Banco',
  showReconciliationOverride,
}: DebtMapSectionProps) {
  const data = buildDebtMapData({
    contracts,
    consignadoLines,
    consignadoMensalCent,
    totalDescontosCent,
  })

  const start = Math.max(0, rowOffset)
  const size = rowLimit === undefined ? data.rows.length : Math.max(0, rowLimit)
  const visibleRows = data.rows.slice(start, start + size)
  const showReconciliation =
    showReconciliationOverride ?? (data.showReconciliation && start === 0)

  if (visibleRows.length === 0) return null

  return (
    <section className="space-y-3">
      <h3 className="text-xl font-semibold text-slate-900">{title}</h3>
      {showReconciliation && data.totalDescontosCent !== null && (
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs">
          <p className="mb-2 font-semibold text-slate-900">Reconciliação dos descontos</p>
          <div className="grid gap-1 text-slate-700">
            <div className="flex items-center justify-between">
              <span>Consignado identificado (linhas do contracheque)</span>
              <span className="font-semibold text-slate-900">
                {formatCurrency(data.consignadoBaseCent)}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span>Outros descontos (não consignados)</span>
              <span className="font-semibold text-slate-900">
                {formatCurrency(data.outrosDescontosCent)}
              </span>
            </div>
            <div className="mt-1 flex items-center justify-between border-t border-slate-200 pt-1">
              <span className="font-semibold text-slate-900">Total de descontos</span>
              <span className="font-semibold text-slate-900">
                {formatCurrency(data.totalDescontosCent)}
              </span>
            </div>
          </div>
        </div>
      )}
      <div className="space-y-2">
        {visibleRows.map((row) => {
          const commitment = getCommitmentLabel(
            row.totalCent,
            salarioLiquidoCent,
            beneficioBrutoCent
          )
          const consignadoShare = getConsignadoShareLabel(row.totalCent, data.consignadoBaseCent)
          return (
            <div key={row.lender} className="rounded-lg border border-slate-200 p-3 text-sm">
              <div className="flex items-center justify-between">
                <p className="font-medium text-slate-900">{row.lender}</p>
                <p className="font-semibold text-slate-900">{formatCurrency(row.totalCent)}</p>
              </div>
              <div className="mt-2 h-2 rounded bg-slate-200">
                <div
                  className="h-2 rounded bg-slate-700"
                  style={{
                    width: `${Math.max(
                      5,
                      Math.round((row.totalCent / data.maxCent) * 100)
                    )}%`,
                  }}
                />
              </div>
              <p className={`mt-2 text-xs font-medium ${getRateColor(commitment.percent)}`}>
                {commitment.text}
              </p>
              <p className={`mt-1 text-xs font-medium ${getRateColor(consignadoShare.percent)}`}>
                {consignadoShare.text}
              </p>
            </div>
          )
        })}
      </div>
    </section>
  )
}
