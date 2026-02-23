import { formatCurrency, type INSSMarginDetail } from '@/types/api'

type INSSMarginSectionProps = {
  margin: INSSMarginDetail
}

function marginBadge(value: number | null) {
  if (value === null) return <span className="text-slate-500">--</span>
  if (value === 0) return <span className="font-semibold text-red-700">Esgotada</span>
  return <span className="font-semibold text-emerald-700">{formatCurrency(value)}</span>
}

export function INSSMarginSection({ margin }: INSSMarginSectionProps) {
  return (
    <section className="space-y-4">
      <h3 className="text-xl font-semibold text-slate-900">Margem INSS</h3>
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
          <p className="text-slate-500">Base de cálculo</p>
          <p className="text-lg font-semibold text-slate-900">{formatCurrency(margin.base_calculo_cent)}</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
          <p className="text-slate-500">Total comprometido</p>
          <p className="text-lg font-semibold text-slate-900">
            {formatCurrency(margin.total_comprometido_cent)}
          </p>
        </div>
      </div>
      <div className="rounded-xl border border-slate-200 p-4 text-sm">
        <div className="flex items-center justify-between py-1">
          <p>Margem empréstimo</p>
          {marginBadge(margin.margem_emprestimo_cent)}
        </div>
        <div className="flex items-center justify-between py-1">
          <p>Margem RMC</p>
          {marginBadge(margin.margem_rmc_cent)}
        </div>
        <div className="flex items-center justify-between py-1">
          <p>Margem RCC</p>
          {marginBadge(margin.margem_rcc_cent)}
        </div>
      </div>
      {(margin.rmc_banco || margin.rmc_limite_cent !== null || margin.rmc_reservado_cent !== null) && (
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm">
          <p className="mb-2 font-semibold text-slate-900">Detalhes RMC/RCC</p>
          <div className="grid grid-cols-3 gap-2">
            <div>
              <p className="text-slate-500">Banco</p>
              <p className="font-medium text-slate-900">{margin.rmc_banco ?? '--'}</p>
            </div>
            <div>
              <p className="text-slate-500">Limite</p>
              <p className="font-medium text-slate-900">
                {formatCurrency(margin.rmc_limite_cent)}
              </p>
            </div>
            <div>
              <p className="text-slate-500">Reservado</p>
              <p className="font-medium text-slate-900">
                {formatCurrency(margin.rmc_reservado_cent)}
              </p>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}
