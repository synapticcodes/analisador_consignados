import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { BankSummaryPage } from '@/components/pdf-sections/bank-summary-page'
import type { BankGroup, ConsolidatedSummary } from '@/components/pdf-sections/pdf-utils'

describe('BankSummaryPage', () => {
  it('exibe disclaimer dinâmico abaixo dos 3 cards com os dados reais dos cálculos', () => {
    const bankGroups: BankGroup[] = [
      {
        banco: 'Banco PAN',
        contratos: 10,
        parcelaAtualCent: 200000,
        novaParcelaCent: 50000,
        economiaCent: 150000,
        percentSalario: 8.3,
      },
      {
        banco: 'Banco PRB',
        contratos: 7,
        parcelaAtualCent: 148130,
        novaParcelaCent: 37030,
        economiaCent: 111100,
        percentSalario: 7.4,
      },
    ]

    const consolidatedSummary: ConsolidatedSummary = {
      totalAtualFinalCent: 37357907,
      totalComReducaoFinalCent: 9537907,
      economiaTotalFinalCent: 27820000,
      totalParcelasMensaisAtuaisCent: 348130,
      totalParcelasMensaisReducaoCent: 87030,
      economiaMensalParcelasCent: 27820,
      linhasSemPrazo: 0,
    }

    render(
      <BankSummaryPage
        bankGroups={bankGroups}
        consolidatedSummary={consolidatedSummary}
      />
    )

    expect(screen.getByText('Como chegamos nesse valor:')).toBeInTheDocument()
    expect(screen.getByText(/Seus 17 contratos somam/)).toBeInTheDocument()
    expect(screen.getByText(/Com a revisão judicial, a projeção é de/)).toBeInTheDocument()
    expect(screen.getByText(/Isso representa uma economia de/)).toBeInTheDocument()
    expect(screen.getByText(/x ~1000 meses =/)).toBeInTheDocument()
    expect(screen.getByText('15,7%')).toBeInTheDocument()
  })

  it('oculta os 3 cards e o disclaimer quando não há base de prazo para projeção final', () => {
    const bankGroups: BankGroup[] = [
      {
        banco: 'Banco PAN',
        contratos: 2,
        parcelaAtualCent: 50000,
        novaParcelaCent: 12500,
        economiaCent: 37500,
        percentSalario: 5,
      },
    ]

    const consolidatedSummary: ConsolidatedSummary = {
      totalAtualFinalCent: 0,
      totalComReducaoFinalCent: 0,
      economiaTotalFinalCent: 0,
      totalParcelasMensaisAtuaisCent: 50000,
      totalParcelasMensaisReducaoCent: 12500,
      economiaMensalParcelasCent: 37500,
      linhasSemPrazo: 2,
    }

    render(
      <BankSummaryPage
        bankGroups={bankGroups}
        consolidatedSummary={consolidatedSummary}
      />
    )

    expect(screen.queryByText('Como chegamos nesse valor:')).not.toBeInTheDocument()
    expect(screen.queryByText('Total mantendo contratos')).not.toBeInTheDocument()
    expect(
      screen.getByText(/Totais finais não exibidos porque o documento não informa prazo de parcelas\./)
    ).toBeInTheDocument()
  })
})
