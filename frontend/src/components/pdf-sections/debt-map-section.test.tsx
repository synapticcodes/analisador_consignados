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

  it('mostra comprometimento N/D quando salário/benefício não estão disponíveis', () => {
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
    expect(screen.getByText('Comprometimento do benefício: N/D')).toBeInTheDocument()
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

  it('usa benefício bruto no extrato quando salário não se aplica', () => {
    render(
      <DebtMapSection
        contracts={[
          {
            id: 'c4',
            lender_name: 'Banco BMG',
            contract_id: '4',
            parcela_cent: 20000,
            parcelas_restantes: 12,
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
        salarioLiquidoCent={0}
        beneficioBrutoCent={151800}
        consignadoMensalCent={83490}
      />
    )

    expect(screen.getByText('Comprometimento do benefício: 13,2%')).toBeInTheDocument()
    expect(
      screen.getByText('Participação no consignado identificado: 24,0%')
    ).toBeInTheDocument()
  })

  it('exibe reconciliação entre consignado identificado e total de descontos', () => {
    render(
      <DebtMapSection
        contracts={[]}
        consignadoLines={[
          {
            descricao: 'EMPREST BCO PRIVADOS - PAN',
            rubrica: '086',
            valor_cent: 464130,
          },
        ]}
        salarioLiquidoCent={639688}
        consignadoMensalCent={464130}
        totalDescontosCent={866898}
      />
    )

    expect(screen.getByText('Reconciliação dos descontos')).toBeInTheDocument()
    expect(
      screen.getByText('Consignado identificado (linhas do contracheque)')
    ).toBeInTheDocument()
    expect(screen.getByText('Outros descontos (não consignados)')).toBeInTheDocument()
    expect(screen.getAllByText(/4\.641,30/).length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText(/4\.027,68/)).toBeInTheDocument()
    expect(screen.getByText(/8\.668,98/)).toBeInTheDocument()
  })

  it('oculta reconciliação quando total de descontos é zero ou não aplicável', () => {
    render(
      <DebtMapSection
        contracts={[]}
        consignadoLines={[
          {
            descricao: 'EMPREST BCO PRIVADOS - PAN',
            rubrica: '086',
            valor_cent: 77345,
          },
        ]}
        consignadoMensalCent={77345}
        totalDescontosCent={0}
      />
    )

    expect(screen.queryByText('Reconciliação dos descontos')).not.toBeInTheDocument()
    expect(screen.getByText('Banco PAN')).toBeInTheDocument()
  })

  it('não permite valor negativo em outros descontos quando consignado excede total', () => {
    render(
      <DebtMapSection
        contracts={[]}
        consignadoLines={[
          {
            descricao: 'EMPREST BCO PRIVADOS - PAN',
            rubrica: '086',
            valor_cent: 77345,
          },
        ]}
        consignadoMensalCent={77345}
        totalDescontosCent={50000}
      />
    )

    expect(screen.getByText('Reconciliação dos descontos')).toBeInTheDocument()
    expect(screen.getByText('Outros descontos (não consignados)')).toBeInTheDocument()
    expect(screen.queryByText(/-R\$/)).not.toBeInTheDocument()
  })

  it('permite renderizar página de continuação sem reconciliação via offset/limite', () => {
    render(
      <DebtMapSection
        contracts={[
          {
            id: 'a',
            lender_name: 'Banco A',
            contract_id: '1',
            parcela_cent: 30000,
            parcelas_restantes: 12,
            valor_total_cent: 100000,
            taxa_juros: null,
            status: 'ATIVO',
            cet_mensal: null,
            cet_anual: null,
            iof_cent: null,
            valor_emprestado_cent: null,
          },
          {
            id: 'b',
            lender_name: 'Banco B',
            contract_id: '2',
            parcela_cent: 20000,
            parcelas_restantes: 12,
            valor_total_cent: 100000,
            taxa_juros: null,
            status: 'ATIVO',
            cet_mensal: null,
            cet_anual: null,
            iof_cent: null,
            valor_emprestado_cent: null,
          },
          {
            id: 'c',
            lender_name: 'Banco C',
            contract_id: '3',
            parcela_cent: 10000,
            parcelas_restantes: 12,
            valor_total_cent: 100000,
            taxa_juros: null,
            status: 'ATIVO',
            cet_mensal: null,
            cet_anual: null,
            iof_cent: null,
            valor_emprestado_cent: null,
          },
        ]}
        consignadoLines={[]}
        totalDescontosCent={100000}
        rowOffset={1}
        rowLimit={1}
        title="Mapa de Dívidas por Banco (continuação)"
      />
    )

    expect(screen.getByText('Mapa de Dívidas por Banco (continuação)')).toBeInTheDocument()
    expect(screen.queryByText('Reconciliação dos descontos')).not.toBeInTheDocument()
    expect(screen.getByText('Banco B')).toBeInTheDocument()
    expect(screen.queryByText('Banco A')).not.toBeInTheDocument()
    expect(screen.queryByText('Banco C')).not.toBeInTheDocument()
  })

  it('reconhece aliases de bancos do contracheque (BRB, INBURSA, PRB, SAF)', () => {
    render(
      <DebtMapSection
        contracts={[]}
        consignadoLines={[
          { descricao: 'EMPREST BCO OFICIAL - BRB CFI', rubrica: '095', valor_cent: 10000 },
          { descricao: 'EMPREST BCO PRIVADOS - INBURSA', rubrica: '090', valor_cent: 10000 },
          { descricao: 'EMPREST BCO PRIVADOS - PRB', rubrica: '086', valor_cent: 10000 },
          { descricao: 'EMPREST BCO PRIVADOS - BCO SAF', rubrica: '093', valor_cent: 10000 },
        ]}
        salarioLiquidoCent={200000}
      />
    )

    expect(screen.getByText('Banco BRB')).toBeInTheDocument()
    expect(screen.getByText('Banco INBURSA')).toBeInTheDocument()
    expect(screen.getByText('Banco PRB')).toBeInTheDocument()
    expect(screen.getByText('Banco Safra')).toBeInTheDocument()
    expect(screen.queryByText('Contracheque (sem banco identificado)')).not.toBeInTheDocument()
  })

  it('não cria Banco EMP/Emp05 e reconhece PANAMERICANO corretamente', () => {
    render(
      <DebtMapSection
        contracts={[]}
        consignadoLines={[
          { descricao: 'DIGIO - EMP 1', rubrica: '9068', valor_cent: 126866 },
          { descricao: 'PANAMERICANO-EMP05', rubrica: '5933', valor_cent: 8696 },
          { descricao: 'PANAMERICANO EMP02', rubrica: '5927', valor_cent: 3533 },
          { descricao: 'BANCO PANAMERICANO', rubrica: '5754', valor_cent: 10048 },
        ]}
        salarioLiquidoCent={300000}
      />
    )

    expect(screen.getByText('Banco Digio')).toBeInTheDocument()
    expect(screen.getByText('Banco PANAMERICANO')).toBeInTheDocument()
    expect(screen.queryByText('Banco EMP')).not.toBeInTheDocument()
    expect(screen.queryByText('Banco Emp05')).not.toBeInTheDocument()
  })
})
