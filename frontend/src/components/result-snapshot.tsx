import { forwardRef } from 'react'

import { ConsignadoBreakdown } from '@/components/pdf-sections/consignado-breakdown'
import { CostBreakdownSection } from '@/components/pdf-sections/cost-breakdown-section'
import { ContractsTable } from '@/components/pdf-sections/contracts-table'
import { CoverSummary } from '@/components/pdf-sections/cover-summary'
import {
  buildDebtMapData,
  DebtMapSection,
} from '@/components/pdf-sections/debt-map-section'
import { INSSMarginSection } from '@/components/pdf-sections/inss-margin-section'
import { MethodologyFooter } from '@/components/pdf-sections/methodology-footer'
import {
  buildTimelineData,
  TimelineSection,
} from '@/components/pdf-sections/timeline-section'
import { type FinalResultResponse } from '@/types/api'

type ResultSnapshotProps = {
  result: FinalResultResponse
  clientName?: string
  dateLabel: string
  whatsappCtaText?: string
  enablePhase2?: boolean
  enablePhase3?: boolean
}

const DEBT_MAP_ROWS_PER_PAGE = 6
const TIMELINE_EVENTS_PER_PAGE = 5

function splitInChunks<T>(items: T[], size: number): T[][] {
  if (items.length === 0) return []
  if (size <= 0) return [items]
  const chunks: T[][] = []
  for (let index = 0; index < items.length; index += size) {
    chunks.push(items.slice(index, index + size))
  }
  return chunks
}

function PageWrapper({
  pageNumber,
  totalPages,
  children,
}: {
  pageNumber: number
  totalPages: number
  children: React.ReactNode
}) {
  return (
    <div
      data-pdf-page="true"
      style={{ width: 794, height: 1123 }}
      className="mb-4 flex flex-col bg-white p-10 text-slate-900"
    >
      <div className="min-h-0 flex-1">{children}</div>
      <footer className="mt-4 border-t border-slate-200 pt-3 text-right text-xs text-slate-500">
        Página {pageNumber} de {totalPages}
      </footer>
    </div>
  )
}

const ResultSnapshot = forwardRef<HTMLDivElement, ResultSnapshotProps>(
  ({
    result,
    clientName,
    dateLabel,
    whatsappCtaText = 'WhatsApp: (11) 99999-9999',
    enablePhase2 = true,
    enablePhase3 = true,
  }, ref) => {
    const debtMapData = buildDebtMapData({
      contracts: result.loan_contracts ?? [],
      consignadoLines: result.consignado_lines ?? [],
      consignadoMensalCent: result.consignado_mensal_cent,
      totalDescontosCent: result.total_descontos_cent,
    })
    const timelineData = buildTimelineData(result.historical_contracts ?? [])

    const hasContracts = (result.loan_contracts?.length ?? 0) > 0
    const hasConsignadoLines = (result.consignado_lines?.length ?? 0) > 0
    const hasMargin = result.inss_margin !== null && result.inss_margin !== undefined
    const hasTimeline = enablePhase3 && timelineData.nodes.length > 0
    const hasDebtMap = enablePhase3 && debtMapData.rows.length > 0
    const hasCostBreakdown =
      enablePhase2 && (result.custo_juros_por_contrato?.length ?? 0) > 0
    const hasInsightsCore = hasMargin || hasCostBreakdown
    const debtMapChunks = hasDebtMap
      ? splitInChunks(debtMapData.rows, DEBT_MAP_ROWS_PER_PAGE)
      : []
    const timelineOffsets = hasTimeline
      ? Array.from(
          { length: Math.ceil(timelineData.nodes.length / TIMELINE_EVENTS_PER_PAGE) },
          (_, index) => index * TIMELINE_EVENTS_PER_PAGE
        )
      : []

    const pageDescriptors: Array<{ key: string; render: () => React.ReactNode }> = [
      {
        key: 'p1',
        render: () => <CoverSummary result={result} clientName={clientName} dateLabel={dateLabel} />,
      },
      ...(hasContracts
        ? [
            {
              key: 'contracts',
              render: () => (
                <ContractsTable contracts={result.loan_contracts ?? []} />
              ),
            },
          ]
        : []),
      ...(hasConsignadoLines
        ? [
            {
              key: 'consignado',
              render: () => <ConsignadoBreakdown lines={result.consignado_lines ?? []} />,
            },
          ]
        : []),
      ...(hasInsightsCore
        ? [
            {
              key: 'insights-core',
              render: () => (
                <div className="space-y-5">
                  {hasMargin && result.inss_margin && <INSSMarginSection margin={result.inss_margin} />}
                  {hasCostBreakdown && (
                    <CostBreakdownSection
                      totalJurosCent={result.custo_juros_total_cent ?? null}
                      items={result.custo_juros_por_contrato ?? []}
                    />
                  )}
                </div>
              ),
            },
          ]
        : []),
      ...debtMapChunks.map((_, chunkIndex) => ({
        key: `debt-map-${chunkIndex + 1}`,
        render: () => (
          <DebtMapSection
            contracts={result.loan_contracts ?? []}
            consignadoLines={result.consignado_lines ?? []}
            salarioLiquidoCent={result.salario_liquido_cent}
            totalDescontosCent={result.total_descontos_cent}
            consignadoMensalCent={result.consignado_mensal_cent}
            rowOffset={chunkIndex * DEBT_MAP_ROWS_PER_PAGE}
            rowLimit={DEBT_MAP_ROWS_PER_PAGE}
            title={
              chunkIndex === 0
                ? 'Mapa de Dívidas por Banco'
                : 'Mapa de Dívidas por Banco (continuação)'
            }
            showReconciliationOverride={chunkIndex === 0}
          />
        ),
      })),
      ...timelineOffsets.map((offset, timelineIndex) => ({
        key: `timeline-${timelineIndex + 1}`,
        render: () => (
          <TimelineSection
            historicalContracts={result.historical_contracts ?? []}
            eventOffset={offset}
            eventLimit={TIMELINE_EVENTS_PER_PAGE}
            title={
              timelineIndex === 0
                ? 'Timeline de Refinanciamentos'
                : 'Timeline de Refinanciamentos (continuação)'
            }
            showSummary={timelineIndex === 0}
            showReasons={false}
          />
        ),
      })),
      {
        key: 'p4',
        render: () => <MethodologyFooter whatsappText={whatsappCtaText} />,
      },
    ]

    const totalPages = pageDescriptors.length

    return (
      <div ref={ref}>
        {pageDescriptors.map((page, index) => (
          <PageWrapper key={page.key} pageNumber={index + 1} totalPages={totalPages}>
            {page.render()}
          </PageWrapper>
        ))}
      </div>
    )
  }
)

ResultSnapshot.displayName = 'ResultSnapshot'

export default ResultSnapshot
