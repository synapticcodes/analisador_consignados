import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { ContractsTable } from '@/components/pdf-sections/contracts-table'
import type { LoanContractDetail } from '@/types/api'

const CONTRACTS: LoanContractDetail[] = [
  {
    id: '1',
    lender_name: 'Banco A',
    contract_id: 'A-1',
    parcela_cent: 10000,
    parcelas_restantes: 10,
    valor_total_cent: 100000,
    taxa_juros: '1,40%',
    status: 'ATIVO',
    cet_mensal: '1,60%',
    cet_anual: '21,00%',
    iof_cent: 500,
    valor_emprestado_cent: 80000,
  },
  {
    id: '2',
    lender_name: 'Banco B',
    contract_id: 'B-1',
    parcela_cent: 5000,
    parcelas_restantes: 8,
    valor_total_cent: 40000,
    taxa_juros: '2,10%',
    status: 'ATIVO',
    cet_mensal: null,
    cet_anual: null,
    iof_cent: 300,
    valor_emprestado_cent: 35000,
  },
]

describe('ContractsTable', () => {
  it('exibe colunas de CET/IOF/valor emprestado e totalização', () => {
    render(<ContractsTable contracts={CONTRACTS} />)

    expect(screen.getByText('CET')).toBeInTheDocument()
    expect(screen.getByText('IOF')).toBeInTheDocument()
    expect(screen.getByText('Emprestado')).toBeInTheDocument()
    expect(screen.getByText('R$ 150,00')).toBeInTheDocument()
    expect(screen.getByText('R$ 1.400,00')).toBeInTheDocument()
    expect(screen.getByText('R$ 8,00')).toBeInTheDocument()
    expect(screen.getByText('R$ 1.150,00')).toBeInTheDocument()
  })

  it('exibe "não consta" quando campo contratual não está presente', () => {
    const withoutEvidence: LoanContractDetail[] = [
      {
        ...CONTRACTS[0],
        taxa_juros: null,
        cet_mensal: null,
        cet_anual: null,
        iof_cent: null,
        valor_emprestado_cent: null,
      },
    ]

    render(<ContractsTable contracts={withoutEvidence} />)

    expect(screen.getAllByText('não consta').length).toBeGreaterThan(0)
  })

  it('no total usa dados únicos disponíveis para restantes, taxa e CET', () => {
    const partialContracts: LoanContractDetail[] = [
      {
        id: 'a',
        lender_name: 'Banco Único',
        contract_id: 'U-1',
        parcela_cent: 53030,
        parcelas_restantes: 12,
        valor_total_cent: 559383,
        taxa_juros: '1,80%',
        status: 'ATIVO',
        cet_mensal: '1,81%',
        cet_anual: null,
        iof_cent: null,
        valor_emprestado_cent: null,
      },
      {
        id: 'b',
        lender_name: 'Cartão RMC',
        contract_id: null,
        parcela_cent: 16210,
        parcelas_restantes: null,
        valor_total_cent: 83000,
        taxa_juros: null,
        status: 'ATIVO',
        cet_mensal: null,
        cet_anual: null,
        iof_cent: null,
        valor_emprestado_cent: null,
      },
    ]

    render(<ContractsTable contracts={partialContracts} />)

    const totalRow = screen.getAllByRole('row').at(-1)
    expect(totalRow).toBeTruthy()
    expect(totalRow?.textContent).toContain('Total')
    expect(totalRow?.textContent).toContain('12')
    expect(totalRow?.textContent).toContain('1,80%')
    expect(totalRow?.textContent).toContain('1,81%')
  })
})
