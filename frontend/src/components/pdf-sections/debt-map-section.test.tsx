import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { DebtMapSection } from '@/components/pdf-sections/debt-map-section'

describe('DebtMapSection', () => {
  it('agrupa contratos e linhas de consignado por instituição e mostra indicador de taxa', () => {
    render(
      <DebtMapSection
        contracts={[
          {
            id: 'c1',
            lender_name: 'Banco XPTO',
            contract_id: '1',
            parcela_cent: 20000,
            parcelas_restantes: 12,
            valor_total_cent: 240000,
            taxa_juros: '1,40%',
            status: 'ATIVO',
            cet_mensal: null,
            cet_anual: null,
            iof_cent: null,
            valor_emprestado_cent: null,
          },
        ]}
        consignadoLines={[
          {
            descricao: 'DESCONTO CONSIGNADO SEM BANCO',
            rubrica: '123',
            valor_cent: 4000,
          },
        ]}
      />
    )

    expect(screen.getByText('Banco XPTO')).toBeInTheDocument()
    expect(screen.getByText('Contracheque (sem banco identificado)')).toBeInTheDocument()
    expect(screen.getByText(/Taxa 1,40% \(baixo\)/)).toBeInTheDocument()
  })
})
