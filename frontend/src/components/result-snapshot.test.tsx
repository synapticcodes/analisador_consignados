import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import ResultSnapshot from '@/components/result-snapshot'
import type { FinalResultResponse } from '@/types/api'

function buildResult(overrides: Partial<FinalResultResponse> = {}): FinalResultResponse {
  return {
    job_id: 'job-1',
    competencia_alvo: '2026-02',
    salario_bruto_cent: 500000,
    salario_liquido_cent: 420000,
    total_descontos_cent: 80000,
    divida_mensal_cent: 72000,
    divida_mensal_reduzida_cent: 18000,
    consignado_mensal_cent: 18000,
    divida_total_consignada_cent: 2500000,
    divida_total_reduzida_cent: 625000,
    parcelas_restantes_total: 24,
    alerts: [],
    offers: [],
    loan_contracts: [],
    consignado_lines: [],
    inss_margin: null,
    historical_contracts: [],
    custo_juros_total_cent: null,
    custo_juros_total_brl: null,
    custo_juros_por_contrato: [],
    savings_simulation: null,
    report_layers: {
      confirmado: [],
      indicacao: [],
      nao_disponivel: [],
    },
    ...overrides,
  }
}

describe('ResultSnapshot', () => {
  it('renderiza apenas páginas 1 e 4 quando não há dados de páginas condicionais', () => {
    render(
      <ResultSnapshot
        result={buildResult()}
        dateLabel="06/02/2026"
      />
    )

    const pages = screen.getAllByText(/Página \d de \d/)
    expect(pages).toHaveLength(2)
    expect(screen.queryByText('Contratos Identificados')).not.toBeInTheDocument()
    expect(screen.getByText('Metodologia e Próximos Passos')).toBeInTheDocument()
  })

  it('renderiza páginas condicionais sem exibir ofertas no relatório PDF', () => {
    render(
      <ResultSnapshot
        result={buildResult({
          loan_contracts: [
            {
              id: 'c1',
              lender_name: 'Banco A',
              contract_id: '1',
              parcela_cent: 10000,
              parcelas_restantes: 10,
              valor_total_cent: 100000,
              taxa_juros: '1,40%',
              status: 'ATIVO',
              cet_mensal: null,
              cet_anual: null,
              iof_cent: 1000,
              valor_emprestado_cent: 90000,
            },
          ],
          consignado_lines: [
            {
              descricao: 'EMPR CONSIGNADO',
              descricao_raw: 'EMPREST BCO PRIVADOS - PAN',
              descricao_canonica: 'EMPREST BCO PRIVADOS',
              rubrica: '123',
              valor_cent: 3000,
            },
          ],
          inss_margin: {
            base_calculo_cent: 100000,
            max_comprometimento_cent: 45000,
            total_comprometido_cent: 30000,
            margem_emprestimo_cent: 15000,
            margem_rmc_cent: 0,
            margem_rcc_cent: 5000,
            cet_mensal: null,
            cet_anual: null,
            rmc_banco: null,
            rmc_limite_cent: null,
            rmc_reservado_cent: null,
            evidence: null,
          },
          offers: [
            {
              id: 'o1',
              product_id: 'p',
              kind: 'SUPER',
              payment_method: 'BOLETO',
              entry_value_cent: 0,
              entry_due_days: 0,
              installment_count: 12,
              installment_value_cent: 10000,
              first_payment_days: 30,
              total_value_cent: 120000,
              salary_liquid_used_cent: 420000,
              percent_used: 30,
              text: 'Oferta super',
              created_at: '2026-02-06T00:00:00Z',
            },
            {
              id: 'o2',
              product_id: 'p',
              kind: 'PRINCIPAL',
              payment_method: 'BOLETO',
              entry_value_cent: 0,
              entry_due_days: 0,
              installment_count: 12,
              installment_value_cent: 9000,
              first_payment_days: 30,
              total_value_cent: 108000,
              salary_liquid_used_cent: 420000,
              percent_used: 27,
              text: 'Oferta principal',
              created_at: '2026-02-06T00:00:00Z',
            },
            {
              id: 'o3',
              product_id: 'p',
              kind: 'REDUZIDA',
              payment_method: 'BOLETO',
              entry_value_cent: 0,
              entry_due_days: 0,
              installment_count: 12,
              installment_value_cent: 8000,
              first_payment_days: 30,
              total_value_cent: 96000,
              salary_liquid_used_cent: 420000,
              percent_used: 24,
              text: 'Oferta reduzida',
              created_at: '2026-02-06T00:00:00Z',
            },
          ],
        })}
        dateLabel="06/02/2026"
      />
    )

    const pages = screen.getAllByText(/Página \d de \d/)
    expect(pages.length).toBeGreaterThanOrEqual(4)

    expect(screen.queryByText('REDUZIDA')).not.toBeInTheDocument()
    expect(screen.queryByText('PRINCIPAL')).not.toBeInTheDocument()
    expect(screen.queryByText('SUPER')).not.toBeInTheDocument()
    expect(screen.getByText('EMPREST BCO PRIVADOS - PAN · Rub 123')).toBeInTheDocument()
  })

  it('mantém CTA do WhatsApp na página 4', () => {
    render(
      <ResultSnapshot
        result={buildResult()}
        dateLabel="06/02/2026"
        whatsappCtaText="WhatsApp: (11) 99999-9999"
      />
    )

    expect(
      screen.getByText('Próximo passo: fale com nossa equipe no WhatsApp para análise completa.')
    ).toBeInTheDocument()
    expect(screen.getByText('WhatsApp: (11) 99999-9999')).toBeInTheDocument()
    expect(screen.queryByText('O que ainda não sabemos')).not.toBeInTheDocument()
  })

  it('não renderiza a seção Simulação de Economia no relatório', () => {
    render(
      <ResultSnapshot
        result={buildResult({
          savings_simulation: {
            economia_mensal_total_cent: 978,
            economia_total_restante_cent: 11732,
            taxa_referencia_mensal_percent: '1,5%',
            disclaimer: 'Estimativa para teste',
            contratos: [],
          },
        })}
        dateLabel="06/02/2026"
      />
    )

    expect(screen.queryByText('Simulação de Economia')).not.toBeInTheDocument()
  })

  it('cria páginas de continuação no mapa de dívidas e mostra reconciliação só na primeira', () => {
    const manyContracts = Array.from({ length: 9 }).map((_, index) => ({
      id: `m-${index}`,
      lender_name: `Banco ${index + 1}`,
      contract_id: `${index + 1}`,
      parcela_cent: 9000 - index * 500,
      parcelas_restantes: 12,
      valor_total_cent: 100000,
      taxa_juros: null,
      status: 'ATIVO',
      cet_mensal: null,
      cet_anual: null,
      iof_cent: null,
      valor_emprestado_cent: null,
    }))

    render(
      <ResultSnapshot
        result={buildResult({
          loan_contracts: manyContracts,
          consignado_lines: [],
          total_descontos_cent: 120000,
          consignado_mensal_cent: 77345,
        })}
        dateLabel="06/02/2026"
      />
    )

    expect(screen.getByText('Mapa de Dívidas por Banco')).toBeInTheDocument()
    expect(screen.getByText('Mapa de Dívidas por Banco (continuação)')).toBeInTheDocument()
    expect(screen.getAllByText('Reconciliação dos descontos')).toHaveLength(1)
  })

  it('pagina timeline em múltiplas páginas quando há muitos eventos históricos', () => {
    const manyHistory = Array.from({ length: 12 }).map((_, index) => ({
      id: `h-${index}`,
      lender_name: `Banco Histórico ${index + 1}`,
      contract_id: `${1000 + index}`,
      data_contratacao: `2025-${String((index % 12) + 1).padStart(2, '0')}-01`,
      data_quitacao: `2025-${String((index % 12) + 1).padStart(2, '0')}-01`,
      parcela_cent: 10000,
      valor_emprestado_cent: null,
      motivo_encerramento: 'Encerrado',
    }))

    render(
      <ResultSnapshot
        result={buildResult({
          historical_contracts: manyHistory,
        })}
        dateLabel="06/02/2026"
      />
    )

    expect(screen.getByText('Timeline de Refinanciamentos')).toBeInTheDocument()
    expect(
      screen.getAllByText('Timeline de Refinanciamentos (continuação)').length
    ).toBeGreaterThan(0)
    expect(screen.getAllByText('Eventos identificados:')).toHaveLength(1)
  })

  it('pagina linhas do contracheque sem estourar página quando há muitas linhas', () => {
    const lines = Array.from({ length: 25 }).map((_, index) => ({
      descricao: `EMPREST BCO TESTE ${index + 1}`,
      rubrica: `${100 + index}`,
      valor_cent: 10000 + index,
    }))

    render(
      <ResultSnapshot
        result={buildResult({
          consignado_lines: lines,
        })}
        dateLabel="06/02/2026"
      />
    )

    const pages = screen.getAllByText(/Página \d de \d/)
    expect(pages).toHaveLength(4)
    expect(screen.getByText('EMPREST BCO TESTE 1 · Rub 100')).toBeInTheDocument()
    expect(screen.getByText('EMPREST BCO TESTE 25 · Rub 124')).toBeInTheDocument()
    expect(screen.queryByText(/parte \d de \d/)).not.toBeInTheDocument()
    expect(screen.getByText('Total consignados')).toBeInTheDocument()
  })
})
