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
  it('renderiza exatamente 4 páginas fixas', () => {
    render(
      <ResultSnapshot
        result={buildResult()}
        dateLabel="06/02/2026"
      />
    )

    const pages = screen.getAllByText(/Página \d de 4/)
    expect(pages).toHaveLength(4)
  })

  it('renderiza a capa com título e economia mensal', () => {
    render(
      <ResultSnapshot
        result={buildResult()}
        dateLabel="06/02/2026"
      />
    )

    expect(screen.getByText(/Seu Diagn[óo]stico Financeiro/)).toBeInTheDocument()
    expect(screen.getByText(/Economia mensal estimada/)).toBeInTheDocument()
    expect(screen.getAllByText((content) => content.includes('540,00')).length).toBeGreaterThan(0)
  })

  it('mantém fallback de capa quando faltam dados para estimativa', () => {
    render(
      <ResultSnapshot
        result={buildResult({
          salario_bruto_cent: null,
          salario_liquido_cent: null,
          divida_mensal_cent: null,
          divida_mensal_reduzida_cent: null,
        })}
        dateLabel="06/02/2026"
      />
    )

    expect(screen.getByText(/Economia mensal estimada/)).toBeInTheDocument()
    expect(screen.getByText(/Dados insuficientes para estimar a economia mensal/)).toBeInTheDocument()
    expect(screen.getAllByText('R$ --').length).toBeGreaterThan(0)
  })

  it('troca para contexto de benefício quando salário não se aplica no extrato INSS', () => {
    render(
      <ResultSnapshot
        result={buildResult({
          salario_bruto_cent: 0,
          salario_liquido_cent: 0,
          total_descontos_cent: 0,
          divida_mensal_cent: 0,
          divida_mensal_reduzida_cent: 0,
          divida_total_consignada_cent: 752383,
          inss_margin: {
            base_calculo_cent: 162100,
            max_comprometimento_cent: 72945,
            total_comprometido_cent: 61135,
            margem_emprestimo_cent: 3705,
            margem_rmc_cent: 0,
            margem_rcc_cent: 8105,
            cet_mensal: null,
            cet_anual: null,
            rmc_banco: null,
            rmc_limite_cent: null,
            rmc_reservado_cent: null,
            evidence: null,
          },
        })}
        dateLabel="06/02/2026"
      />
    )

    expect(screen.getAllByText((content) => content.includes('Benefício bruto')).length).toBeGreaterThan(0)
    expect(screen.getAllByText((content) => content.includes('Benefício líquido')).length).toBeGreaterThan(0)
    expect(screen.getAllByText((content) => content.includes('1.621,00')).length).toBeGreaterThan(0)
    expect(screen.queryByText('Salário bruto')).not.toBeInTheDocument()
  })

  it('renderiza página 2 com resumo por banco quando há consignado_lines', () => {
    render(
      <ResultSnapshot
        result={buildResult({
          consignado_lines: [
            {
              descricao: 'EMPR CONSIGNADO',
              descricao_raw: 'EMPREST BCO PRIVADOS - PAN',
              descricao_canonica: 'EMPREST BCO PRIVADOS',
              rubrica: '123',
              valor_cent: 30000,
            },
            {
              descricao: 'EMPR CONSIGNADO BMG',
              descricao_raw: 'EMPREST BCO BMG',
              descricao_canonica: 'EMPREST BCO BMG',
              rubrica: '45',
              valor_cent: 20000,
            },
          ],
        })}
        dateLabel="06/02/2026"
      />
    )

    expect(screen.getByText('Resumo por Banco')).toBeInTheDocument()
    expect(screen.getAllByText('Banco PAN').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Banco BMG').length).toBeGreaterThan(0)
  })

  it('renderiza página 3 com detalhamento por empréstimo', () => {
    render(
      <ResultSnapshot
        result={buildResult({
          consignado_lines: [
            {
              descricao: 'EMPR CONSIGNADO',
              descricao_raw: 'EMPREST BCO PRIVADOS - PAN',
              descricao_canonica: 'EMPREST BCO PRIVADOS',
              rubrica: '123',
              valor_cent: 30000,
            },
          ],
        })}
        dateLabel="06/02/2026"
      />
    )

    expect(screen.getByText(/Detalhamento por Empr[ée]stimo/)).toBeInTheDocument()
    expect(screen.getByText(/Como ler esta tabela/)).toBeInTheDocument()
  })

  it('renderiza página 4 com próximos passos e glossário', () => {
    render(
      <ResultSnapshot
        result={buildResult()}
        dateLabel="06/02/2026"
      />
    )

    expect(screen.getByText(/Pr[óo]ximos Passos/)).toBeInTheDocument()
    expect(screen.getByText(/Gloss[áa]rio/)).toBeInTheDocument()
    expect(screen.getByText(/Credilly Solu[çc][õo]es Financeiras Ltda/)).toBeInTheDocument()
  })

  it('header aparece em todas as páginas', () => {
    render(
      <ResultSnapshot
        result={buildResult()}
        dateLabel="06/02/2026"
      />
    )

    const headers = screen.getAllByText(/Diagn[óo]stico Financeiro/)
    // At least 4 (one header bar per page) + cover title
    expect(headers.length).toBeGreaterThanOrEqual(4)
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

  it('usa fallback de loan_contracts quando consignado_lines está vazio', () => {
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
          consignado_lines: [],
        })}
        dateLabel="06/02/2026"
      />
    )

    expect(screen.getAllByText('Banco A').length).toBeGreaterThan(0)
    expect(screen.getByText('Resumo por Banco')).toBeInTheDocument()
  })

  it('não inclui contratos RMC/RCC na listagem de bancos', () => {
    render(
      <ResultSnapshot
        result={buildResult({
          loan_contracts: [
            {
              id: 'n-1',
              lender_name: 'Banco Extrato 1',
              contract_id: '301',
              parcela_cent: 10000,
              parcelas_restantes: 12,
              valor_total_cent: 0,
              taxa_juros: null,
              status: 'ATIVO',
              cet_mensal: null,
              cet_anual: null,
              iof_cent: null,
              valor_emprestado_cent: null,
            },
            {
              id: 'rmc-1',
              lender_name: 'Cartão RMC',
              contract_id: 'RMC-999',
              parcela_cent: 9000,
              parcelas_restantes: 12,
              valor_total_cent: 0,
              taxa_juros: null,
              status: 'ATIVO',
              cet_mensal: null,
              cet_anual: null,
              iof_cent: null,
              valor_emprestado_cent: null,
            },
          ],
          consignado_lines: [],
        })}
        dateLabel="06/02/2026"
      />
    )

    expect(screen.getAllByText('Banco Extrato 1').length).toBeGreaterThan(0)
    expect(screen.queryByText('Cartão RMC')).not.toBeInTheDocument()
  })

  it('troca textos de contracheque para extrato INSS quando o relatório é extrato-only', () => {
    render(
      <ResultSnapshot
        result={buildResult({
          consignado_lines: [],
          inss_margin: {
            base_calculo_cent: 151800,
            max_comprometimento_cent: 68310,
            total_comprometido_cent: 61135,
            margem_emprestimo_cent: 0,
            margem_rmc_cent: 0,
            margem_rcc_cent: 0,
            cet_mensal: null,
            cet_anual: null,
            rmc_banco: 'BMG',
            rmc_limite_cent: 138700,
            rmc_reservado_cent: 7590,
            evidence: null,
          },
          loan_contracts: [
            {
              id: 'c1',
              lender_name: 'Banco BMG',
              contract_id: '1',
              parcela_cent: 12000,
              parcelas_restantes: 10,
              valor_total_cent: 120000,
              taxa_juros: null,
              status: 'ATIVO',
              cet_mensal: null,
              cet_anual: null,
              iof_cent: null,
              valor_emprestado_cent: null,
            },
          ],
        })}
        dateLabel="06/02/2026"
      />
    )

    expect(screen.getAllByText(/extrato INSS/i).length).toBeGreaterThan(0)
    expect(screen.queryByText(/identificados no seu contracheque/i)).not.toBeInTheDocument()
  })

  it('oculta cards de totais finais na página 2 quando nenhuma linha tem prazo', () => {
    render(
      <ResultSnapshot
        result={buildResult({
          consignado_lines: [
            {
              descricao: 'FUPRES',
              descricao_raw: 'FUPRES',
              descricao_canonica: 'FUPRES',
              rubrica: '9014',
              prazo: null,
              valor_cent: 408366,
            },
            {
              descricao: 'PANAMERICANO-EMP05',
              descricao_raw: 'PANAMERICANO-EMP05',
              descricao_canonica: 'PANAMERICANO',
              rubrica: '5933',
              prazo: null,
              valor_cent: 8696,
            },
          ],
        })}
        dateLabel="06/02/2026"
      />
    )

    expect(screen.queryByText('Total mantendo contratos')).not.toBeInTheDocument()
    expect(screen.queryByText('Total com nossos serviços')).not.toBeInTheDocument()
    expect(screen.queryByText('Economia total projetada')).not.toBeInTheDocument()
    expect(
      screen.getByText(/Totais finais n[ãa]o exibidos porque o documento n[ãa]o informa prazo/)
    ).toBeInTheDocument()
  })
})
