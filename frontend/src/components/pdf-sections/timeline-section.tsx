import type { HistoricalContractDetail } from '@/types/api'

type TimelineSectionProps = {
  historicalContracts: HistoricalContractDetail[]
}

function getYearFromIsoDate(value: string | null): number | null {
  if (!value) return null
  const [year] = value.split('-')
  const parsed = Number(year)
  return Number.isNaN(parsed) ? null : parsed
}

export function TimelineSection({ historicalContracts }: TimelineSectionProps) {
  if (historicalContracts.length === 0) return null

  const ordered = [...historicalContracts].sort((a, b) =>
    (a.data_contratacao ?? '').localeCompare(b.data_contratacao ?? '')
  )
  const validYears = ordered.flatMap((item) => {
    const start = getYearFromIsoDate(item.data_contratacao)
    const end = getYearFromIsoDate(item.data_quitacao)
    return [start, end].filter((year): year is number => year !== null)
  })
  if (validYears.length === 0) return null

  const minYear = Math.min(...validYears)
  const maxYear = Math.max(...validYears)
  const years = Array.from({ length: maxYear - minYear + 1 }, (_, index) => minYear + index)

  return (
    <section className="space-y-3">
      <h3 className="text-xl font-semibold text-slate-900">Timeline de Refinanciamentos</h3>
      <div className="overflow-hidden rounded-lg border border-slate-200 text-xs">
        <div
          className="grid bg-slate-100 font-medium text-slate-700"
          style={{ gridTemplateColumns: `180px repeat(${years.length}, minmax(0, 1fr))` }}
        >
          <div className="border-r border-slate-200 px-3 py-2">Contrato</div>
          {years.map((year) => (
            <div key={`header-${year}`} className="border-r border-slate-200 px-2 py-2 text-center last:border-r-0">
              {year}
            </div>
          ))}
        </div>

        {ordered.map((item) => {
          const startYear = getYearFromIsoDate(item.data_contratacao)
          const endYear = getYearFromIsoDate(item.data_quitacao) ?? startYear
          return (
            <div
              key={item.id}
              className="grid border-t border-slate-200"
              style={{ gridTemplateColumns: `180px repeat(${years.length}, minmax(0, 1fr))` }}
            >
              <div className="border-r border-slate-200 px-3 py-2">
                <p className="font-medium text-slate-900">
                  {item.lender_name ?? 'Banco não identificado'}
                </p>
                <p className="text-slate-600">
                  {item.data_contratacao ?? '--'} a {item.data_quitacao ?? '--'}
                </p>
              </div>

              {years.map((year) => {
                const active =
                  startYear !== null &&
                  endYear !== null &&
                  year >= startYear &&
                  year <= endYear
                return (
                  <div
                    key={`${item.id}-${year}`}
                    className="border-r border-slate-100 px-1 py-2 last:border-r-0"
                  >
                    <div
                      className={`h-4 rounded ${
                        active ? 'bg-slate-700' : 'bg-slate-100'
                      }`}
                    />
                  </div>
                )
              })}
            </div>
          )
        })}
      </div>

      {ordered.length > 1 && (
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-700">
          <p className="font-medium text-slate-900">Conexões de refinanciamento</p>
          {ordered.slice(1).map((current, index) => (
            <p key={`${current.id}-connection`} className="mt-1">
              {ordered[index].lender_name ?? 'Banco não identificado'} →{' '}
              {current.lender_name ?? 'Banco não identificado'}
            </p>
          ))}
        </div>
      )}

      {ordered.some((item) => item.motivo_encerramento) && (
        <div className="rounded-lg border border-slate-200 bg-white p-3 text-xs text-slate-600">
          {ordered.map((item) => (
            <p key={`${item.id}-reason`}>
              {item.lender_name ?? 'Banco não identificado'}: {item.motivo_encerramento ?? '--'}
            </p>
          ))}
        </div>
      )}
    </section>
  )
}
