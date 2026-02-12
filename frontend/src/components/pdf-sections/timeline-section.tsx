import type { HistoricalContractDetail } from '@/types/api'
import { formatCurrency } from '@/types/api'

type TimelineSectionProps = {
  historicalContracts: HistoricalContractDetail[]
  eventOffset?: number
  eventLimit?: number
  title?: string
  showSummary?: boolean
  showReasons?: boolean
}

type TimelineNode = {
  item: HistoricalContractDetail
  start: Date | null
  end: Date | null
  lenderNormalized: string
}

export type TimelineData = {
  nodes: TimelineNode[]
  links: boolean[]
  totalLinks: number
}

function parseIsoDate(value: string | null): Date | null {
  if (!value) return null
  const parsed = new Date(`${value}T00:00:00`)
  if (Number.isNaN(parsed.getTime())) return null
  return parsed
}

function formatMonthYear(value: string | null): string {
  if (!value) return '--'
  const [year, month] = value.split('-')
  if (!year || !month) return value
  return `${month}/${year}`
}

function normalizeLender(value: string | null): string {
  return (value ?? '')
    .toUpperCase()
    .replace(/[^A-Z0-9\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

function hasRefinEvidence(value: string | null): boolean {
  return (value ?? '').toUpperCase().includes('REFINANC')
}

function monthDistance(a: Date, b: Date): number {
  return (b.getFullYear() - a.getFullYear()) * 12 + (b.getMonth() - a.getMonth())
}

function isActiveNode(node: TimelineNode): boolean {
  const reason = (node.item.motivo_encerramento ?? '').toUpperCase()
  if (reason.includes('ATIVO')) return true
  if (!node.end) return false
  const now = new Date()
  return node.end.getTime() >= now.getTime()
}

function hasStrictLink(previous: TimelineNode, current: TimelineNode): boolean {
  if (!hasRefinEvidence(previous.item.motivo_encerramento)) return false
  if (!previous.lenderNormalized || !current.lenderNormalized) return false
  if (previous.lenderNormalized !== current.lenderNormalized) return false

  const prevEnd = previous.end ?? previous.start
  const currStart = current.start
  if (!prevEnd || !currStart) return false

  const diffMonths = monthDistance(prevEnd, currStart)
  if (diffMonths < 0 || diffMonths > 2) return false

  if (previous.item.parcela_cent !== null && current.item.parcela_cent !== null) {
    const prevInstallment = Math.abs(previous.item.parcela_cent)
    const currInstallment = Math.abs(current.item.parcela_cent)
    const base = Math.max(prevInstallment, currInstallment, 1)
    const ratio = Math.abs(prevInstallment - currInstallment) / base
    if (ratio > 0.05) return false
  }

  return true
}

export function buildTimelineData(
  historicalContracts: HistoricalContractDetail[]
): TimelineData {
  const orderedNodes: TimelineNode[] = [...historicalContracts]
    .map((item) => ({
      item,
      start: parseIsoDate(item.data_contratacao),
      end: parseIsoDate(item.data_quitacao),
      lenderNormalized: normalizeLender(item.lender_name),
    }))
    .filter((node) => node.start !== null)
    .sort((a, b) => (a.item.data_contratacao ?? '').localeCompare(b.item.data_contratacao ?? ''))

  const links = orderedNodes.map((node, index) => {
    if (index >= orderedNodes.length - 1) return false
    return hasStrictLink(node, orderedNodes[index + 1]!)
  })
  return {
    nodes: orderedNodes,
    links,
    totalLinks: links.filter(Boolean).length,
  }
}

export function TimelineSection({
  historicalContracts,
  eventOffset = 0,
  eventLimit,
  title = 'Timeline de Refinanciamentos',
  showSummary = true,
  showReasons = true,
}: TimelineSectionProps) {
  if (historicalContracts.length === 0) return null

  const timeline = buildTimelineData(historicalContracts)
  if (timeline.nodes.length === 0) return null

  const safeStart = Math.max(0, eventOffset)
  const safeLimit =
    eventLimit === undefined
      ? timeline.nodes.length
      : Math.max(0, eventLimit)
  const visibleNodes = timeline.nodes.slice(safeStart, safeStart + safeLimit)

  if (visibleNodes.length === 0) return null

  return (
    <section className="space-y-3">
      <h3 className="text-xl font-semibold text-slate-900">{title}</h3>
      {showSummary && (
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-700">
          <p>
            Eventos identificados:{' '}
            <span className="font-semibold text-slate-900">{timeline.nodes.length}</span>
          </p>
          <p>
            Conexões validadas:{' '}
            <span className="font-semibold text-slate-900">{timeline.totalLinks}</span>
          </p>
        </div>
      )}

      <div className="space-y-2">
        {visibleNodes.map((node, localIndex) => {
          const globalIndex = safeStart + localIndex
          const linkedFromPrevious =
            globalIndex > 0 ? timeline.links[globalIndex - 1] ?? false : true
          const linkedToNext = timeline.links[globalIndex] ?? false
          const active = isActiveNode(node)
          const statusLabel = active ? 'ATIVO' : 'ENCERRADO'

          return (
            <div key={node.item.id}>
              <div className="rounded-lg border border-slate-200 bg-white p-3 text-xs">
                <div className="mb-1 flex items-center justify-between gap-2">
                  <p className="font-semibold text-slate-900">
                    {node.item.lender_name ?? 'Banco não identificado'}
                  </p>
                  <span
                    className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                      active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-700'
                    }`}
                  >
                    {statusLabel}
                  </span>
                </div>
                <p className="text-slate-700">
                  {formatMonthYear(node.item.data_contratacao)} {' -> '} {formatMonthYear(node.item.data_quitacao)}
                </p>
                <p className="text-slate-600">
                  Contrato: {node.item.contract_id ?? '--'} {' · '} Parcela:{' '}
                  {formatCurrency(node.item.parcela_cent)}
                </p>
                {node.item.motivo_encerramento && (
                  <p className="text-slate-600">Motivo: {node.item.motivo_encerramento}</p>
                )}
                {!linkedFromPrevious && (
                  <span className="mt-2 inline-flex rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold text-amber-700">
                    Sem vínculo ativo identificado
                  </span>
                )}
              </div>

              {localIndex < visibleNodes.length - 1 && (
                <div className="py-1 text-center text-[10px]">
                  {linkedToNext ? (
                    <p className="font-semibold text-slate-700">↓ refinanciado para ↓</p>
                  ) : (
                    <p className="text-slate-500">sem conexão validada</p>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {showReasons && visibleNodes.some((node) => node.item.motivo_encerramento) && (
        <div className="rounded-lg border border-slate-200 bg-white p-3 text-xs text-slate-600">
          {visibleNodes.map((node) => (
            <p key={`${node.item.id}-reason`}>
              {node.item.lender_name ?? 'Banco não identificado'}: {node.item.motivo_encerramento ?? '--'}
            </p>
          ))}
        </div>
      )}
    </section>
  )
}
