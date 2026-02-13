import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { ContractsProjectionBreakdown } from '@/components/pdf-sections/contracts-projection-breakdown'
import type { LoanContractDetail } from '@/types/api'

describe('ContractsProjectionBreakdown', () => {
  it('exibe simulação por contrato com resumo consolidado', () => {
    const contracts: LoanContractDetail[] = [
      {
        id: 'c1',
        lender_name: 'Banco A',
        contract_id: '001',
        parcela_cent: 10000,
        parcelas_restantes: 10,
        valor_total_cent: 100000,
        taxa_juros: null,
        status: 'ATIVO',
        cet_mensal: null,
        cet_anual: null,
        iof_cent: null,
        valor_emprestado_cent: null,
      },
      {
        id: 'c2',
        lender_name: 'Banco B',
        contract_id: '002',
        parcela_cent: 20000,
        parcelas_restantes: 5,
        valor_total_cent: 100000,
        taxa_juros: null,
        status: 'ATIVO',
        cet_mensal: null,
        cet_anual: null,
        iof_cent: null,
        valor_emprestado_cent: null,
      },
    ]

    render(
      <ContractsProjectionBreakdown
        contracts={contracts}
        showConsolidatedSummary
        summaryContracts={contracts}
      />
    )

    expect(screen.getByText('Projeção dos Contratos (Extrato)')).toBeInTheDocument()
    expect(
      screen.getByText('Simulação por contrato considerando redução de 75% na parcela mensal.')
    ).toBeInTheDocument()
    expect(screen.getByText('Total mensal dos contratos')).toBeInTheDocument()
    expect(screen.getAllByText((content) => content.includes('300,00')).length).toBeGreaterThan(0)
    expect(screen.getByText('Resumo geral consolidado')).toBeInTheDocument()
    expect(screen.getAllByText((content) => content.includes('2.000,00')).length).toBeGreaterThan(0)
    expect(screen.getAllByText((content) => content.includes('500,00')).length).toBeGreaterThan(0)
    expect(screen.getAllByText((content) => content.includes('1.500,00')).length).toBeGreaterThan(0)
    expect(screen.getAllByText((content) => content.includes('75,00')).length).toBeGreaterThan(0)
    expect(screen.getAllByText((content) => content.includes('225,00')).length).toBeGreaterThan(0)
  })

  it('mostra não consta quando faltam parcela ou parcelas restantes', () => {
    const contracts: LoanContractDetail[] = [
      {
        id: 'c3',
        lender_name: 'Banco C',
        contract_id: '003',
        parcela_cent: null,
        parcelas_restantes: 12,
        valor_total_cent: null,
        taxa_juros: null,
        status: 'ATIVO',
        cet_mensal: null,
        cet_anual: null,
        iof_cent: null,
        valor_emprestado_cent: null,
      },
      {
        id: 'c4',
        lender_name: 'Banco D',
        contract_id: '004',
        parcela_cent: 12000,
        parcelas_restantes: null,
        valor_total_cent: null,
        taxa_juros: null,
        status: 'ATIVO',
        cet_mensal: null,
        cet_anual: null,
        iof_cent: null,
        valor_emprestado_cent: null,
      },
    ]

    render(
      <ContractsProjectionBreakdown
        contracts={contracts}
        showConsolidatedSummary
        summaryContracts={contracts}
      />
    )

    expect(screen.getAllByText('não consta').length).toBeGreaterThan(0)
    expect(
      screen.getByText((content) => content.includes('Contratos sem parcela identificada: 1'))
    ).toBeInTheDocument()
    expect(
      screen.getByText((content) =>
        content.includes('Contratos sem parcelas restantes identificadas: 1')
      )
    ).toBeInTheDocument()
  })
})
