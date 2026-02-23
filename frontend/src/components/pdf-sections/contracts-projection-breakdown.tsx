import { formatCurrency, type LoanContractDetail } from '@/types/api'

type ContractsProjectionBreakdownProps = {
  contracts: LoanContractDetail[]
  title?: string
  showTotal?: boolean
  itemOffset?: number
  showConsolidatedSummary?: boolean
  summaryContracts?: LoanContractDetail[]
}

const REDUCED_PERCENT = 25
const MISSING_TEXT = 'não consta'

type ConsolidatedSummary = {
  totalAtualFinalCent: number
  totalComReducaoFinalCent: number
  economiaTotalFinalCent: number
  totalParcelasMensaisAtuaisCent: number
  totalParcelasMensaisReducaoCent: number
  economiaMensalParcelasCent: number
  contratosSemParcela: number
  contratosSemPrazo: number
}

function compactContractLabel(contract: LoanContractDetail, maxLength = 96): string {
  const banco = contract.lender_name?.trim() || 'Banco não identificado'
  const contrato = contract.contract_id?.trim() || '--'
  const base = `${banco} · Contrato ${contrato}`
  if (base.length <= maxLength) return base
  return `${base.slice(0, Math.max(0, maxLength - 1))}…`
}

function normalizeRemainingInstallments(value: number | null): number | null {
  if (typeof value !== 'number' || !Number.isFinite(value) || value <= 0) return null
  return Math.floor(value)
}

function computeReducedInstallment(parcelaCent: number): number {
  return Math.floor((parcelaCent * REDUCED_PERCENT) / 100)
}

function buildConsolidatedSummary(contracts: LoanContractDetail[]): ConsolidatedSummary {
  let totalAtualFinalCent = 0
  let totalComReducaoFinalCent = 0
  let totalParcelasMensaisAtuaisCent = 0
  let totalParcelasMensaisReducaoCent = 0
  let contratosSemParcela = 0
  let contratosSemPrazo = 0

  for (const contract of contracts) {
    const parcelaAtualCent = contract.parcela_cent
    if (parcelaAtualCent === null || parcelaAtualCent === undefined) {
      contratosSemParcela += 1
      continue
    }

    const novaParcelaCent = computeReducedInstallment(parcelaAtualCent)
    totalParcelasMensaisAtuaisCent += parcelaAtualCent
    totalParcelasMensaisReducaoCent += novaParcelaCent

    const parcelasRestantes = normalizeRemainingInstallments(contract.parcelas_restantes)
    if (!parcelasRestantes) {
      contratosSemPrazo += 1
      continue
    }

    totalAtualFinalCent += parcelaAtualCent * parcelasRestantes
    totalComReducaoFinalCent += novaParcelaCent * parcelasRestantes
  }

  return {
    totalAtualFinalCent,
    totalComReducaoFinalCent,
    economiaTotalFinalCent: totalAtualFinalCent - totalComReducaoFinalCent,
    totalParcelasMensaisAtuaisCent,
    totalParcelasMensaisReducaoCent,
    economiaMensalParcelasCent:
      totalParcelasMensaisAtuaisCent - totalParcelasMensaisReducaoCent,
    contratosSemParcela,
    contratosSemPrazo,
  }
}

function ConsolidatedSummaryBlock({ consolidatedSummary }: { consolidatedSummary: ConsolidatedSummary }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3">
      <h4 className="text-sm font-semibold text-slate-900">Resumo geral consolidado</h4>
      <div className="mt-2 space-y-1 text-xs text-slate-700">
        <p>
          Valor total que o cliente pagaria ao final de todos os contratos mantendo os
          contratos atuais:{' '}
          <span className="font-semibold text-red-700">
            {formatCurrency(consolidatedSummary.totalAtualFinalCent)}
          </span>
        </p>
        <p>
          Valor total com nossos serviços:{' '}
          <span className="font-semibold text-emerald-700">
            {formatCurrency(consolidatedSummary.totalComReducaoFinalCent)}
          </span>
        </p>
        <p>
          Valor total de economia:{' '}
          <span className="font-bold text-emerald-800">
            {formatCurrency(consolidatedSummary.economiaTotalFinalCent)}
          </span>
        </p>
        <p>
          Valor total das parcelas mensais atuais:{' '}
          <span className="font-semibold text-red-700">
            {formatCurrency(consolidatedSummary.totalParcelasMensaisAtuaisCent)}
          </span>
        </p>
        <p>
          Valor total das parcelas mensais com nossos serviços:{' '}
          <span className="font-semibold text-emerald-700">
            {formatCurrency(consolidatedSummary.totalParcelasMensaisReducaoCent)}
          </span>
        </p>
        <p>
          Redução mensal no valor das parcelas:{' '}
          <span className="font-bold text-emerald-800">
            {formatCurrency(consolidatedSummary.economiaMensalParcelasCent)}
          </span>
        </p>
      </div>
      {(consolidatedSummary.contratosSemParcela > 0 ||
        consolidatedSummary.contratosSemPrazo > 0) && (
        <p className="mt-2 text-[11px] text-slate-500">
          Contratos sem parcela identificada: {consolidatedSummary.contratosSemParcela}. Contratos sem
          parcelas restantes identificadas: {consolidatedSummary.contratosSemPrazo}. Totais finais
          consideram apenas contratos com parcela e prazo.
        </p>
      )}
    </div>
  )
}

