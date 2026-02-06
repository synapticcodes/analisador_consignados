import { formatCurrency, type ConsignadoLineDetail } from '@/types/api'

type ConsignadoBreakdownProps = {
  lines: ConsignadoLineDetail[]
}

export function ConsignadoBreakdown({ lines }: ConsignadoBreakdownProps) {
  if (lines.length === 0) return null

  const total = lines.reduce((acc, item) => acc + item.valor_cent, 0)

  return (
    <section className="space-y-3">
      <h3 className="text-xl font-semibold text-slate-900">Linhas do Contracheque</h3>
      <div className="rounded-xl border border-slate-200">
        {lines.map((line, index) => (
          <div
            key={`${line.descricao}-${index}`}
            className="flex items-center justify-between border-b border-slate-100 px-4 py-2 text-sm last:border-b-0"
          >
            <div>
              <p className="font-medium text-slate-900">{line.descricao}</p>
              <p className="text-xs text-slate-500">Rubrica: {line.rubrica ?? '--'}</p>
            </div>
            <p className="font-semibold text-slate-900">{formatCurrency(line.valor_cent)}</p>
          </div>
        ))}
        <div className="flex items-center justify-between bg-slate-50 px-4 py-3 text-sm font-semibold">
          <p>Total consignados</p>
          <p>{formatCurrency(total)}</p>
        </div>
      </div>
    </section>
  )
}
