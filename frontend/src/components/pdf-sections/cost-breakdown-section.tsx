import {
  formatCurrency,
  type ContractCostDetail,
} from '@/types/api'

type CostBreakdownSectionProps = {
  totalJurosCent: number | null
  items: ContractCostDetail[]
}

function formatPercentBasisPoints(value: number | null): string {
  if (value === null || value === undefined) return '--'
  return `${(value / 100).toFixed(2).replace('.', ',')}%`
}

export function CostBreakdownSection({
  totalJurosCent,
  items,
}: CostBreakdownSectionProps) {
  if (items.length === 0) return null

  const totalEmprestadoCent = items.reduce(
    (acc, item) => acc + (item.valor_emprestado_cent ?? 0),
    0
  )
  const totalPagarCent = items.reduce(
    (acc, item) => acc + (item.total_a_pagar_cent ?? 0),
    0
  )

  return (
    <section className="space-y-3">
      <h3 className="text-xl font-semibold text-slate-900">Custo Real da Dívida</h3>
      <div className="grid grid-cols-3 gap-2 text-sm">
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
          <p className="text-slate-500">Total emprestado</p>
          <p className="font-semibold text-slate-900">
            {formatCurrency(totalEmprestadoCent)}
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
          <p className="text-slate-500">Total a pagar</p>
          <p className="font-semibold text-slate-900">
            {formatCurrency(totalPagarCent)}
          </p>
        </div>
        <div className="rounded-lg border border-red-200 bg-red-50 p-3">
          <p className="text-red-700">Juros totais</p>
          <p className="font-semibold text-red-900">
            {formatCurrency(totalJurosCent)}
          </p>
        </div>
      </div>

      <div className="rounded-lg border border-slate-200">
        {items.slice(0, 6).map((item, index) => (
          <div
            key={`${item.contract_id ?? 'sem-id'}-${index}`}
            className="grid grid-cols-[1.4fr_1fr_1fr] gap-3 border-b border-slate-100 px-3 py-2 text-xs last:border-b-0"
          >
            <div>
              <p className="font-medium text-slate-900">
                {item.lender_name ?? 'Banco não identificado'}
              </p>
              <p className="text-slate-500">
                Contrato: {item.contract_id ?? '--'} • {item.parcelas_restantes ?? '--'} parcelas
              </p>
            </div>
            <div>
              <p className="text-slate-500">Total a pagar</p>
              <p className="font-semibold text-slate-900">
                {formatCurrency(item.total_a_pagar_cent)}
              </p>
            </div>
            <div>
              <p className="text-slate-500">Juros ({formatPercentBasisPoints(item.percentual_juros_basis_points)})</p>
              <p className="font-semibold text-red-900">
                {formatCurrency(item.custo_juros_cent)}
              </p>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
