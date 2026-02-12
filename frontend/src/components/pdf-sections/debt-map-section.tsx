import {
  formatCurrency,
  type ConsignadoLineDetail,
  type LoanContractDetail,
} from '@/types/api'

type DebtMapSectionProps = {
  contracts: LoanContractDetail[]
  consignadoLines: ConsignadoLineDetail[]
  salarioLiquidoCent?: number | null
}

type GroupedDebt = {
  lender: string
  totalCent: number
}

function inferInstitution(line: ConsignadoLineDetail): string {
  const descricao =
    line.descricao_raw?.trim() ||
    line.descricao_canonica?.trim() ||
    line.descricao?.trim() ||
    ''
  const source = `${descricao} ${line.rubrica ?? ''}`.toUpperCase()
  const patterns = [
    'BMG',
    'PAN',
    'BRADESCO',
    'ITAU',
    'SANTANDER',
    'CAIXA',
    'SAFRA',
    'C6',
    'AGIBANK',
    'DAYCOVAL',
    'MERCANTIL',
    'BANRISUL',
    'NUBANK',
    'BB',
  ]
  const found = patterns.find((item) => source.includes(item))
  return found ? `Banco ${found}` : 'Contracheque (sem banco identificado)'
}

function getRateColor(rate: number | null): string {
  if (rate === null) return 'text-slate-500'
  if (rate <= 20) return 'text-emerald-700'
  if (rate <= 35) return 'text-amber-700'
  return 'text-red-700'
}

function getCommitmentLabel(
  totalCent: number,
  salarioLiquidoCent: number | null | undefined
): { text: string; percent: number | null } {
  if (!salarioLiquidoCent || salarioLiquidoCent <= 0) {
    return {
      text: 'Comprometimento do salário: N/D',
      percent: null,
    }
  }

  const percent = (totalCent / salarioLiquidoCent) * 100
  const formatted = percent.toFixed(1).replace('.', ',')
  return {
    text: `Comprometimento do salário: ${formatted}%`,
    percent,
  }
}

export function DebtMapSection({
  contracts,
  consignadoLines,
  salarioLiquidoCent = null,
}: DebtMapSectionProps) {
  if (contracts.length === 0 && consignadoLines.length === 0) return null

  const grouped = new Map<string, GroupedDebt>()

  for (const item of contracts) {
    const lender = item.lender_name || 'Banco não identificado'
    if (!grouped.has(lender)) {
      grouped.set(lender, { lender, totalCent: 0 })
    }
    const row = grouped.get(lender)!
    row.totalCent += item.parcela_cent ?? 0
  }

  for (const line of consignadoLines) {
    const lender = inferInstitution(line)
    if (!grouped.has(lender)) {
      grouped.set(lender, { lender, totalCent: 0 })
    }
    const row = grouped.get(lender)!
    row.totalCent += line.valor_cent
  }

  const rows = Array.from(grouped.values()).sort((a, b) => b.totalCent - a.totalCent)
  const max = rows[0]?.totalCent ?? 1

  return (
    <section className="space-y-3">
      <h3 className="text-xl font-semibold text-slate-900">Mapa de Dívidas por Banco</h3>
      <div className="space-y-2">
        {rows.map((row) => {
          const commitment = getCommitmentLabel(row.totalCent, salarioLiquidoCent)
          return (
            <div key={row.lender} className="rounded-lg border border-slate-200 p-3 text-sm">
            <div className="flex items-center justify-between">
                <p className="font-medium text-slate-900">{row.lender}</p>
                <p className="font-semibold text-slate-900">{formatCurrency(row.totalCent)}</p>
            </div>
            <div className="mt-2 h-2 rounded bg-slate-200">
              <div
                className="h-2 rounded bg-slate-700"
                style={{ width: `${Math.max(5, Math.round((row.totalCent / max) * 100))}%` }}
              />
            </div>
              <p className={`mt-2 text-xs font-medium ${getRateColor(commitment.percent)}`}>
                {commitment.text}
              </p>
          </div>
          )
        })}
      </div>
    </section>
  )
}
