import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { TimelineSection } from '@/components/pdf-sections/timeline-section'

describe('TimelineSection', () => {
  it('renderiza conexão rígida de refinanciamento quando critérios são atendidos', () => {
    render(
      <TimelineSection
        historicalContracts={[
          {
            id: 'h1',
            lender_name: 'BANCO AGIBANK SA',
            contract_id: '1523528551',
            data_contratacao: '2025-02-01',
            data_quitacao: '2025-08-01',
            parcela_cent: 53030,
            valor_emprestado_cent: 565907,
            motivo_encerramento: 'Exclusão por refinanciamento',
          },
          {
            id: 'h2',
            lender_name: 'BANCO AGIBANK SA',
            contract_id: '1537518772',
            data_contratacao: '2025-09-01',
            data_quitacao: '2025-09-01',
            parcela_cent: 53030,
            valor_emprestado_cent: 564730,
            motivo_encerramento: 'Exclusão por refinanciamento',
          },
          {
            id: 'h3',
            lender_name: 'BANCO AGIBANK SA',
            contract_id: '1539282128',
            data_contratacao: '2025-10-01',
            data_quitacao: '2026-10-01',
            parcela_cent: 53030,
            valor_emprestado_cent: 559383,
            motivo_encerramento: 'ATIVO (Averbação por refinanciamento)',
          },
        ]}
      />
    )

    expect(screen.getByText('Timeline de Refinanciamentos')).toBeInTheDocument()
    expect(screen.getAllByText('↓ refinanciado para ↓')).toHaveLength(2)
    expect(screen.getByText('Conexões validadas:')).toBeInTheDocument()
    expect(screen.getByText('ATIVO')).toBeInTheDocument()
  })

  it('marca sem evidência de vínculo quando não atende critérios rígidos', () => {
    render(
      <TimelineSection
        historicalContracts={[
          {
            id: 'h1',
            lender_name: 'BANCO AGIBANK SA',
            contract_id: '111',
            data_contratacao: '2025-02-01',
            data_quitacao: '2025-08-01',
            parcela_cent: 53030,
            valor_emprestado_cent: null,
            motivo_encerramento: 'Exclusão por refinanciamento',
          },
          {
            id: 'h2',
            lender_name: 'BANCO BMG S A',
            contract_id: '222',
            data_contratacao: '2025-09-01',
            data_quitacao: '2025-09-01',
            parcela_cent: 53030,
            valor_emprestado_cent: null,
            motivo_encerramento: 'Exclusão por refinanciamento',
          },
        ]}
      />
    )

    expect(screen.getByText('sem conexão validada')).toBeInTheDocument()
    expect(screen.getByText('Sem vínculo ativo identificado')).toBeInTheDocument()
  })

  it('renderiza fatia da timeline por offset/limite e título de continuação', () => {
    render(
      <TimelineSection
        historicalContracts={[
          {
            id: 'h1',
            lender_name: 'BANCO A',
            contract_id: '1',
            data_contratacao: '2025-01-01',
            data_quitacao: '2025-01-01',
            parcela_cent: 10000,
            valor_emprestado_cent: null,
            motivo_encerramento: 'Encerrado',
          },
          {
            id: 'h2',
            lender_name: 'BANCO B',
            contract_id: '2',
            data_contratacao: '2025-02-01',
            data_quitacao: '2025-02-01',
            parcela_cent: 10000,
            valor_emprestado_cent: null,
            motivo_encerramento: 'Encerrado',
          },
          {
            id: 'h3',
            lender_name: 'BANCO C',
            contract_id: '3',
            data_contratacao: '2025-03-01',
            data_quitacao: '2025-03-01',
            parcela_cent: 10000,
            valor_emprestado_cent: null,
            motivo_encerramento: 'Encerrado',
          },
        ]}
        eventOffset={1}
        eventLimit={1}
        title="Timeline de Refinanciamentos (continuação)"
        showSummary={false}
        showReasons={false}
      />
    )

    expect(screen.getByText('Timeline de Refinanciamentos (continuação)')).toBeInTheDocument()
    expect(screen.queryByText('Eventos identificados:')).not.toBeInTheDocument()
    expect(screen.getByText('BANCO B')).toBeInTheDocument()
    expect(screen.queryByText('BANCO A')).not.toBeInTheDocument()
    expect(screen.queryByText('BANCO C')).not.toBeInTheDocument()
  })
})
