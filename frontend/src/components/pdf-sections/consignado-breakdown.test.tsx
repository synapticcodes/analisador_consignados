import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { ConsignadoBreakdown } from '@/components/pdf-sections/consignado-breakdown'
import type { ConsignadoLineDetail } from '@/types/api'

describe('ConsignadoBreakdown', () => {
  it('exibe simulação por linha quando prazo está disponível', () => {
    const lines: ConsignadoLineDetail[] = [
      {
        descricao: 'EMPREST BCO OFICIAL - BRB CFI',
        rubrica: '095',
        prazo: 84,
        valor_cent: 3664,
      },
    ]

    render(<ConsignadoBreakdown lines={lines} />)

    expect(
      screen.getByText('Simulação por linha considerando redução de 75% na parcela mensal.')
    ).toBeInTheDocument()
    expect(
      screen.getByText('Quantidade estimada de parcelas:')
    ).toBeInTheDocument()
    expect(screen.getByText('84')).toBeInTheDocument()
    expect(screen.getByText((content) => content.includes('3.077,76'))).toBeInTheDocument()
    expect(screen.getByText((content) => content.includes('9,16'))).toBeInTheDocument()
  })

  it('mostra fallback quando prazo não consta no documento', () => {
    const lines: ConsignadoLineDetail[] = [
      {
        descricao: 'EMPREST BCO PRIVADOS - PRB',
        rubrica: null,
        valor_cent: 41700,
      },
    ]

    render(<ConsignadoBreakdown lines={lines} />)

    expect(
      screen.getByText((content) => content.includes('Quantidade estimada de parcelas:'))
    ).toBeInTheDocument()
    expect(screen.getAllByText('não consta').length).toBeGreaterThan(0)
  })

  it('suporta página de continuação sem total e com numeração contínua', () => {
    const lines: ConsignadoLineDetail[] = [
      {
        descricao: 'EMPREST BCO PRIVADOS - PAN',
        rubrica: '051',
        prazo: 51,
        valor_cent: 65925,
      },
    ]

    render(
      <ConsignadoBreakdown
        lines={lines}
        title="Linhas do Contracheque (continuação)"
        showTotal={false}
        itemOffset={5}
      />
    )

    expect(screen.getByText('Linhas do Contracheque (continuação)')).toBeInTheDocument()
    expect(screen.getByText('Empréstimo 6')).toBeInTheDocument()
    expect(screen.queryByText('Total consignados')).not.toBeInTheDocument()
  })

  it('renderiza resumo geral consolidado com totais finais e mensais', () => {
    const lines: ConsignadoLineDetail[] = [
      {
        descricao: 'EMPREST BCO OFICIAL - BRB CFI',
        rubrica: '095',
        prazo: 84,
        valor_cent: 3664,
      },
      {
        descricao: 'EMPREST BCO PRIVADOS - PAN',
        rubrica: '051',
        prazo: 51,
        valor_cent: 65925,
      },
    ]

    render(
      <ConsignadoBreakdown
        lines={lines}
        showConsolidatedSummary
        summaryLines={lines}
      />
    )

    expect(screen.getByText('Resumo geral consolidado')).toBeInTheDocument()
    expect(
      screen.getByText((content) =>
        content.includes(
          'Valor total que o cliente pagaria ao final de todos os empréstimos mantendo os contratos atuais:'
        )
      )
    ).toBeInTheDocument()
    expect(screen.getByText((content) => content.includes('36.699,51'))).toBeInTheDocument()
    expect(screen.getByText((content) => content.includes('9.174,75'))).toBeInTheDocument()
    expect(screen.getByText((content) => content.includes('27.524,76'))).toBeInTheDocument()
    expect(screen.getAllByText((content) => content.includes('695,89')).length).toBeGreaterThan(0)
    expect(screen.getAllByText((content) => content.includes('173,97')).length).toBeGreaterThan(0)
    expect(screen.getAllByText((content) => content.includes('521,92')).length).toBeGreaterThan(0)
  })
})
