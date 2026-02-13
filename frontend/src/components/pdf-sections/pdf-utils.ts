import type { ConsignadoLineDetail, LoanContractDetail } from '@/types/api'

// ---------------------------------------------------------------------------
// PDF color palette — inline-style friendly for html-to-image reliability
// ---------------------------------------------------------------------------

export const PDF_COLORS = {
  darkBlue: '#1B2A4A',
  mediumBlue: '#2C4A7C',
  lightBlue: '#E8EFF8',
  accentGreen: '#1A8754',
  lightGreen: '#E6F4ED',
  accentRed: '#C0392B',
  warmGray: '#F7F8FA',
  mediumGray: '#6C757D',
  borderGray: '#DEE2E6',
  textDark: '#212529',
  textSecondary: '#495057',
  highlightYellow: '#FFF8E1',
  highlightYellowBorder: '#FFD54F',
  orangeAccent: '#E67E22',
  lightRed: '#FDEDEC',
  white: '#FFFFFF',
} as const

// ---------------------------------------------------------------------------
// Bank name inference (extracted from debt-map-section.tsx)
// ---------------------------------------------------------------------------

export const BANK_MATCHERS: Array<{ label: string; patterns: RegExp[] }> = [
  { label: 'Banco BRB', patterns: [/\bBRB\b/, /\bBRB\s+CFI\b/] },
  { label: 'Banco INBURSA', patterns: [/\bINBURSA\b/] },
  { label: 'Banco PRB', patterns: [/\bPRB\b/] },
  { label: 'Banco Safra', patterns: [/\bSAFRA\b/, /\bBCO\s+SAF\b/, /\bSAF\b/] },
  { label: 'Banco PANAMERICANO', patterns: [/\bPANAMERICANO\b/] },
  { label: 'Banco PAN', patterns: [/\bPAN\b/] },
  { label: 'Banco SANTANDER', patterns: [/\bSANTANDER\b/] },
  { label: 'Banco BMG', patterns: [/\bBMG\b/] },
  { label: 'Banco BRADESCO', patterns: [/\bBRADESCO\b/] },
  { label: 'Banco ITAU', patterns: [/\bITAU\b/] },
  { label: 'Banco CAIXA', patterns: [/\bCAIXA\b/] },
  { label: 'Banco C6', patterns: [/\bC6\b/] },
  { label: 'Banco AGIBANK', patterns: [/\bAGIBANK\b/] },
  { label: 'Banco DAYCOVAL', patterns: [/\bDAYCOVAL\b/] },
  { label: 'Banco MERCANTIL', patterns: [/\bMERCANTIL\b/] },
  { label: 'Banco BANRISUL', patterns: [/\bBANRISUL\b/] },
  { label: 'Banco NUBANK', patterns: [/\bNUBANK\b/] },
  { label: 'Banco BB', patterns: [/\bBB\b/, /\bBANCO\s+DO\s+BRASIL\b/] },
]

export const GENERIC_TOKENS = new Set([
  'BCO',
  'BANCO',
  'PRIVADO',
  'PRIVADOS',
  'OFICIAL',
  'EMPREST',
  'EMPRESTIMO',
  'EMPR',
  'DESCONTO',
  'CONSIGNADO',
  'SEM',
  'CARTAO',
  'CREDITO',
  'AMORT',
  'OLE',
  'CFI',
])

function isGenericToken(token: string): boolean {
  const upper = token.toUpperCase()
  if (!upper) return true
  if (GENERIC_TOKENS.has(upper)) return true
  if (/^EMP\d*$/.test(upper)) return true
  if (/^EMPR?\d*$/.test(upper)) return true
  if (/^\d+$/.test(upper)) return true
  return false
}

function normalizeDynamicBankLabel(token: string): string {
  const upper = token.toUpperCase().replace(/[^A-Z0-9]/g, '')
  if (!upper) return ''
  if (upper === 'SAF') return 'Safra'
  if (upper.length <= 4) return upper
  return `${upper[0]}${upper.slice(1).toLowerCase()}`
}

