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
      screen.getByText(/Nova parcela calculada com base na projeção de revisão contratual/)
    ).toBeInTheDocument()
  })
})
