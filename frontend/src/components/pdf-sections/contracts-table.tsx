import { formatCurrency, type LoanContractDetail } from '@/types/api'

type ContractsTableProps = {
  contracts: LoanContractDetail[]
}

export function ContractsTable({ contracts }: ContractsTableProps) {
  if (contracts.length === 0) return null

  const ativos = contracts.filter((item) => item.status !== 'QUITADO')
  const quitados = contracts.filter((item) => item.status === 'QUITADO')
  const totalParcela = ativos.reduce((acc, item) => acc + (item.parcela_cent ?? 0), 0)
  const totalSaldo = ativos.reduce((acc, item) => acc + (item.valor_total_cent ?? 0), 0)
  const totalIof = ativos.reduce((acc, item) => acc + (item.iof_cent ?? 0), 0)
  const totalEmprestado = ativos.reduce(
    (acc, item) => acc + (item.valor_emprestado_cent ?? 0),
    0
  )

  return (
    <section className="space-y-4">
      <h2 className="text-2xl font-semibold text-slate-900">Contratos Identificados</h2>
      <table className="w-full border-collapse text-xs">
        <thead>
          <tr className="bg-slate-100 text-left text-slate-700">
            <th className="border border-slate-200 px-3 py-2">Banco</th>
            <th className="border border-slate-200 px-3 py-2">Parcela</th>
            <th className="border border-slate-200 px-3 py-2">Restantes</th>
            <th className="border border-slate-200 px-3 py-2">Saldo</th>
            <th className="border border-slate-200 px-3 py-2">Taxa</th>
            <th className="border border-slate-200 px-3 py-2">CET</th>
            <th className="border border-slate-200 px-3 py-2">IOF</th>
            <th className="border border-slate-200 px-3 py-2">Emprestado</th>
          </tr>
        </thead>
        <tbody>
          {ativos.map((contract) => (
            <tr key={contract.id}>
              <td className="border border-slate-200 px-3 py-2">
                {contract.lender_name || 'Banco não identificado'}
              </td>
              <td className="border border-slate-200 px-3 py-2">
                {formatCurrency(contract.parcela_cent)}
              </td>
              <td className="border border-slate-200 px-3 py-2">{contract.parcelas_restantes ?? '--'}</td>
              <td className="border border-slate-200 px-3 py-2">
                {formatCurrency(contract.valor_total_cent)}
              </td>
              <td className="border border-slate-200 px-3 py-2">{contract.taxa_juros ?? '—'}</td>
              <td className="border border-slate-200 px-3 py-2">
                {contract.cet_mensal ?? contract.cet_anual ?? '—'}
              </td>
              <td className="border border-slate-200 px-3 py-2">
                {formatCurrency(contract.iof_cent)}
              </td>
              <td className="border border-slate-200 px-3 py-2">
                {formatCurrency(contract.valor_emprestado_cent)}
              </td>
            </tr>
          ))}
          <tr className="bg-slate-50 font-semibold">
            <td className="border border-slate-200 px-3 py-2">Total</td>
            <td className="border border-slate-200 px-3 py-2">{formatCurrency(totalParcela)}</td>
            <td className="border border-slate-200 px-3 py-2">—</td>
            <td className="border border-slate-200 px-3 py-2">{formatCurrency(totalSaldo)}</td>
            <td className="border border-slate-200 px-3 py-2">—</td>
            <td className="border border-slate-200 px-3 py-2">—</td>
            <td className="border border-slate-200 px-3 py-2">{formatCurrency(totalIof)}</td>
            <td className="border border-slate-200 px-3 py-2">
              {formatCurrency(totalEmprestado)}
            </td>
          </tr>
        </tbody>
      </table>

      {quitados.length > 0 && (
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-500">Contratos quitados</p>
          <ul className="mt-1 text-sm text-slate-700">
            {quitados.map((item) => (
              <li key={`${item.id}-quitado`}>{item.lender_name || 'Banco não identificado'}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  )
}
