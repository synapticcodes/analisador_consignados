import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { DebtMapSection } from '@/components/pdf-sections/debt-map-section'

describe('DebtMapSection', () => {
  it('agrupa contratos e linhas de consignado por instituição e mostra comprometimento do salário', () => {
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
        salarioLiquidoCent={100000}
      />
    )

    expect(screen.getByText('Banco XPTO')).toBeInTheDocument()
    expect(screen.getByText('Contracheque (sem banco identificado)')).toBeInTheDocument()
    expect(screen.getByText('Comprometimento do salário: 20,0%')).toBeInTheDocument()
    expect(screen.getByText('Comprometimento do salário: 4,0%')).toBeInTheDocument()
  })

  it('mostra comprometimento N/D quando salário líquido não está disponível', () => {
    render(
      <DebtMapSection
        contracts={[
          {
            id: 'c2',
            lender_name: 'Banco Estimado',
            contract_id: '2',
            parcela_cent: 10000,
            parcelas_restantes: 12,
            valor_total_cent: null,
            taxa_juros: null,
            status: 'ATIVO',
            cet_mensal: null,
            cet_anual: null,
            iof_cent: null,
            valor_emprestado_cent: 100000,
          },
        ]}
        consignadoLines={[]}
      />
    )

    expect(screen.getByText('Banco Estimado')).toBeInTheDocument()
    expect(screen.getByText('Comprometimento do salário: N/D')).toBeInTheDocument()
  })

  it('calcula comprometimento para banco sem taxa quando há salário líquido', () => {
    render(
      <DebtMapSection
        contracts={[
          {
            id: 'c3',
            lender_name: 'Banco Fallback',
            contract_id: '3',
            parcela_cent: 20000,
            parcelas_restantes: null,
            valor_total_cent: null,
            taxa_juros: null,
            status: 'ATIVO',
            cet_mensal: null,
            cet_anual: null,
            iof_cent: null,
            valor_emprestado_cent: null,
          },
        ]}
        consignadoLines={[]}
        salarioLiquidoCent={500000}
      />
    )

    expect(screen.getByText('Banco Fallback')).toBeInTheDocument()
    expect(screen.getByText('Comprometimento do salário: 4,0%')).toBeInTheDocument()
  })

  it('calcula comprometimento para banco vindo apenas do contracheque', () => {
    render(
      <DebtMapSection
        contracts={[]}
        consignadoLines={[
          {
            descricao: 'EMPREST BCO PRIVADOS - PAN',
            rubrica: '086',
            valor_cent: 15000,
          },
        ]}
        salarioLiquidoCent={300000}
      />
    )

    expect(screen.getByText('Banco PAN')).toBeInTheDocument()
    expect(screen.getByText('Comprometimento do salário: 5,0%')).toBeInTheDocument()
  })
})
