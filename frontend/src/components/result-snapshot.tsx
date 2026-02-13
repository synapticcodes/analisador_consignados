import { forwardRef } from 'react'

import { BankSummaryPage } from '@/components/pdf-sections/bank-summary-page'
import { CoverSummary } from '@/components/pdf-sections/cover-summary'
import { DetailedBreakdownPage } from '@/components/pdf-sections/detailed-breakdown-page'
import { NextStepsPage } from '@/components/pdf-sections/next-steps-page'
import { PdfPageWrapper } from '@/components/pdf-sections/pdf-shared'
import {
  buildConsolidatedSummary,
  buildDetailedLoans,
  groupByBank,
} from '@/components/pdf-sections/pdf-utils'
import { type FinalResultResponse } from '@/types/api'

type ResultSnapshotProps = {
  result: FinalResultResponse
  clientName?: string
  dateLabel: string
  whatsappCtaText?: string
  enablePhase2?: boolean
  enablePhase3?: boolean
}

function normalizeTokenSource(value: string): string {
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toUpperCase()
}

function isMarginCardContract(contract: { lender_name: string | null; contract_id: string | null }): boolean {
  const source = normalizeTokenSource(
    `${contract.lender_name ?? ''} ${contract.contract_id ?? ''}`.trim()
  )
  return /\bRMC\b/.test(source) || /\bRCC\b/.test(source)
}

const TOTAL_PAGES = 4

const ResultSnapshot = forwardRef<HTMLDivElement, ResultSnapshotProps>(
  ({
    result,
    clientName,
    dateLabel,
  }, ref) => {
    // Filter out margin card contracts for consignado-based calculations
    const activeContracts =
      result.loan_contracts?.filter((contract) => {
        const status = contract.status?.toUpperCase() ?? ''
        return status !== 'QUITADO' && status !== 'ENCERRADO' && !isMarginCardContract(contract)
      }) ?? []

    const consignadoLines = result.consignado_lines ?? []

    // Determine salary base for percentage calculations
    const isBenefitContext =
      result.inss_margin?.base_calculo_cent != null &&
      result.inss_margin?.total_comprometido_cent != null &&
      (result.salario_bruto_cent === null || result.salario_bruto_cent === 0) &&
      (result.salario_liquido_cent === null || result.salario_liquido_cent === 0)
    const salarioBrutoCent = isBenefitContext
      ? result.inss_margin?.base_calculo_cent ?? null
      : result.salario_bruto_cent

    // Pre-compute data for all pages
    const bankGroups = groupByBank(consignadoLines, activeContracts, salarioBrutoCent)
    const detailedLoans = buildDetailedLoans(consignadoLines, activeContracts)
    const consolidatedSummary = buildConsolidatedSummary(
      consignadoLines.length > 0 ? consignadoLines : []
    )

    return (
      <div ref={ref}>
        <PdfPageWrapper pageNumber={1} totalPages={TOTAL_PAGES} dateLabel={dateLabel} clientName={clientName}>
          <CoverSummary
            result={result}
            clientName={clientName}
            dateLabel={dateLabel}
            consolidatedSummary={consignadoLines.length > 0 ? consolidatedSummary : null}
          />
        </PdfPageWrapper>

        <PdfPageWrapper pageNumber={2} totalPages={TOTAL_PAGES} dateLabel={dateLabel} clientName={clientName}>
          <BankSummaryPage
            bankGroups={bankGroups}
            consolidatedSummary={consolidatedSummary}
          />
        </PdfPageWrapper>

        <PdfPageWrapper pageNumber={3} totalPages={TOTAL_PAGES} dateLabel={dateLabel} clientName={clientName}>
          <DetailedBreakdownPage loans={detailedLoans} />
        </PdfPageWrapper>

        <PdfPageWrapper pageNumber={4} totalPages={TOTAL_PAGES} dateLabel={dateLabel} clientName={clientName}>
          <NextStepsPage />
        </PdfPageWrapper>
      </div>
    )
  }
)

ResultSnapshot.displayName = 'ResultSnapshot'

export default ResultSnapshot