export function inferInstitution(line: ConsignadoLineDetail): string {
  const descricao =
    line.descricao_raw?.trim() ||
    line.descricao_canonica?.trim() ||
    line.descricao?.trim() ||
    ''
  const source = `${descricao} ${line.rubrica ?? ''}`.toUpperCase()
  for (const matcher of BANK_MATCHERS) {
    if (matcher.patterns.some((pattern) => pattern.test(source))) {
      return matcher.label
    }
  }

  const bancoMatch = source.match(/\b(?:BCO|BANCO)\s+([A-Z0-9]{2,})\b/)
  if (bancoMatch?.[1] && !isGenericToken(bancoMatch[1])) {
    const normalized = normalizeDynamicBankLabel(bancoMatch[1])
    if (normalized) {
      return `Banco ${normalized}`
    }
  }

  const dynamicTokens = Array.from(source.matchAll(/(?:^|[\s\-\/])([A-Z0-9]{2,})\b/g))
    .map((match) => match[1])
    .filter((token) => token && !isGenericToken(token))
  if (dynamicTokens.length > 0) {
    const normalized = normalizeDynamicBankLabel(dynamicTokens[0] ?? '')
    if (normalized) {
      return `Banco ${normalized}`
    }
  }

  return 'Contracheque (sem banco identificado)'
}

// ---------------------------------------------------------------------------
// Consignado calculations (extracted from consignado-breakdown.tsx)
// ---------------------------------------------------------------------------

const REDUCED_PERCENT = 25

export function parsePrazo(line: ConsignadoLineDetail): number | null {
  if (typeof line.prazo === 'number' && Number.isFinite(line.prazo) && line.prazo > 0) {
    return Math.floor(line.prazo)
  }

  if (line.rubrica) {
    const trimmed = line.rubrica.trim()
    if (/^\d{2,3}$/.test(trimmed)) {
      const parsed = parseInt(trimmed, 10)
      if (parsed > 0 && parsed <= 120) return parsed
    }
  }

  return null
}

export function computeReducedInstallment(parcelaCent: number): number {
  return Math.floor((parcelaCent * REDUCED_PERCENT) / 100)
}

export type ConsolidatedSummary = {
  totalAtualFinalCent: number
  totalComReducaoFinalCent: number
  economiaTotalFinalCent: number
  totalParcelasMensaisAtuaisCent: number
  totalParcelasMensaisReducaoCent: number
  economiaMensalParcelasCent: number
  linhasSemPrazo: number
}

export function buildConsolidatedSummary(lines: ConsignadoLineDetail[]): ConsolidatedSummary {
  let totalAtualFinalCent = 0
  let totalComReducaoFinalCent = 0
  let totalParcelasMensaisAtuaisCent = 0
  let totalParcelasMensaisReducaoCent = 0
  let linhasSemPrazo = 0

  for (const line of lines) {
    const parcelaAtualCent = line.valor_cent
    const parcelaReducaoCent = computeReducedInstallment(parcelaAtualCent)
    totalParcelasMensaisAtuaisCent += parcelaAtualCent
    totalParcelasMensaisReducaoCent += parcelaReducaoCent

    const prazo = parsePrazo(line)
    if (!prazo) {
      linhasSemPrazo += 1
      continue
    }

    totalAtualFinalCent += parcelaAtualCent * prazo
    totalComReducaoFinalCent += parcelaReducaoCent * prazo
  }

  return {
    totalAtualFinalCent,
    totalComReducaoFinalCent,
    economiaTotalFinalCent: totalAtualFinalCent - totalComReducaoFinalCent,
    totalParcelasMensaisAtuaisCent,
    totalParcelasMensaisReducaoCent,
    economiaMensalParcelasCent:
      totalParcelasMensaisAtuaisCent - totalParcelasMensaisReducaoCent,
    linhasSemPrazo,
  }
}

// ---------------------------------------------------------------------------
// New: groupByBank — groups consignado_lines (or loan_contracts fallback)
// ---------------------------------------------------------------------------

export type BankGroup = {
  banco: string
  contratos: number
  parcelaAtualCent: number
  novaParcelaCent: number
  economiaCent: number
  percentSalario: number | null
}