export function ContractsProjectionConsolidatedSummary({
  contracts,
}: {
  contracts: LoanContractDetail[]
}) {
  if (contracts.length === 0) return null
  const consolidatedSummary = buildConsolidatedSummary(contracts)

  return (
    <section className="space-y-2">
      <h3 className="text-xl font-semibold text-slate-900">Projeção dos Contratos (Extrato) - Resumo</h3>
      <ConsolidatedSummaryBlock consolidatedSummary={consolidatedSummary} />
    </section>
  )
}

export function ContractsProjectionBreakdown({
  contracts,
  title = 'Projeção dos Contratos (Extrato)',
  showTotal = true,
  itemOffset = 0,
  showConsolidatedSummary = false,
  summaryContracts,
}: ContractsProjectionBreakdownProps) {
  if (contracts.length === 0) return null

  const totalMensal = contracts.reduce((acc, item) => acc + (item.parcela_cent ?? 0), 0)
  const consolidatedSummary = buildConsolidatedSummary(summaryContracts ?? contracts)

  return (
    <section className="space-y-2">
      <h3 className="text-xl font-semibold text-slate-900">{title}</h3>
      <p className="text-xs text-slate-600">
        Simulação por contrato considerando projeção de redução na parcela mensal.
      </p>

      <div className="space-y-2">
        {contracts.map((contract, index) => {
          const parcelaAtualCent = contract.parcela_cent
          const parcelasRestantes = normalizeRemainingInstallments(contract.parcelas_restantes)
          const novaParcelaCent =
            parcelaAtualCent !== null && parcelaAtualCent !== undefined
              ? computeReducedInstallment(parcelaAtualCent)
              : null
          const valorTotalAtualCent =
            parcelaAtualCent !== null &&
            parcelaAtualCent !== undefined &&
            parcelasRestantes !== null
              ? parcelaAtualCent * parcelasRestantes
              : null
          const valorTotalReduzidoCent =
            novaParcelaCent !== null && parcelasRestantes !== null
              ? novaParcelaCent * parcelasRestantes
              : null
          const valorEconomiaTotalCent =
            valorTotalAtualCent !== null && valorTotalReduzidoCent !== null
              ? valorTotalAtualCent - valorTotalReduzidoCent
              : null
          const displayIndex = itemOffset + index + 1

          return (
            <div
              key={contract.id}
              className="rounded-lg border border-slate-200 bg-slate-50 p-2"
            >
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-semibold text-slate-900">Contrato {displayIndex}</p>
                <p className="rounded-md bg-red-50 px-2 py-0.5 text-sm font-bold text-red-700">
                  {parcelaAtualCent !== null && parcelaAtualCent !== undefined
                    ? formatCurrency(parcelaAtualCent)
                    : MISSING_TEXT}
                </p>
              </div>
              <p className="mt-1 truncate text-xs leading-tight text-slate-600">
                {compactContractLabel(contract)}
              </p>

              <div className="mt-1 grid grid-cols-2 gap-x-2 gap-y-1 text-[11px] leading-tight text-slate-700">
                <div className="rounded-md border border-red-200 bg-red-50 px-2 py-1">
                  <p className="font-semibold text-slate-900">Parcela atual:</p>
                  <p className="font-bold text-red-700">
                    {parcelaAtualCent !== null && parcelaAtualCent !== undefined
                      ? formatCurrency(parcelaAtualCent)
                      : MISSING_TEXT}
                  </p>
                </div>
                <div className="rounded-md border border-slate-200 bg-white px-2 py-1">
                  <p className="font-semibold text-slate-900">Quantidade de parcelas restantes:</p>
                  <p className="font-semibold text-slate-800">
                    {parcelasRestantes ?? MISSING_TEXT}
                  </p>
                </div>
                <div className="rounded-md border border-red-200 bg-red-50 px-2 py-1">
                  <p className="font-semibold text-slate-900">Valor total mantendo o contrato atual:</p>
                  <p className="font-bold text-red-700">
                    {valorTotalAtualCent !== null ? formatCurrency(valorTotalAtualCent) : MISSING_TEXT}
                  </p>
                </div>
                <div className="rounded-md border border-emerald-200 bg-emerald-50 px-2 py-1">
                  <p className="font-semibold text-slate-900">Nova parcela com nossos serviços:</p>
                  <p className="font-bold text-emerald-700">
                    {novaParcelaCent !== null ? formatCurrency(novaParcelaCent) : MISSING_TEXT}
                  </p>
                </div>
                <div className="rounded-md border border-emerald-200 bg-emerald-50 px-2 py-1">
                  <p className="font-semibold text-slate-900">Valor total com a redução:</p>
                  <p className="font-bold text-emerald-700">
                    {valorTotalReduzidoCent !== null ? formatCurrency(valorTotalReduzidoCent) : MISSING_TEXT}
                  </p>
                </div>
                <div className="rounded-md border border-emerald-300 bg-emerald-100 px-2 py-1">
                  <p className="font-semibold text-slate-900">Valor total reduzido neste contrato:</p>
                  <p className="font-extrabold text-emerald-800">
                    {valorEconomiaTotalCent !== null ? formatCurrency(valorEconomiaTotalCent) : MISSING_TEXT}
                  </p>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {showTotal && (
        <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-semibold text-slate-900">
          <p>Total mensal dos contratos</p>
          <p>{formatCurrency(totalMensal)}</p>
        </div>
      )}

      {showConsolidatedSummary && (
        <ConsolidatedSummaryBlock consolidatedSummary={consolidatedSummary} />
      )}
    </section>
  )
}
