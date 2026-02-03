'use client'

/**
 * Job Results Page - Visualização dos resultados finais
 */

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { toast } from 'sonner'
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
import { getJobResult } from '@/lib/api'
import {
  type FinalResultResponse,
  formatCurrency,
  formatCompetencia,
} from '@/types/api'

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

// =============================================
// Main Component
// =============================================

export default function JobResultPage() {
  const router = useRouter()
  const params = useParams()
  const jobId = params?.id as string

  const [result, setResult] = useState<FinalResultResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)

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
              description="Remuneração total antes dos descontos"
            />

            {/* Salário Líquido */}
            <OutputCard
              icon={DollarSign}
              title="Salário Líquido"
              value={result.salario_liquido_cent}
              color="green"
              description="Valor recebido após descontos"
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
              description="90% do total de descontos"
            />

            {/* Dívida Mensal Reduzida */}
            <OutputCard
              icon={ArrowDownRight}
              title="Dívida Mensal Reduzida"
              value={result.divida_mensal_reduzida_cent}
              color="green"
              description="25% da dívida mensal"
            />

            {/* Dívida Total Consignada */}
            <OutputCard
              icon={CreditCard}
              title="Dívida Total Consignada"
              value={result.divida_total_consignada_cent}
              color="purple"
              description="Saldo devedor total"
            />

            {/* Dívida Total Reduzida */}
            <OutputCard
              icon={ArrowDownLeft}
              title="Dívida Total Reduzida"
              value={result.divida_total_reduzida_cent}
              color="green"
              description="25% da dívida total consignada"
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
                            {offer.entry_due_days
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
    </div>
  )
}