export function groupByBank(
  consignadoLines: ConsignadoLineDetail[],
  loanContracts: LoanContractDetail[],
  salarioBrutoCent: number | null
): BankGroup[] {
  const grouped = new Map<string, { contratos: number; parcelaAtualCent: number }>()

  const lines = consignadoLines.length > 0 ? consignadoLines : null
  if (lines) {
    for (const line of lines) {
      const banco = inferInstitution(line)
      const entry = grouped.get(banco) ?? { contratos: 0, parcelaAtualCent: 0 }
      entry.contratos += 1
      entry.parcelaAtualCent += line.valor_cent
      grouped.set(banco, entry)
    }
  } else {
    for (const contract of loanContracts) {
      const banco = contract.lender_name || 'Banco não identificado'
      const entry = grouped.get(banco) ?? { contratos: 0, parcelaAtualCent: 0 }
      entry.contratos += 1
      entry.parcelaAtualCent += contract.parcela_cent ?? 0
      grouped.set(banco, entry)
    }
  }

  const result: BankGroup[] = []
  for (const [banco, data] of grouped) {
    const novaParcelaCent = computeReducedInstallment(data.parcelaAtualCent)
    const economiaCent = data.parcelaAtualCent - novaParcelaCent
    const percentSalario =
      salarioBrutoCent && salarioBrutoCent > 0
        ? (data.parcelaAtualCent / salarioBrutoCent) * 100
        : null
    result.push({
      banco,
      contratos: data.contratos,
      parcelaAtualCent: data.parcelaAtualCent,
      novaParcelaCent,
      economiaCent,
      percentSalario,
    })
  }

  return result.sort((a, b) => b.parcelaAtualCent - a.parcelaAtualCent)
}

// ---------------------------------------------------------------------------
// New: buildDetailedLoans — individual loan details for Page 3
// ---------------------------------------------------------------------------

export type DetailedLoan = {
  index: number
  banco: string
  tipo: string
  parcelaAtualCent: number
  novaParcelaCent: number
  reducaoCent: number
  parcelasEst: number | null
  saldoRestanteCent: number | null
}

export function buildDetailedLoans(
  consignadoLines: ConsignadoLineDetail[],
  loanContracts: LoanContractDetail[]
): DetailedLoan[] {
  const result: DetailedLoan[] = []

  if (consignadoLines.length > 0) {
    for (let i = 0; i < consignadoLines.length; i++) {
      const line = consignadoLines[i]!
      const banco = inferInstitution(line)
      const parcelaAtualCent = line.valor_cent
      const novaParcelaCent = computeReducedInstallment(parcelaAtualCent)
      const prazo = parsePrazo(line)
      result.push({
        index: i + 1,
        banco,
        tipo: 'Consignado',
        parcelaAtualCent,
        novaParcelaCent,
        reducaoCent: parcelaAtualCent - novaParcelaCent,
        parcelasEst: prazo,
        saldoRestanteCent: prazo ? parcelaAtualCent * prazo : null,
      })
    }
  } else {
    for (let i = 0; i < loanContracts.length; i++) {
      const contract = loanContracts[i]!
      const parcelaAtualCent = contract.parcela_cent ?? 0
      const novaParcelaCent = computeReducedInstallment(parcelaAtualCent)
      const prazo = contract.parcelas_restantes ?? null
      result.push({
        index: i + 1,
        banco: contract.lender_name || 'Banco não identificado',
        tipo: 'Contrato',
        parcelaAtualCent,
        novaParcelaCent,
        reducaoCent: parcelaAtualCent - novaParcelaCent,
        parcelasEst: prazo,
        saldoRestanteCent: prazo ? parcelaAtualCent * prazo : null,
      })
    }
  }

  return result
}

// ---------------------------------------------------------------------------
// New: formatPercent — formats percentage with 1 decimal, pt-BR comma
// ---------------------------------------------------------------------------

export function formatPercent(value: number | null): string {
  if (value === null) return 'N/D'
  return `${value.toFixed(1).replace('.', ',')}%`
}
