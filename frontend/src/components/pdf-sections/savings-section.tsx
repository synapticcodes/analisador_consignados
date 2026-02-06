import { formatCurrency, type SavingsSimulationDetail } from '@/types/api'

type SavingsSectionProps = {
  simulation: SavingsSimulationDetail
}

export function SavingsSection({ simulation }: SavingsSectionProps) {
  if (simulation.contratos.length === 0) return null

  return (
    <section className="space-y-3">
      <h3 className="text-xl font-semibold text-slate-900">Simulação de Economia</h3>
      <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm">
        <p>
          Economia mensal total: <strong>{formatCurrency(simulation.economia_mensal_total_cent)}</strong>
        </p>
        <p>
          Economia total restante:{' '}
          <strong>{formatCurrency(simulation.economia_total_restante_cent)}</strong>
        </p>
        <p className="mt-2 text-xs text-slate-600">{simulation.disclaimer}</p>
      </div>
    </section>
  )
}
