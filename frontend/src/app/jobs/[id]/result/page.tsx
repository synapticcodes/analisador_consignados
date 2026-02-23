'use client'

/**
 * Job Results Page - Visualização dos resultados finais
 */

import { useEffect, useMemo, useRef, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { toast } from 'sonner'
import { toPng } from 'html-to-image'
import jsPDF from 'jspdf'
import {
  DollarSign,
  TrendingDown,
  CreditCard,
  AlertTriangle,
  Info,
  ChevronRight,
  ArrowLeft,
  Percent,
  ArrowDownRight,
  ArrowDownLeft,
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import ResultSnapshot from '@/components/result-snapshot'
import LegacyResultSnapshot from '@/components/result-snapshot-legacy'
import { getJobResult } from '@/lib/api'
import { resolvePdfExportTargets } from '@/lib/pdf-export'
import {
  type FinalResultResponse,
  formatCurrency,
  formatCompetencia,
} from '@/types/api'

const MIN_OFFER_QUALIFICATION_CENT = 1621 * 100

// =============================================
// Output Card Component
// =============================================

interface OutputCardProps {
  icon: React.ElementType
  title: string
  value: number | null
  suffix?: string
  color: string
  description?: string
}

function OutputCard({
  icon: Icon,
  title,
  value,
  suffix = '',
  color,
  description,
}: OutputCardProps) {
  return (
    <Card className="transition-shadow hover:shadow-md">
      <CardHeader>
        <div className="flex items-center gap-3">
          <div
            className={`rounded-lg p-2 ${color === 'blue' ? 'bg-blue-100' : color === 'green' ? 'bg-green-100' : color === 'orange' ? 'bg-orange-100' : color === 'red' ? 'bg-red-100' : color === 'purple' ? 'bg-purple-100' : 'bg-gray-100'}`}
          >
            <Icon
              className={`h-5 w-5 ${color === 'blue' ? 'text-blue-600' : color === 'green' ? 'text-green-600' : color === 'orange' ? 'text-orange-600' : color === 'red' ? 'text-red-600' : color === 'purple' ? 'text-purple-600' : 'text-gray-600'}`}
            />
          </div>
          <div className="flex-1">
            <CardTitle className="text-sm font-medium text-gray-600">
              {title}
            </CardTitle>
            {description && (
              <CardDescription className="text-xs">{description}</CardDescription>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-2xl font-bold text-gray-900">
          {value !== null ? formatCurrency(value) : '--'}
          {suffix && <span className="text-base font-normal text-gray-600"> {suffix}</span>}
        </p>
      </CardContent>
    </Card>
  )
}

function buildWhatsappMessage(offers: FinalResultResponse['offers']) {
  if (!offers || offers.length === 0) return ''

  const order = ['REDUZIDA', 'PRINCIPAL', 'SUPER']
  const labels = [
    '⭐ Recomendada (melhor equilíbrio mensal)',
    'Intermediária (menor valor total)',
    'Curta (quita mais rápido)',
  ]

  const orderedOffers = offers
    .filter((offer) => order.includes(offer.kind))
    .sort((a, b) => order.indexOf(a.kind) - order.indexOf(b.kind))
    .slice(0, 3)

  if (orderedOffers.length === 0) return ''

  const headerCount = orderedOffers.length
  const header =
    headerCount === 1
      ? 'Separei 1 condição para você, toda no boleto e sem juros:'
      : `Separei ${headerCount} condições para você, todas no boleto e sem juros:`

  const offerBlocks = orderedOffers.map((offer, index) => {
    const label = labels[index] ?? ''
    const dayLabel = offer.first_payment_days === 1 ? 'dia' : 'dias'
    const firstPayment =
      offer.kind === 'SUPER' && offer.first_payment_days === 1
        ? '1ª parcela amanhã'
        : `1ª parcela em ${offer.first_payment_days} ${dayLabel}`
    const entryDetails =
      offer.entry_value_cent !== undefined && offer.entry_value_cent !== null
        ? `Entrada de ${formatCurrency(offer.entry_value_cent)} ${
            offer.entry_due_days === 1
              ? 'amanhã'
              : offer.entry_due_days && offer.entry_due_days > 1
                ? `em ${offer.entry_due_days} dias`
                : 'no ato'
          } + `
        : ''
    const details = `${entryDetails}${offer.installment_count}x de ${formatCurrency(offer.installment_value_cent)} — ${firstPayment}`
    return [label, details].filter(Boolean).join('\n')
  })

  const closing =
    'A maioria das pessoas com renda parecida com a sua opta pela recomendada, porque fica mais confortável no mês.\n' +
    'Qual faz mais sentido pra você?'

  return [header, ...offerBlocks, closing].join('\n\n')
}

function getBeneficioLiquidoCent(result: FinalResultResponse): number | null {
  const baseCalculo = result.inss_margin?.base_calculo_cent ?? null
  const totalComprometido = result.inss_margin?.total_comprometido_cent ?? null
  if (baseCalculo === null || totalComprometido === null) return null
  const value = baseCalculo - totalComprometido
  return value > 0 ? value : null
}

function getOfferQualificationBaseCent(result: FinalResultResponse): number | null {
  const salarioLiquidoCent =
    result.salario_liquido_cent !== null && result.salario_liquido_cent > 0
      ? result.salario_liquido_cent
      : null
  const beneficioLiquidoCent = getBeneficioLiquidoCent(result)

  if (salarioLiquidoCent !== null && beneficioLiquidoCent !== null) {
    return salarioLiquidoCent + beneficioLiquidoCent
  }
  return salarioLiquidoCent ?? beneficioLiquidoCent
}

// =============================================
// Main Component
// =============================================

export default function JobResultPage() {
  const router = useRouter()
  const params = useParams()
  const jobId = params?.id as string

  const [result, setResult] = useState<FinalResultResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [clientName, setClientName] = useState('')
  const [clientCpf, setClientCpf] = useState('')
  const [exporting, setExporting] = useState<'pdf' | null>(null)
  const snapshotRef = useRef<HTMLDivElement | null>(null)
  const legacySnapshotRef = useRef<HTMLDivElement | null>(null)

  const dateLabel = useMemo(
    () => new Date().toLocaleDateString('pt-BR'),
    []
  )
  const fileDate = useMemo(() => new Date().toISOString().slice(0, 10), [])
  const featurePdfV2Enabled =
    process.env.NEXT_PUBLIC_FEATURE_PDF_V2_ENABLED !== 'false'
  const featurePdfV2Phase2Enabled =
    process.env.NEXT_PUBLIC_FEATURE_PDF_V2_PHASE2_ENABLED !== 'false'
  const featurePdfV2Phase3Enabled =
    process.env.NEXT_PUBLIC_FEATURE_PDF_V2_PHASE3_ENABLED !== 'false'

  const formatCpfInput = (value: string) => {
    const digits = value.replace(/\D/g, '').slice(0, 11)
    if (digits.length <= 3) return digits
    if (digits.length <= 6) return `${digits.slice(0, 3)}.${digits.slice(3)}`
    if (digits.length <= 9) return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6)}`
    return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6, 9)}-${digits.slice(9)}`
  }

  useEffect(() => {
    if (!jobId) {
      toast.error('ID do job inválido')
      router.push('/upload')
      return
    }

    // Buscar resultado
    getJobResult(jobId)
      .then((data) => {
        setResult(data)
        setIsLoading(false)
      })
      .catch((error) => {
        console.error('Error fetching result:', error)

        if (error.response?.status === 202) {
          toast.info('Job ainda está processando')
          router.push(`/jobs/${jobId}`)
        } else if (error.response?.status === 500) {
          toast.error('Job falhou no processamento')
          router.push(`/jobs/${jobId}`)
        } else {
          toast.error('Erro ao buscar resultado')
        }

        setIsLoading(false)
      })
  }, [jobId, router])

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
          <p className="text-gray-600">Carregando resultados...</p>
        </div>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="text-center">Resultado não encontrado</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-center">
            <AlertTriangle className="mx-auto h-16 w-16 text-orange-500" />
            <p className="text-gray-600">
              Não foi possível carregar o resultado do job.
            </p>
            <Button onClick={() => router.push('/upload')}>
              Voltar para Upload
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  const hasAlerts = result.alerts && result.alerts.length > 0
  const hasOffers = result.offers && result.offers.length > 0
  const singleOffer = hasOffers && result.offers!.length === 1
  const qualificationBaseCent = getOfferQualificationBaseCent(result)
  const isLeadNotQualifiedForOffers =
    qualificationBaseCent !== null &&
    qualificationBaseCent < MIN_OFFER_QUALIFICATION_CENT
  const whatsappMessage = buildWhatsappMessage(result.offers)
  const shouldShowWhatsappMessage =
    hasOffers && whatsappMessage.length > 0 && !isLeadNotQualifiedForOffers

  const baseFileName = `diagnostico-${jobId}-${fileDate}`

  const ensureSnapshot = () => {
    if (!snapshotRef.current) {
      toast.error('Não foi possível gerar o arquivo agora.')
      return null
    }
    return snapshotRef.current
  }

  const captureElementPng = async (element: HTMLElement) => {
    return toPng(element, {
      backgroundColor: '#ffffff',
      cacheBust: true,
      pixelRatio: 2,
    })
  }

  const handleExportPdf = async () => {
    const snapshot = ensureSnapshot()
    if (!snapshot) return

    setExporting('pdf')
    const startedAt = performance.now()
    try {
      const pdf = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4',
      })

      const pageWidth = 210
      const pageHeight = 297
      const exportTargets = resolvePdfExportTargets({
        featurePdfV2Enabled,
        v2Snapshot: snapshotRef.current,
        legacySnapshot: legacySnapshotRef.current,
      })

      if (exportTargets.hasMultipage) {
        for (let index = 0; index < exportTargets.multipagePages.length; index += 1) {
          const dataUrl = await captureElementPng(exportTargets.multipagePages[index])
          if (index > 0) {
            pdf.addPage('a4', 'portrait')
          }
          pdf.addImage(dataUrl, 'PNG', 0, 0, pageWidth, pageHeight, undefined, 'FAST')
        }
        console.info('export_pdf_v2', {
          elapsed_ms: Math.round(performance.now() - startedAt),
          pages: exportTargets.multipagePages.length,
          sections: {
            contracts: result.loan_contracts?.length ?? 0,
            consignado_lines: result.consignado_lines?.length ?? 0,
            has_margin: !!result.inss_margin,
            offers: result.offers?.length ?? 0,
          },
        })
      } else {
        const fallbackPage = exportTargets.legacyPage
        if (!fallbackPage) {
          throw new Error('Snapshot legado de fallback não encontrado')
        }
        const fallbackUrl = await captureElementPng(fallbackPage)
        pdf.addImage(fallbackUrl, 'PNG', 0, 0, pageWidth, pageHeight, undefined, 'FAST')
        console.info('export_pdf_legacy_fallback', {
          elapsed_ms: Math.round(performance.now() - startedAt),
          pages: 1,
        })
      }

      pdf.save(`${baseFileName}.pdf`)
      toast.success('PDF gerado com sucesso')
    } catch (error) {
      console.error('Error exporting PDF:', error)
      try {
        // Fallback de segurança para formato legado de 1 página real.
        const fallbackPage = resolvePdfExportTargets({
          featurePdfV2Enabled,
          v2Snapshot: snapshotRef.current,
          legacySnapshot: legacySnapshotRef.current,
        }).legacyPage
        if (!fallbackPage) {
          throw new Error('Snapshot legado de fallback não encontrado')
        }
        const fallbackUrl = await captureElementPng(fallbackPage)
        const fallbackPdf = new jsPDF({
          orientation: 'portrait',
          unit: 'mm',
          format: 'a4',
        })
        fallbackPdf.addImage(fallbackUrl, 'PNG', 0, 0, 210, 297, undefined, 'FAST')
        fallbackPdf.save(`${baseFileName}.pdf`)
        toast.success('PDF gerado com fallback de segurança')
      } catch (fallbackError) {
        console.error('Error on PDF fallback:', fallbackError)
        toast.error('Erro ao gerar PDF')
      }
    } finally {
      setExporting(null)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 p-8">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={() => router.push('/upload')}
            className="mb-4"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Nova Análise
          </Button>

          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Resultados da Análise
              </h1>
              <p className="mt-1 text-gray-600">
                Competência: {formatCompetencia(result.competencia_alvo)}
              </p>
            </div>
            <Badge variant="success" className="text-base px-4 py-2">
              ✓ Concluído
            </Badge>
          </div>
        </div>

        {/* Export Panel */}
        <Card className="mb-8 border-blue-100">
          <CardHeader>
            <CardTitle className="text-base font-semibold text-gray-900">
              Exportar diagnóstico
            </CardTitle>
            <CardDescription>
              Gere o PDF para compartilhar com o cliente
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="text-sm font-medium text-gray-700">
                  Nome do cliente (opcional)
                </label>
                <input
                  value={clientName}
                  onChange={(event) => setClientName(event.target.value)}
                  placeholder="Ex.: Maria da Silva"
                  className="mt-2 w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-800 shadow-sm focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">
                  CPF (opcional)
                </label>
                <input
                  value={clientCpf}
                  onChange={(event) => setClientCpf(formatCpfInput(event.target.value))}
                  placeholder="111.111.111-11"
                  inputMode="numeric"
                  className="mt-2 w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-800 shadow-sm focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
                />
              </div>
            </div>
            <div className="mt-6 flex flex-wrap items-center gap-3">
              <Button onClick={handleExportPdf} disabled={exporting !== null}>
                {exporting === 'pdf' ? 'Gerando PDF...' : 'Baixar PDF'}
              </Button>
              <span className="text-xs text-gray-500">
                Data do relatório: {dateLabel}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Alerts */}
        {hasAlerts && (
          <Card className="mb-6 border-orange-200 bg-orange-50">
            <CardHeader>
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-orange-600" />
                <CardTitle className="text-orange-900">
                  Alertas ({result.alerts!.length})
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {result.alerts!.map((alert, index) => (
                  <div
                    key={index}
                    className="flex items-start gap-3 rounded-lg border border-orange-200 bg-white p-3"
                  >
                    {alert.severity === 'ERROR' ? (
                      <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-red-600" />
                    ) : alert.severity === 'WARNING' ? (
                      <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-orange-600" />
                    ) : (
                      <Info className="mt-0.5 h-4 w-4 flex-shrink-0 text-blue-600" />
                    )}
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">
                        {alert.type}
                      </p>
                      <p className="text-sm text-gray-700">{alert.message}</p>
                      {alert.field && (
                        <p className="mt-1 text-xs text-gray-500">
                          Campo: {alert.field}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* 7 Outputs Principais */}
        <div className="mb-8">
          <h2 className="mb-4 text-xl font-semibold text-gray-900">
            Indicadores Financeiros
          </h2>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {/* Salário Bruto */}
            <OutputCard
              icon={DollarSign}
              title="Salário Bruto"
              value={result.salario_bruto_cent}
              color="blue"
              description="Salário bruto do lead antes dos descontos"
            />

            {/* Salário Líquido */}
            <OutputCard
              icon={DollarSign}
              title="Salário Líquido"
              value={result.salario_liquido_cent}
              color="green"
              description="Salário líquido do lead antes dos descontos"
            />

            {/* Total Descontos */}
            <OutputCard
              icon={TrendingDown}
              title="Total de Descontos"
              value={result.total_descontos_cent}
              color="orange"
              description="Soma de todos os descontos"
            />

            {/* Dívida Mensal */}
            <OutputCard
              icon={Percent}
              title="Dívida Mensal"
              value={result.divida_mensal_cent}
              color="blue"
              description="Desconto mensal atual no salário do lead"
            />

            {/* Dívida Mensal Reduzida */}
            <OutputCard
              icon={ArrowDownRight}
              title="Dívida Mensal Reduzida"
              value={result.divida_mensal_reduzida_cent}
              color="green"
              description="Valor estimado que passará a ser descontado do lead"
            />

            {/* Dívida Total Consignada */}
            <OutputCard
              icon={CreditCard}
              title="Dívida Total Consignada"
              value={result.divida_total_consignada_cent}
              color="purple"
              description="Total da soma das dívidas de consignado do lead"
            />

            {/* Dívida Total Reduzida */}
            <OutputCard
              icon={ArrowDownLeft}
              title="Dívida Total Reduzida"
              value={result.divida_total_reduzida_cent}
              color="green"
              description="Valor estimado reduzido das dívidas de consignado do lead"
            />
          </div>
        </div>

        {/* Offers */}
        {hasOffers && (
          <div className="mb-8">
            <h2 className="mb-4 text-xl font-semibold text-gray-900">
              Ofertas do Produto
            </h2>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {result.offers!.map((offer) => (
                <Card key={offer.id} className="border-blue-100">
                  <CardHeader>
                    <CardTitle className="text-sm font-medium text-gray-600">
                      {singleOffer
                        ? 'Oferta Única'
                        : offer.kind === 'PRINCIPAL'
                          ? 'Oferta Principal'
                          : offer.kind === 'REDUZIDA'
                            ? 'Oferta Reduzida'
                            : 'Super Oferta'}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <p className="text-base font-semibold text-gray-900">
                      {offer.text}
                    </p>
                    <div className="text-xs text-gray-500">
                      {offer.entry_value_cent !== undefined &&
                        offer.entry_value_cent !== null && (
                          <p>
                            Entrada: {formatCurrency(offer.entry_value_cent)}{' '}
                            {offer.entry_due_days === 1
                              ? 'amanhã'
                              : offer.entry_due_days && offer.entry_due_days > 1
                                ? `em ${offer.entry_due_days} dias`
                                : 'no ato'}
                          </p>
                        )}
                      <p>
                        Total: {formatCurrency(offer.total_value_cent)}
                      </p>
                      <p>
                        Parcelas: {offer.installment_count}x de{' '}
                        {formatCurrency(offer.installment_value_cent)}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {!hasOffers && isLeadNotQualifiedForOffers && (
          <Card className="mb-8 border-red-200 bg-red-50">
            <CardHeader>
              <div className="flex items-center gap-3">
                <Badge variant="error">Não qualificado</Badge>
                <CardTitle className="text-base font-semibold text-red-900">
                  Ofertas do Produto
                </CardTitle>
              </div>
              <CardDescription className="text-red-800">
                Este lead não se qualifica para nossos serviços.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-red-900">
                A base financeira para elegibilidade ficou abaixo de {formatCurrency(MIN_OFFER_QUALIFICATION_CENT)}.
              </p>
            </CardContent>
          </Card>
        )}

        {/* WhatsApp Message */}
        {shouldShowWhatsappMessage && (
          <Card className="mb-8 border-emerald-100">
            <CardHeader>
              <CardTitle className="text-base font-semibold text-gray-900">
                Mensagem para WhatsApp
              </CardTitle>
              <CardDescription>
                Texto pronto para copiar e enviar
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <textarea
                readOnly
                value={whatsappMessage}
                className="min-h-[120px] w-full resize-none rounded-lg border border-gray-200 bg-gray-50 p-3 text-sm text-gray-700"
              />
              <div className="flex justify-end">
                <Button
                  onClick={async () => {
                    try {
                      await navigator.clipboard.writeText(whatsappMessage)
                      toast.success('Mensagem copiada')
                    } catch (error) {
                      console.error('Error copying message:', error)
                      toast.error('Não foi possível copiar a mensagem')
                    }
                  }}
                >
                  Copiar
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Calculation Methods */}
        {result.calculation_methods && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Métodos de Cálculo</CardTitle>
              <CardDescription>
                Como cada valor foi calculado
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3 md:grid-cols-2">
                {Object.entries(result.calculation_methods)
                  .filter(
                    ([key]) =>
                      !['consignado_mensal', 'parcelas_restantes'].includes(key)
                  )
                  .map(([key, method]) => (
                  <div
                    key={key}
                    className="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 p-3"
                  >
                    <span className="text-sm font-medium text-gray-700">
                      {key.replace(/_/g, ' ')}
                    </span>
                    <Badge variant="default">
                      {method}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Provenance */}
        {result.provenance && (
          <Card>
            <CardHeader>
              <CardTitle>Rastreabilidade</CardTitle>
              <CardDescription>
                Origem dos dados extraídos
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {Object.entries(result.provenance).map(([key, value]) => (
                  <div
                    key={key}
                    className="flex items-start gap-3 rounded-lg border border-gray-200 bg-gray-50 p-3"
                  >
                    <ChevronRight className="mt-0.5 h-4 w-4 flex-shrink-0 text-gray-400" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">
                        {key.replace(/_/g, ' ')}
                      </p>
                      <pre className="mt-1 text-xs text-gray-600">
                        {JSON.stringify(value, null, 2)}
                      </pre>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Footer Info */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>
            Job ID: <code className="rounded bg-gray-100 px-2 py-1">{result.job_id}</code>
          </p>
          <p className="mt-2">
            Todos os valores foram validados deterministicamente com evidências rastreáveis
          </p>
        </div>
      </div>

      <div
        aria-hidden="true"
        className="pointer-events-none fixed left-[-9999px] top-0"
      >
        <ResultSnapshot
          ref={snapshotRef}
          result={result}
          clientName={clientName}
          clientCpf={clientCpf}
          dateLabel={dateLabel}
          whatsappCtaText="WhatsApp: (11) 99999-9999"
          enablePhase2={featurePdfV2Phase2Enabled}
          enablePhase3={featurePdfV2Phase3Enabled}
        />
      </div>
      <div
        aria-hidden="true"
        className="pointer-events-none fixed left-[-9999px] top-0"
      >
        <LegacyResultSnapshot
          ref={legacySnapshotRef}
          result={result}
          clientName={clientName}
          clientCpf={clientCpf}
          dateLabel={dateLabel}
        />
      </div>
    </div>
  )
}
