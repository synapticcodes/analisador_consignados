'use client'

/**
 * Job Progress Page - Acompanhamento do processamento
 */

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { toast } from 'sonner'
import {
  Loader2,
  CheckCircle2,
  XCircle,
  Clock,
  FileText,
  Zap,
  BarChart,
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { pollJobStatus } from '@/lib/api'
import {
  type AnalysisJobResponse,
  getStatusColor,
  getStatusLabel,
  formatDate,
  formatCompetencia,
} from '@/types/api'

// =============================================
// Pipeline Steps
// =============================================

const PIPELINE_STEPS = [
  { id: 1, name: 'PDF Extraction', icon: FileText },
  { id: 2, name: 'Router LLM', icon: Zap },
  { id: 3, name: 'Extractors LLM', icon: Zap },
  { id: 4, name: 'Evidence Gate', icon: CheckCircle2 },
  { id: 5, name: 'Consolidator', icon: BarChart },
  { id: 6, name: 'Compute Engine', icon: BarChart },
]

// =============================================
// Component
// =============================================

export default function JobProgressPage() {
  const router = useRouter()
  const params = useParams()
  const jobId = params?.id as string

  const [job, setJob] = useState<AnalysisJobResponse | null>(null)
  const [currentStep, setCurrentStep] = useState(1)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (!jobId) {
      toast.error('ID do job inválido')
      router.push('/upload')
      return
    }

    // Iniciar polling
    pollJobStatus(jobId, (updatedJob) => {
      setJob(updatedJob)
      setIsLoading(false)

      // Simular progresso dos steps baseado no status
      if (updatedJob.status === 'PENDING') {
        setCurrentStep(1)
      } else if (updatedJob.status === 'RUNNING') {
        // Simular progresso incremental
        setCurrentStep((prev) => Math.min(prev + 1, 5))
      } else if (updatedJob.status === 'SUCCEEDED') {
        setCurrentStep(6)
        toast.success('Análise concluída!')
      } else if (updatedJob.status === 'FAILED') {
        toast.error('Erro no processamento')
      }
    })
      .then((finalJob) => {
        // Polling terminou
        if (finalJob.status === 'SUCCEEDED') {
          // Aguardar 1 segundo antes de redirecionar
          setTimeout(() => {
            router.push(`/jobs/${jobId}/result`)
          }, 1000)
        }
      })
      .catch((error) => {
        console.error('Polling error:', error)
        toast.error('Erro ao consultar status do job')
        setIsLoading(false)
      })
  }, [jobId, router])

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <Loader2 className="mx-auto mb-4 h-12 w-12 animate-spin text-blue-600" />
          <p className="text-gray-600">Carregando...</p>
        </div>
      </div>
    )
  }

  if (!job) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="text-center">Job não encontrado</CardTitle>
          </CardHeader>
          <CardContent className="text-center">
            <XCircle className="mx-auto mb-4 h-16 w-16 text-red-500" />
            <p className="text-gray-600">
              O job com ID <code className="rounded bg-gray-100 px-2 py-1">{jobId}</code> não foi encontrado.
            </p>
          </CardContent>
          <CardFooter className="justify-center">
            <Button onClick={() => router.push('/upload')}>
              Voltar para Upload
            </Button>
          </CardFooter>
        </Card>
      </div>
    )
  }

  const isProcessing = job.status === 'PENDING' || job.status === 'RUNNING'
  const isSuccess = job.status === 'SUCCEEDED'
  const isFailed = job.status === 'FAILED'

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 p-8">
      <div className="mx-auto max-w-4xl">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="mb-2 text-3xl font-bold text-gray-900">
            Processamento em Andamento
          </h1>
          <p className="text-gray-600">Acompanhe o progresso da análise</p>
        </div>

        {/* Status Card */}
        <Card className="mb-6">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Status do Job</CardTitle>
              <Badge className={getStatusColor(job.status)}>
                {getStatusLabel(job.status)}
              </Badge>
            </div>
          </CardHeader>

          <CardContent className="space-y-6">
            {/* Job Info */}
            <div className="grid grid-cols-2 gap-4 rounded-lg bg-gray-50 p-4">
              <div>
                <p className="text-sm text-gray-600">Job ID</p>
                <p className="font-mono text-sm font-medium text-gray-900">
                  {job.id}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Criado em</p>
                <p className="text-sm font-medium text-gray-900">
                  {formatDate(job.created_at)}
                </p>
              </div>
              {job.competencia_alvo && (
                <div>
                  <p className="text-sm text-gray-600">Competência Alvo</p>
                  <p className="text-sm font-medium text-gray-900">
                    {formatCompetencia(job.competencia_alvo)}
                  </p>
                </div>
              )}
              {job.completed_at && (
                <div>
                  <p className="text-sm text-gray-600">Concluído em</p>
                  <p className="text-sm font-medium text-gray-900">
                    {formatDate(job.completed_at)}
                  </p>
                </div>
              )}
            </div>

            {/* Pipeline Progress */}
            {isProcessing && (
              <div className="space-y-4">
                <h3 className="text-sm font-medium text-gray-700">
                  Etapas do Pipeline
                </h3>
                <div className="space-y-3">
                  {PIPELINE_STEPS.map((step) => {
                    const isActive = step.id === currentStep
                    const isCompleted = step.id < currentStep
                    const Icon = step.icon

                    return (
                      <div
                        key={step.id}
                        className={`flex items-center gap-3 rounded-lg border p-3 transition-colors ${
                          isActive
                            ? 'border-blue-300 bg-blue-50'
                            : isCompleted
                              ? 'border-green-300 bg-green-50'
                              : 'border-gray-200 bg-gray-50'
                        }`}
                      >
                        {isCompleted ? (
                          <CheckCircle2 className="h-5 w-5 text-green-600" />
                        ) : isActive ? (
                          <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
                        ) : (
                          <Clock className="h-5 w-5 text-gray-400" />
                        )}
                        <Icon
                          className={`h-5 w-5 ${
                            isActive
                              ? 'text-blue-600'
                              : isCompleted
                                ? 'text-green-600'
                                : 'text-gray-400'
                          }`}
                        />
                        <span
                          className={`text-sm font-medium ${
                            isActive
                              ? 'text-blue-900'
                              : isCompleted
                                ? 'text-green-900'
                                : 'text-gray-600'
                          }`}
                        >
                          {step.name}
                        </span>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {/* Success State */}
            {isSuccess && (
              <div className="rounded-lg border border-green-200 bg-green-50 p-6 text-center">
                <CheckCircle2 className="mx-auto mb-3 h-16 w-16 text-green-600" />
                <h3 className="mb-2 text-lg font-semibold text-green-900">
                  Análise Concluída!
                </h3>
                <p className="mb-4 text-sm text-green-700">
                  Todos os dados foram extraídos e validados com sucesso.
                </p>
                <Button onClick={() => router.push(`/jobs/${jobId}/result`)}>
                  Ver Resultados
                </Button>
              </div>
            )}

            {/* Error State */}
            {isFailed && (
              <div className="rounded-lg border border-red-200 bg-red-50 p-6">
                <div className="flex gap-4">
                  <XCircle className="h-12 w-12 flex-shrink-0 text-red-600" />
                  <div>
                    <h3 className="mb-2 text-lg font-semibold text-red-900">
                      Erro no Processamento
                    </h3>
                    {job.error_code && (
                      <p className="mb-1 text-sm font-medium text-red-800">
                        Código: {job.error_code}
                      </p>
                    )}
                    {job.error_message && (
                      <p className="text-sm text-red-700">
                        {job.error_message}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}
          </CardContent>

          {isFailed && (
            <CardFooter className="justify-center">
              <Button onClick={() => router.push('/upload')}>
                Tentar Novamente
              </Button>
            </CardFooter>
          )}
        </Card>

        {/* Info */}
        {isProcessing && (
          <p className="text-center text-sm text-gray-500">
            ⏱️ Tempo estimado: 30-60 segundos
          </p>
        )}
      </div>
    </div>
  )
}
