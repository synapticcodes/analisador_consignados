import { forwardRef } from 'react'

import { type FinalResultResponse, formatCurrency } from '@/types/api'

type LegacyResultSnapshotProps = {
  result: FinalResultResponse
  clientName?: string
  clientCpf?: string
  dateLabel: string
}

const LegacyResultSnapshot = forwardRef<HTMLDivElement, LegacyResultSnapshotProps>(
  ({ result, clientName, clientCpf, dateLabel }, ref) => {
    const normalizedName = clientName?.trim()
    const normalizedCpf = clientCpf?.trim()

    const metaItems = []
    if (normalizedName) {
      metaItems.push(`Cliente: ${normalizedName}`)
    }
    if (normalizedCpf) {
      metaItems.push(`CPF: ${normalizedCpf}`)
    }
    metaItems.push(`Data: ${dateLabel}`)

    const formatValue = (value: number | null) =>
      value === null ? '--' : formatCurrency(value)

    const canComputeRelief =
      result.divida_mensal_cent !== null &&
      result.divida_mensal_reduzida_cent !== null

    const reliefValue = canComputeRelief
      ? result.divida_mensal_cent! - result.divida_mensal_reduzida_cent!
      : null
    const reliefAnnualValue = reliefValue !== null ? reliefValue * 12 : null
    const consignadosAtivosCent = result.divida_total_consignada_cent
    const shouldShowConsignadosAtivos =
      consignadosAtivosCent !== null && consignadosAtivosCent > 1_000_000
    const shouldShowDividaTotalReduzida =
      shouldShowConsignadosAtivos && result.divida_total_reduzida_cent !== null

    const missingSalaryInfo =
      result.salario_bruto_cent === null ||
      result.salario_liquido_cent === null ||
      result.total_descontos_cent === null ||
      result.divida_mensal_cent === null ||
      result.divida_mensal_reduzida_cent === null

    return (
      <div
        ref={ref}
        data-pdf-legacy-page="true"
        style={{ width: 1240, height: 1754 }}
        className="flex flex-col bg-white p-16 text-slate-900"
      >
        <header className="space-y-3 border-b border-slate-200 pb-6">
          <div className="flex items-start justify-between gap-6">
            <div>
              <h1 className="text-3xl font-semibold">
                Seu diagnóstico financeiro (antes e depois)
              </h1>
              <p className="mt-2 text-sm text-slate-600">{metaItems.join(' • ')}</p>
            </div>
            <span className="rounded-full bg-slate-100 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
              Relatório
            </span>
          </div>
        </header>

        <main className="flex flex-1 flex-col">
          <div className="mt-10 grid grid-cols-2 gap-8">
            <section className="flex flex-col gap-6 rounded-3xl border border-orange-100 bg-orange-50 p-8">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-orange-700">
                  Antes
                </p>
                <h2 className="mt-2 text-lg font-semibold text-slate-900">
                  Quanto entra e quanto sai
                </h2>
              </div>

              <div className="space-y-4 text-sm">
                <div>
                  <p className="text-slate-700">Salário bruto</p>
                  <p className="text-xl font-semibold text-slate-900">
                    {formatValue(result.salario_bruto_cent)}
                  </p>
                  <p className="text-sm text-slate-600">
                    seu salário total, antes dos descontos
                  </p>
                </div>
                <div>
                  <p className="text-slate-700">Salário líquido</p>
                  <p className="text-xl font-semibold text-slate-900">
                    {formatValue(result.salario_liquido_cent)}
                  </p>
                  <p className="text-sm text-slate-600">o que cai na conta</p>
                </div>
                <div>
                  <p className="text-slate-700">Total de descontos</p>
                  <p className="text-xl font-semibold text-slate-900">
                    {formatValue(result.total_descontos_cent)}
                  </p>
                  <p className="text-sm text-slate-600">
                    descontos do salário (em folha)
                  </p>
                </div>
                {shouldShowConsignadosAtivos && (
                  <div>
                    <p className="text-slate-700">Consignados ativos</p>
                    <p className="text-xl font-semibold text-slate-900">
                      {formatValue(consignadosAtivosCent)}
                    </p>
                    <p className="max-w-xs text-sm leading-snug text-slate-600">
                      total que ainda falta pagar dos seus consignados
                    </p>
                  </div>
                )}
              </div>

              <p className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
                Hoje, seus descontos estão consumindo grande parte do seu salário.
              </p>

              <div className="rounded-2xl border border-orange-100 bg-white p-5">
                <p className="text-sm font-semibold text-slate-900">
                  Desconto mensal atual no salário
                </p>
                <p className="mt-2 text-2xl font-semibold text-slate-900">
                  {formatValue(result.divida_mensal_cent)}
                </p>
                <p className="mt-1 text-sm text-slate-600">
                  estimativa baseada nos descontos informados
                </p>
                <p className="mt-3 text-sm font-semibold text-orange-700">
                  Isso aperta seu orçamento mês a mês.
                </p>
              </div>
            </section>

            <section className="flex flex-col gap-6 rounded-3xl border border-emerald-100 bg-emerald-50 p-8">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
                  Depois
                </p>
                <h2 className="mt-2 text-lg font-semibold text-slate-900">
                  Como ficaria com a redução
                </h2>
              </div>

              <div className="space-y-4 text-sm">
                <div>
                  <p className="text-slate-700">Desconto mensal no salário</p>
                  <p className="text-xl font-semibold text-slate-900">
                    {formatValue(result.divida_mensal_reduzida_cent)}
                  </p>
                  <p className="max-w-xs text-sm leading-snug text-slate-600">
                    valor estimado que passará a ser descontado do seu salário
                  </p>
                </div>
                {shouldShowDividaTotalReduzida && (
                  <div>
                    <p className="text-slate-700">Valor final dos consignados</p>
                    <p className="text-xl font-semibold text-slate-900">
                      {formatValue(result.divida_total_reduzida_cent)}
                    </p>
                    <p className="max-w-xs text-sm leading-snug text-slate-600">
                      valor final estimado após a redução de todos os consignados
                    </p>
                  </div>
                )}
              </div>
            </section>
          </div>

          {canComputeRelief && reliefValue !== null && (
            <section className="mt-8 rounded-3xl border border-emerald-200 bg-emerald-50 p-8">
              <p className="text-sm font-semibold uppercase tracking-wide text-emerald-700">
                Economia mensal estimada
              </p>
              <p className="mt-3 text-4xl font-semibold text-emerald-900">
                {formatCurrency(reliefValue)}
              </p>
              <p className="mt-2 text-sm text-emerald-800">
                {formatCurrency(result.divida_mensal_cent!)} / mês →{' '}
                {formatCurrency(result.divida_mensal_reduzida_cent!)} / mês
              </p>
              <p className="mt-2 text-sm font-semibold text-emerald-900">
                Economia: {formatCurrency(reliefValue)} / mês
              </p>
              {reliefAnnualValue !== null && (
                <p className="mt-1 text-sm text-emerald-900">
                  Economia anual estimada: {formatCurrency(reliefAnnualValue)}
                </p>
              )}
              <p className="mt-3 text-sm text-emerald-900">
                Você pode reduzir a pressão mensal em ~{formatCurrency(reliefValue)}.
              </p>
            </section>
          )}
        </main>

        <footer className="mt-8 border-t border-slate-200 pt-6 text-xs text-slate-600">
          <div className="flex items-start justify-between gap-6">
            <div>
              <p className="font-semibold text-slate-800">Como chegamos aos números</p>
              <p className="mt-1">
                Usamos seu contracheque e o saldo dos consignados para estimar
                o peso mensal e projetar um cenário baseado em acordos já
                obtidos com perfis semelhantes ao seu.
              </p>
              <p className="mt-2">
                Condições e descontos variam conforme credor e perfil.
              </p>
              {missingSalaryInfo && (
                <p className="mt-2 text-slate-500">
                  Para completar salários e descontos, envie contracheque ou
                  informe renda e gasto mensal com dívidas.
                </p>
              )}
            </div>
            <div className="max-w-xs text-right text-slate-500" />
          </div>
        </footer>
      </div>
    )
  }
)

LegacyResultSnapshot.displayName = 'LegacyResultSnapshot'

export default LegacyResultSnapshot
