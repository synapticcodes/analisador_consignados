import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { DetailedBreakdownPage } from '@/components/pdf-sections/detailed-breakdown-page'
import type { DetailedLoan } from '@/components/pdf-sections/pdf-utils'

describe('DetailedBreakdownPage', () => {
  it('exibe coluna de economia total por contrato e totaliza no rodapé', () => {
    const loans: DetailedLoan[] = [
      {
        index: 1,
        banco: 'Banco BRB',
        tipo: 'Consignado',
        parcelaAtualCent: 76955,
        novaParcelaCent: 19238,
        reducaoCent: 57717,
        parcelasEst: 95,
        saldoRestanteCent: 7310725,
        economiaTotalContratoCent: 5483115,
      },
      {
        index: 2,
        banco: 'Banco PRB',
        tipo: 'Consignado',
        parcelaAtualCent: 6200,
        novaParcelaCent: 1550,
        reducaoCent: 4650,
        parcelasEst: null,
        saldoRestanteCent: null,
        economiaTotalContratoCent: null,
      },
    ]

    render(<DetailedBreakdownPage loans={loans} />)

    expect(screen.getByText('Economia total')).toBeInTheDocument()
    expect(screen.getAllByText((content) => content.includes('54.831,15')).length).toBeGreaterThan(0)
    expect(screen.getAllByText('N/D').length).toBeGreaterThan(0)
    expect(
      screen.getByText(/Totais de parcelas estimadas e saldo restante são parciais/)
    ).toBeInTheDocument()
    expect(
      screen.getByText(/Nova parcela calculada com base na projeção de revisão contratual/)
    ).toBeInTheDocument()
  })

  it('soma parcelas estimadas e saldo restante no total quando há dados válidos', () => {
    const loans: DetailedLoan[] = [
      {
        index: 1,
        banco: 'Banco A',
        tipo: 'Contrato',
        parcelaAtualCent: 10000,
        novaParcelaCent: 2500,
        reducaoCent: 7500,
        parcelasEst: 10,
        saldoRestanteCent: 100000,
        economiaTotalContratoCent: 75000,
      },
      {
        index: 2,
        banco: 'Banco B',
        tipo: 'Contrato',
        parcelaAtualCent: 20000,
        novaParcelaCent: 5000,
        reducaoCent: 15000,
        parcelasEst: 5,
        saldoRestanteCent: 100000,
        economiaTotalContratoCent: 75000,
      },
    ]

    render(<DetailedBreakdownPage loans={loans} />)

    expect(screen.getByText('15')).toBeInTheDocument()
    expect(screen.getByText('R$ 2.000,00')).toBeInTheDocument()
    expect(
      screen.queryByText(/Totais de parcelas estimadas e saldo restante são parciais/)
    ).not.toBeInTheDocument()
  })
})
