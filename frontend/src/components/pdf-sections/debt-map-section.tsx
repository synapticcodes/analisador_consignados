import {
  formatCurrency,
  type ConsignadoLineDetail,
  type LoanContractDetail,
} from '@/types/api'

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

const BANK_MATCHERS: Array<{ label: string; patterns: RegExp[] }> = [
  { label: 'Banco BRB', patterns: [/\bBRB\b/, /\bBRB\s+CFI\b/] },
  { label: 'Banco INBURSA', patterns: [/\bINBURSA\b/] },
  { label: 'Banco PRB', patterns: [/\bPRB\b/] },
  { label: 'Banco Safra', patterns: [/\bSAFRA\b/, /\bBCO\s+SAF\b/, /\bSAF\b/] },
  { label: 'Banco PANAMERICANO', patterns: [/\bPANAMERICANO\b/] },
  { label: 'Banco PAN', patterns: [/\bPAN\b/] },
  { label: 'Banco SANTANDER', patterns: [/\bSANTANDER\b/] },
  { label: 'Banco BMG', patterns: [/\bBMG\b/] },
  { label: 'Banco BRADESCO', patterns: [/\bBRADESCO\b/] },
  { label: 'Banco ITAU', patterns: [/\bITAU\b/] },
  { label: 'Banco CAIXA', patterns: [/\bCAIXA\b/] },
  { label: 'Banco C6', patterns: [/\bC6\b/] },
  { label: 'Banco AGIBANK', patterns: [/\bAGIBANK\b/] },
  { label: 'Banco DAYCOVAL', patterns: [/\bDAYCOVAL\b/] },
  { label: 'Banco MERCANTIL', patterns: [/\bMERCANTIL\b/] },
  { label: 'Banco BANRISUL', patterns: [/\bBANRISUL\b/] },
  { label: 'Banco NUBANK', patterns: [/\bNUBANK\b/] },
  { label: 'Banco BB', patterns: [/\bBB\b/, /\bBANCO\s+DO\s+BRASIL\b/] },
]

const GENERIC_TOKENS = new Set([
  'BCO',
  'BANCO',
  'PRIVADO',
  'PRIVADOS',
  'OFICIAL',
  'EMPREST',
  'EMPRESTIMO',
  'EMPR',
  'DESCONTO',
  'CONSIGNADO',
  'SEM',
  'CARTAO',
  'CREDITO',
  'AMORT',
  'OLE',
  'CFI',
])

function isGenericToken(token: string): boolean {
  const upper = token.toUpperCase()
  if (!upper) return true
  if (GENERIC_TOKENS.has(upper)) return true
  if (/^EMP\d*$/.test(upper)) return true
  if (/^EMPR?\d*$/.test(upper)) return true
  if (/^\d+$/.test(upper)) return true
  return false
}

function normalizeDynamicBankLabel(token: string): string {
  const upper = token.toUpperCase().replace(/[^A-Z0-9]/g, '')
  if (!upper) return ''
  if (upper === 'SAF') return 'Safra'
  if (upper.length <= 4) return upper
  return `${upper[0]}${upper.slice(1).toLowerCase()}`
}

function inferInstitution(line: ConsignadoLineDetail): string {
  const descricao =
    line.descricao_raw?.trim() ||
    line.descricao_canonica?.trim() ||
    line.descricao?.trim() ||
    ''
  const source = `${descricao} ${line.rubrica ?? ''}`.toUpperCase()
  for (const matcher of BANK_MATCHERS) {
    if (matcher.patterns.some((pattern) => pattern.test(source))) {
      return matcher.label
    }
  }

  const bancoMatch = source.match(/\b(?:BCO|BANCO)\s+([A-Z0-9]{2,})\b/)
  if (bancoMatch?.[1] && !isGenericToken(bancoMatch[1])) {
    const normalized = normalizeDynamicBankLabel(bancoMatch[1])
    if (normalized) {
      return `Banco ${normalized}`
    }
  }

  const dynamicTokens = Array.from(source.matchAll(/(?:^|[\s\-\/])([A-Z0-9]{2,})\b/g))
    .map((match) => match[1])
    .filter((token) => token && !isGenericToken(token))
  if (dynamicTokens.length > 0) {
    const normalized = normalizeDynamicBankLabel(dynamicTokens[0] ?? '')
    if (normalized) {
      return `Banco ${normalized}`
    }
  }

  return 'Contracheque (sem banco identificado)'
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
