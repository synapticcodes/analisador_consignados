import { formatCurrency, type FinalResultResponse } from '@/types/api'

type CoverSummaryProps = {
  result: FinalResultResponse
  clientName?: string
  dateLabel: string
}

function metricLabel(label: string, value: number | null) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-xl font-semibold text-slate-900">{formatCurrency(value)}</p>
    </div>
  )
}

export function CoverSummary({ result, clientName, dateLabel }: CoverSummaryProps) {
  const salarioBrutoCent = result.salario_bruto_cent
  const salarioLiquidoCent = result.salario_liquido_cent
  const totalDescontosCent = result.total_descontos_cent
  const dividaMensalCent = result.divida_mensal_cent
  const dividaMensalReduzidaCent = result.divida_mensal_reduzida_cent

  const economiaMensalCent =
    dividaMensalCent !== null && dividaMensalReduzidaCent !== null
      ? Math.max(dividaMensalCent - dividaMensalReduzidaCent, 0)
      : null
  const economiaAnualCent = economiaMensalCent !== null ? economiaMensalCent * 12 : null

  const salarioLiquidoProjetadoCent =
    salarioBrutoCent !== null && dividaMensalReduzidaCent !== null && salarioBrutoCent > 0
      ? Math.max(salarioBrutoCent - dividaMensalReduzidaCent, 0)
      : salarioLiquidoCent !== null && economiaMensalCent !== null
        ? Math.max(salarioLiquidoCent + economiaMensalCent, 0)
        : null

  const salarioLiquidoProjetadoHint =
    salarioBrutoCent !== null && dividaMensalReduzidaCent !== null && salarioBrutoCent > 0
      ? 'estimado com base no salário bruto e no desconto reduzido'
      : 'estimado com base no salário líquido atual e na economia mensal'

  return (
    <section className="flex h-full flex-col">
      <header className="border-b border-slate-200 pb-4">
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-500">Diagnóstico Financeiro</p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-900">
            Seu diagnóstico financeiro (antes e depois)
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            {clientName ? `Cliente: ${clientName} • ` : ''}Data: {dateLabel}
          </p>
        </div>
      </header>

      <div className="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="rounded-xl border border-slate-200 bg-white p-4">
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">
              Antes
            </p>
            <h2 className="mt-2 text-lg font-semibold text-slate-900">Quanto entra e quanto sai</h2>
            <div className="mt-3 space-y-2">
              {metricLabel('Salário bruto', salarioBrutoCent)}
              {metricLabel('Salário líquido', salarioLiquidoCent)}
              <div className="rounded-xl border border-red-200 bg-red-50 p-4">
                <p className="text-xs uppercase tracking-wide text-red-700">Total de descontos</p>
                <p className="mt-1 text-3xl font-semibold text-red-700">
                  {formatCurrency(totalDescontosCent)}
                </p>
                <p className="mt-1 text-xs text-red-700">descontos do salário (em folha)</p>
              </div>
              <div className="rounded-xl border border-red-200 bg-white p-4">
                <p className="text-xs text-slate-600">Desconto mensal atual no salário</p>
                <p className="mt-1 text-4xl font-semibold text-red-700">{formatCurrency(dividaMensalCent)}</p>
                <p className="mt-1 text-xs font-semibold text-red-700">isso aperta seu orçamento mês a mês.</p>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-4">
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-emerald-700">
              Depois
            </p>
            <h2 className="mt-2 text-lg font-semibold text-slate-900">Como ficaria com a redução</h2>
            <div className="mt-3 space-y-2">
              <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4">
                <p className="text-xs uppercase tracking-wide text-emerald-700">Desconto mensal no salário</p>
                <p className="mt-1 text-4xl font-semibold text-emerald-700">
                  {formatCurrency(dividaMensalReduzidaCent)}
                </p>
                <p className="mt-1 text-xs text-emerald-700">
                  valor estimado após redução do comprometimento mensal
                </p>
              </div>

              <div className="rounded-xl border border-emerald-200 bg-white p-4">
                <p className="text-xs text-slate-600">Novo salário líquido estimado</p>
                <p className="mt-1 text-4xl font-semibold text-emerald-700">
                  {formatCurrency(salarioLiquidoProjetadoCent)}
                </p>
                <p className="mt-1 text-xs text-slate-600">{salarioLiquidoProjetadoHint}</p>
              </div>

              <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4">
                <p className="text-xs uppercase tracking-wide text-emerald-700">Diferença mensal</p>
                <p className="mt-1 text-4xl font-semibold text-emerald-700">
                  + {formatCurrency(economiaMensalCent)}
                </p>
                <p className="mt-1 text-xs font-semibold text-emerald-700">
                  seu orçamento volta a respirar.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-100/60 p-4">
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-emerald-800">
            Economia mensal estimada
          </p>
          <p className="mt-1 text-5xl font-semibold text-emerald-800">{formatCurrency(economiaMensalCent)}</p>
          <p className="mt-2 text-sm">
            <span className="font-semibold text-red-700">{formatCurrency(dividaMensalCent)} / mês</span>
            <span className="px-1 text-slate-700">{'->'}</span>
            <span className="font-bold text-emerald-700">
              {formatCurrency(dividaMensalReduzidaCent)} / mês
            </span>
          </p>
          <p className="mt-1 text-sm text-emerald-800">
            Economia anual estimada: {formatCurrency(economiaAnualCent)}
          </p>
          {economiaMensalCent === null && (
            <p className="mt-1 text-xs text-slate-600">Dados insuficientes para estimar a economia mensal.</p>
          )}
        </div>

        <div className="mt-3 rounded-xl border border-slate-200 bg-white p-4">
          <p className="text-sm font-semibold text-slate-900">Como chegamos aos números</p>
          <p className="mt-1 text-xs leading-relaxed text-slate-700">
            Usamos seu contracheque e o saldo dos consignados para estimar o peso mensal e projetar
            um cenário baseado em acordos já obtidos com perfis semelhantes ao seu.
          </p>
          <p className="mt-1 text-xs text-slate-600">Condições e descontos variam conforme credor e perfil.</p>
        </div>
      </div>
    </section>
  )
}
