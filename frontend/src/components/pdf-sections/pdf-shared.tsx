import type { ReactNode } from 'react'
import { PDF_COLORS } from './pdf-utils'

// ---------------------------------------------------------------------------
// PdfHeaderBar — dark-blue top bar on every page
// ---------------------------------------------------------------------------

export function PdfHeaderBar({
  dateLabel,
  clientName,
  clientCpf,
}: {
  dateLabel: string
  clientName?: string
  clientCpf?: string
}) {
  const headerMeta = [clientName, clientCpf ? `CPF: ${clientCpf}` : null, `Data: ${dateLabel}`]
    .filter(Boolean)
    .join('  |  ')

  return (
    <div
      className="flex items-center justify-between px-5 py-2.5"
      style={{ backgroundColor: PDF_COLORS.darkBlue }}
    >
      <span
        className="text-[10px] font-semibold uppercase tracking-widest"
        style={{ color: PDF_COLORS.white }}
      >
        Diagnóstico Financeiro  |  Documento Confidencial
      </span>
      <span className="text-[10px]" style={{ color: 'rgba(255,255,255,0.7)' }}>
        {headerMeta}
      </span>
    </div>
  )
}

// ---------------------------------------------------------------------------
// PdfPageFooter — bottom disclaimer + page number
// ---------------------------------------------------------------------------

export function PdfPageFooter({
  pageNumber,
  totalPages,
}: {
  pageNumber: number
  totalPages: number
}) {
  return (
    <footer
      className="mt-auto px-5 pb-3 pt-2"
      style={{ borderTop: `1px solid ${PDF_COLORS.borderGray}` }}
    >
      <div
        className="flex items-end justify-between text-[8px]"
        style={{ color: PDF_COLORS.mediumGray }}
      >
        <span className="max-w-[70%] leading-tight">
          Este documento é de uso exclusivo do destinatário e contém
          informações confidenciais. A Credilly não se responsabiliza
          por decisões tomadas exclusivamente com base neste relatório.
        </span>
        <span>
          Página {pageNumber} de {totalPages}
        </span>
      </div>
    </footer>
  )
}

// ---------------------------------------------------------------------------
// PdfPageWrapper — full page container (794x1123) with header + footer
// ---------------------------------------------------------------------------

export function PdfPageWrapper({
  pageNumber,
  totalPages = 4,
  dateLabel = '',
  clientName,
  clientCpf,
  children,
}: {
  pageNumber: number
  totalPages?: number
  dateLabel?: string
  clientName?: string
  clientCpf?: string
  children: ReactNode
}) {
  return (
    <div
      data-pdf-page="true"
      style={{ width: 794, height: 1123, backgroundColor: PDF_COLORS.white }}
      className="mb-4 flex flex-col overflow-hidden"
    >
      <PdfHeaderBar dateLabel={dateLabel} clientName={clientName} clientCpf={clientCpf} />
      <div className="min-h-0 flex-1 overflow-hidden px-8 py-5">{children}</div>
      <PdfPageFooter pageNumber={pageNumber} totalPages={totalPages} />
    </div>
  )
}

// ---------------------------------------------------------------------------
// YellowCalloutBox — yellow box with left border (#FFD54F)
// ---------------------------------------------------------------------------

export function YellowCalloutBox({
  title,
  children,
}: {
  title?: string
  children: ReactNode
}) {
  return (
    <div
      className="rounded-sm px-4 py-3"
      style={{
        backgroundColor: PDF_COLORS.highlightYellow,
        borderLeft: `4px solid ${PDF_COLORS.highlightYellowBorder}`,
      }}
    >
      {title && (
        <p className="mb-1 text-[11px] font-bold" style={{ color: PDF_COLORS.textDark }}>
          {title}
        </p>
      )}
      <div className="text-[10px] leading-relaxed" style={{ color: PDF_COLORS.textSecondary }}>
        {children}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// GreenHighlightBox — green box (#E6F4ED) with border (#1A8754)
// ---------------------------------------------------------------------------

export function GreenHighlightBox({ children }: { children: ReactNode }) {
  return (
    <div
      className="rounded-sm px-4 py-3"
      style={{
        backgroundColor: PDF_COLORS.lightGreen,
        border: `1px solid ${PDF_COLORS.accentGreen}`,
      }}
    >
      {children}
    </div>
  )
}

// ---------------------------------------------------------------------------
// GrayBox — neutral gray (#F7F8FA) box for explanations
// ---------------------------------------------------------------------------

export function GrayBox({
  title,
  children,
}: {
  title?: string
  children: ReactNode
}) {
  return (
    <div
      className="rounded-sm px-4 py-3"
      style={{ backgroundColor: PDF_COLORS.warmGray }}
    >
      {title && (
        <p className="mb-1 text-[11px] font-bold" style={{ color: PDF_COLORS.textDark }}>
          {title}
        </p>
      )}
      <div className="text-[10px] leading-relaxed" style={{ color: PDF_COLORS.textSecondary }}>
        {children}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// StepBox — white box with left green border for "Proximos Passos"
// ---------------------------------------------------------------------------

export function StepBox({
  stepNumber,
  title,
  description,
}: {
  stepNumber: number
  title: string
  description: string
}) {
  return (
    <div
      className="rounded-sm px-4 py-2.5"
      style={{
        backgroundColor: PDF_COLORS.white,
        border: `1px solid ${PDF_COLORS.borderGray}`,
        borderLeft: `4px solid ${PDF_COLORS.accentGreen}`,
      }}
    >
      <p className="text-[11px] font-bold" style={{ color: PDF_COLORS.textDark }}>
        {stepNumber}. {title}
      </p>
      <p className="mt-0.5 text-[10px] leading-relaxed" style={{ color: PDF_COLORS.textSecondary }}>
        {description}
      </p>
    </div>
  )
}

// ---------------------------------------------------------------------------
// HorizontalCommitmentBar — colored bar with conditional colors
// ---------------------------------------------------------------------------

export function HorizontalCommitmentBar({
  label,
  percent,
  valueCent,
}: {
  label: string
  percent: number | null
  valueCent: number
}) {
  const displayPercent = percent ?? 0
  const barColor =
    displayPercent > 15
      ? PDF_COLORS.accentRed
      : displayPercent > 8
        ? PDF_COLORS.orangeAccent
        : PDF_COLORS.accentGreen

  const formattedValue = (valueCent / 100).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  })
  const formattedPercent =
    percent !== null
      ? `${percent.toFixed(1).replace('.', ',')}%`
      : 'N/D'

  return (
    <div className="mb-1.5">
      <div className="mb-0.5 flex items-center justify-between text-[10px]">
        <span className="font-medium" style={{ color: PDF_COLORS.textDark }}>{label}</span>
        <span style={{ color: PDF_COLORS.textSecondary }}>
          {formattedPercent} - {formattedValue}/mês
        </span>
      </div>
      <div
        className="h-2.5 w-full rounded-sm"
        style={{ backgroundColor: PDF_COLORS.borderGray }}
      >
        <div
          className="h-2.5 rounded-sm"
          style={{
            backgroundColor: barColor,
            width: `${Math.min(Math.max(displayPercent * 2.5, 3), 100)}%`,
          }}
        />
      </div>
    </div>
  )
}
