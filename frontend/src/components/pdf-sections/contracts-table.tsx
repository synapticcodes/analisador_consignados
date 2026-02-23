import { formatCurrency, type LoanContractDetail } from '@/types/api'

type ContractsTableProps = {
  contracts: LoanContractDetail[]
}

export function ContractsTable({ contracts }: ContractsTableProps) {
  if (contracts.length === 0) return null

  const MISSING_TEXT = 'não consta'
  const TOTAL_FALLBACK_TEXT = '—'
  const ativos = contracts.filter((item) => item.status !== 'QUITADO')
  const quitados = contracts.filter((item) => item.status === 'QUITADO')
  const totalParcela = ativos.reduce((acc, item) => acc + (item.parcela_cent ?? 0), 0)
  const totalSaldo = ativos.reduce((acc, item) => acc + (item.valor_total_cent ?? 0), 0)
  const restantesValues = ativos
    .map((item) => item.parcelas_restantes)
    .filter((value): value is number => value !== null && value !== undefined)
  const totalRestantes = restantesValues.length > 0 ? restantesValues.reduce((acc, value) => acc + value, 0) : null
  const iofContracts = ativos.filter((item) => item.iof_cent !== null)
  const emprestadoContracts = ativos.filter((item) => item.valor_emprestado_cent !== null)
  const totalIof = iofContracts.reduce((acc, item) => acc + (item.iof_cent ?? 0), 0)
  const totalEmprestado = emprestadoContracts.reduce(
    (acc, item) => acc + (item.valor_emprestado_cent ?? 0),
    0
  )
  const taxaValues = [
    ...new Set(
      ativos
        .map((item) => item.taxa_juros?.trim())
        .filter((value): value is string => Boolean(value))
    ),
  ]
  const cetValues = [
    ...new Set(
      ativos
        .map((item) => item.cet_mensal?.trim() ?? item.cet_anual?.trim() ?? null)
        .filter((value): value is string => Boolean(value))
    ),
  ]
  const totalTaxa = taxaValues.length === 1 ? taxaValues[0] : null
  const totalCet = cetValues.length === 1 ? cetValues[0] : null

  const displayCentValue = (value: number | null | undefined): string =>
    value === null || value === undefined ? MISSING_TEXT : formatCurrency(value)

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
                {displayCentValue(contract.parcela_cent)}
              </td>
              <td className="border border-slate-200 px-3 py-2">
                {contract.parcelas_restantes ?? MISSING_TEXT}
              </td>
              <td className="border border-slate-200 px-3 py-2">
                {displayCentValue(contract.valor_total_cent)}
              </td>
              <td className="border border-slate-200 px-3 py-2">{contract.taxa_juros ?? MISSING_TEXT}</td>
              <td className="border border-slate-200 px-3 py-2">
                {contract.cet_mensal ?? contract.cet_anual ?? MISSING_TEXT}
              </td>
              <td className="border border-slate-200 px-3 py-2">{displayCentValue(contract.iof_cent)}</td>
              <td className="border border-slate-200 px-3 py-2">{displayCentValue(contract.valor_emprestado_cent)}</td>
            </tr>
          ))}
          <tr className="bg-slate-50 font-semibold">
            <td className="border border-slate-200 px-3 py-2">Total</td>
            <td className="border border-slate-200 px-3 py-2">{formatCurrency(totalParcela)}</td>
            <td className="border border-slate-200 px-3 py-2">
              {totalRestantes !== null ? totalRestantes : TOTAL_FALLBACK_TEXT}
            </td>
            <td className="border border-slate-200 px-3 py-2">{formatCurrency(totalSaldo)}</td>
            <td className="border border-slate-200 px-3 py-2">{totalTaxa ?? TOTAL_FALLBACK_TEXT}</td>
            <td className="border border-slate-200 px-3 py-2">{totalCet ?? TOTAL_FALLBACK_TEXT}</td>
            <td className="border border-slate-200 px-3 py-2">
              {iofContracts.length > 0 ? formatCurrency(totalIof) : MISSING_TEXT}
            </td>
            <td className="border border-slate-200 px-3 py-2">
              {emprestadoContracts.length > 0
                ? formatCurrency(totalEmprestado)
                : MISSING_TEXT}
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
