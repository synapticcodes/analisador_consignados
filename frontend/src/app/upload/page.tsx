'use client'

/**
 * Upload Page - Página principal para upload de PDFs
 */

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useDropzone } from 'react-dropzone'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { Upload, FileText, X, AlertCircle } from 'lucide-react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '@/components/ui/card'
import { createAnalysisJob, createProduct, listProducts } from '@/lib/api'
import { parseCurrency, type ProductApi } from '@/types/api'

// =============================================
// Validation Schema
// =============================================

const uploadSchema = z.object({
  renda_mensal_declarada: z.string().optional(),
  gasto_dividas_declarado: z.string().optional(),
  product_id: z.string().min(1, 'Selecione um produto'),
})

type UploadFormData = z.infer<typeof uploadSchema>

// =============================================
// Component
// =============================================

export default function UploadPage() {
  const router = useRouter()
  const [files, setFiles] = useState<File[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [products, setProducts] = useState<ProductApi[]>([])
  const [isLoadingProducts, setIsLoadingProducts] = useState(true)
  const [isProductModalOpen, setIsProductModalOpen] = useState(false)
  const [newProductName, setNewProductName] = useState('')
  const [newProductValue, setNewProductValue] = useState('')
  const [newProductInstallments, setNewProductInstallments] = useState('6,12,18,24')
  const [newProductPix, setNewProductPix] = useState(true)
  const [newProductBoleto, setNewProductBoleto] = useState(true)

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
  } = useForm<UploadFormData>({
    resolver: zodResolver(uploadSchema),
    defaultValues: {
      product_id: '',
    },
  })

  const selectedProductId = watch('product_id')

  useEffect(() => {
    listProducts()
      .then((data) => {
        setProducts(data)
        setIsLoadingProducts(false)
      })
      .catch(() => {
        toast.error('Erro ao carregar produtos')
        setIsLoadingProducts(false)
      })
  }, [])

  // Drag and Drop
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxFiles: 3,
    maxSize: 10 * 1024 * 1024, // 10MB
    onDrop: (acceptedFiles, rejectedFiles) => {
      if (rejectedFiles.length > 0) {
        const error = rejectedFiles[0].errors[0]
        if (error.code === 'file-too-large') {
          toast.error('Arquivo muito grande (máximo 10MB)')
        } else if (error.code === 'file-invalid-type') {
          toast.error('Formato inválido (apenas PDF)')
        } else if (error.code === 'too-many-files') {
          toast.error('Máximo de 3 arquivos')
        } else {
          toast.error('Erro ao adicionar arquivo')
        }
        return
      }

      // Verificar se já não tem 3 arquivos
      if (files.length + acceptedFiles.length > 3) {
        toast.error('Máximo de 3 arquivos')
        return
      }

      setFiles((prev) => [...prev, ...acceptedFiles])
      toast.success(`${acceptedFiles.length} arquivo(s) adicionado(s)`)
    },
  })

  // Remove file
  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const parseInstallments = (value: string): number[] => {
    return value
      .split(',')
      .map((item) => parseInt(item.trim(), 10))
      .filter((item) => !Number.isNaN(item))
  }

  const handleCreateProduct = async () => {
    if (!newProductName.trim()) {
      toast.error('Informe o nome do produto')
      return
    }

    if (!newProductValue.trim()) {
      toast.error('Informe o valor do produto')
      return
    }

    const installments = parseInstallments(newProductInstallments)
    if (installments.length === 0) {
      toast.error('Informe os parcelamentos')
      return
    }
    if (installments.some((value) => value < 6 || value > 24)) {
      toast.error('Parcelamentos devem estar entre 6 e 24')
      return
    }

    if (!newProductPix && !newProductBoleto) {
      toast.error('Selecione pelo menos uma forma de pagamento')
      return
    }

    let baseValueCent: number
    try {
      const baseValue = parseCurrency(newProductValue)
      baseValueCent = Math.round(parseFloat(baseValue) * 100)
    } catch (e) {
      toast.error('Valor do produto inválido')
      return
    }

    try {
      const product = await createProduct({
        name: newProductName.trim(),
        base_value_cent: baseValueCent,
        installments,
        payment_methods: [
          ...(newProductPix ? ['PIX'] : []),
          ...(newProductBoleto ? ['BOLETO'] : []),
        ],
      })
      setProducts((prev) => [product, ...prev])
      setValue('product_id', product.id)
      setIsProductModalOpen(false)
      setNewProductName('')
      setNewProductValue('')
      setNewProductInstallments('6,12,18,24')
      setNewProductPix(true)
      setNewProductBoleto(true)
      toast.success('Produto criado com sucesso')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erro ao criar produto')
    }
  }

  // Submit
  const onSubmit = async (data: UploadFormData) => {
    if (files.length === 0) {
      toast.error('Adicione pelo menos 1 arquivo PDF')
      return
    }

    setIsSubmitting(true)

    try {
      // Validar e converter valores monetários
      let rendaCent: string | undefined
      let gastoCent: string | undefined

      if (data.renda_mensal_declarada?.trim()) {
        try {
          rendaCent = parseCurrency(data.renda_mensal_declarada)
        } catch (e) {
          toast.error('Renda mensal inválida')
          setIsSubmitting(false)
          return
        }
      }

      if (data.gasto_dividas_declarado?.trim()) {
        try {
          gastoCent = parseCurrency(data.gasto_dividas_declarado)
        } catch (e) {
          toast.error('Gasto com dívidas inválido')
          setIsSubmitting(false)
          return
        }
      }

      // Criar job
      const job = await createAnalysisJob({
        files,
        renda_mensal_declarada: rendaCent,
        gasto_dividas_declarado: gastoCent,
        product_id: data.product_id,
      })

      toast.success('Job criado com sucesso!')

      // Redirecionar para página de progresso
      router.push(`/jobs/${job.id}`)
    } catch (error: any) {
      console.error('Error creating job:', error)
      toast.error(
        error.response?.data?.detail || 'Erro ao criar job de análise'
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 p-8">
      <div className="mx-auto max-w-4xl">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="mb-2 text-4xl font-bold text-gray-900">
            Calculadora de Consignados
          </h1>
          <p className="text-lg text-gray-600">
            Extração inteligente de indicadores financeiros de PDFs
          </p>
        </div>

        {/* Upload Form */}
        <form onSubmit={handleSubmit(onSubmit)}>
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Upload de Documentos</CardTitle>
              <CardDescription>
                Envie de 1 a 3 arquivos PDF (folhas de pagamento, contratos de
                consignado ou histórico INSS)
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-6">
              {/* Dropzone */}
              <div
                {...getRootProps()}
                className={`cursor-pointer rounded-lg border-2 border-dashed p-12 text-center transition-colors ${
                  isDragActive
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-300 bg-gray-50 hover:border-gray-400 hover:bg-gray-100'
                }`}
              >
                <input {...getInputProps()} />
                <Upload
                  className={`mx-auto mb-4 h-12 w-12 ${
                    isDragActive ? 'text-blue-500' : 'text-gray-400'
                  }`}
                />
                {isDragActive ? (
                  <p className="text-lg font-medium text-blue-600">
                    Solte os arquivos aqui...
                  </p>
                ) : (
                  <>
                    <p className="mb-2 text-lg font-medium text-gray-700">
                      Arraste arquivos ou clique para selecionar
                    </p>
                    <p className="text-sm text-gray-500">
                      PDF • Máximo 10MB por arquivo • Até 3 arquivos
                    </p>
                  </>
                )}
              </div>

              {/* Files List */}
              {files.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-sm font-medium text-gray-700">
                    Arquivos Selecionados ({files.length}/3)
                  </h3>
                  {files.map((file, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-3"
                    >
                      <div className="flex items-center gap-3">
                        <FileText className="h-5 w-5 text-red-500" />
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            {file.name}
                          </p>
                          <p className="text-xs text-gray-500">
                            {(file.size / 1024 / 1024).toFixed(2)} MB
                          </p>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeFile(index)}
                        className="rounded-full p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Optional Fields */}
              <div className="space-y-4 border-t border-gray-200 pt-6">
                <h3 className="text-sm font-medium text-gray-700">
                  Valores Declarados (Opcional)
                </h3>

                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-700">
                    Renda Mensal
                  </label>
                  <input
                    type="text"
                    placeholder="Ex: 3.500,00"
                    {...register('renda_mensal_declarada')}
                    className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                  />
                  {errors.renda_mensal_declarada && (
                    <p className="mt-1 text-xs text-red-600">
                      {errors.renda_mensal_declarada.message}
                    </p>
                  )}
                </div>

                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-700">
                    Gasto Mensal com Dívidas
                  </label>
                  <input
                    type="text"
                    placeholder="Ex: 800,00"
                    {...register('gasto_dividas_declarado')}
                    className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                  />
                  {errors.gasto_dividas_declarado && (
                    <p className="mt-1 text-xs text-red-600">
                      {errors.gasto_dividas_declarado.message}
                    </p>
                  )}
                </div>
              </div>

              {/* Product Selection */}
              <div className="space-y-4 border-t border-gray-200 pt-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium text-gray-700">
                    Produto (Obrigatório)
                  </h3>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setIsProductModalOpen(true)}
                  >
                    Criar Produto
                  </Button>
                </div>

                {isLoadingProducts ? (
                  <p className="text-sm text-gray-500">Carregando produtos...</p>
                ) : products.length === 0 ? (
                  <p className="text-sm text-gray-500">
                    Nenhum produto cadastrado. Crie um novo para continuar.
                  </p>
                ) : (
                  <div>
                    <label className="mb-1.5 block text-sm font-medium text-gray-700">
                      Selecione um produto
                    </label>
                    <select
                      {...register('product_id')}
                      className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                      defaultValue=""
                    >
                      <option value="" disabled>
                        Escolha um produto
                      </option>
                      {products.map((product) => (
                        <option key={product.id} value={product.id}>
                          {product.name}
                        </option>
                      ))}
                    </select>
                    {errors.product_id && (
                      <p className="mt-1 text-xs text-red-600">
                        {errors.product_id.message}
                      </p>
                    )}
                  </div>
                )}
              </div>

              {/* Info Box */}
              <div className="flex gap-3 rounded-lg border border-blue-200 bg-blue-50 p-4">
                <AlertCircle className="h-5 w-5 flex-shrink-0 text-blue-600" />
                <div className="text-sm text-blue-900">
                  <p className="font-medium">Como funciona?</p>
                  <p className="mt-1 text-blue-700">
                    1. Enviamos seus PDFs para extração automática
                    <br />
                    2. IA identifica documentos e extrai dados
                    <br />
                    3. Validação determinística garante precisão
                    <br />
                    4. Resultados consolidados em segundos
                  </p>
                </div>
              </div>
            </CardContent>

            <CardFooter className="flex justify-between">
              <Button
                type="button"
                variant="outline"
                onClick={() => setFiles([])}
                disabled={files.length === 0 || isSubmitting}
              >
                Limpar Tudo
              </Button>
              <Button
                type="submit"
                isLoading={isSubmitting}
                disabled={files.length === 0 || !selectedProductId || isSubmitting}
              >
                {isSubmitting ? 'Processando...' : 'Iniciar Análise'}
              </Button>
            </CardFooter>
          </Card>
        </form>

        {isProductModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <Card className="w-full max-w-lg">
              <CardHeader>
                <CardTitle>Criar Produto</CardTitle>
                <CardDescription>
                  Preencha as informações do produto para gerar ofertas
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-700">
                    Nome do produto
                  </label>
                  <input
                    type="text"
                    value={newProductName}
                    onChange={(event) => setNewProductName(event.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                  />
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-700">
                    Valor do produto
                  </label>
                  <input
                    type="text"
                    placeholder="Ex: 5.000,00"
                    value={newProductValue}
                    onChange={(event) => setNewProductValue(event.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                  />
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-700">
                    Parcelamentos (6 a 24)
                  </label>
                  <input
                    type="text"
                    placeholder="Ex: 6,12,18,24"
                    value={newProductInstallments}
                    onChange={(event) => setNewProductInstallments(event.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">
                    Formas de pagamento
                  </label>
                  <div className="flex items-center gap-4 text-sm text-gray-700">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={newProductPix}
                        onChange={(event) => setNewProductPix(event.target.checked)}
                      />
                      PIX
                    </label>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={newProductBoleto}
                        onChange={(event) => setNewProductBoleto(event.target.checked)}
                      />
                      Boleto
                    </label>
                  </div>
                </div>
              </CardContent>
              <CardFooter className="flex justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setIsProductModalOpen(false)}
                >
                  Cancelar
                </Button>
                <Button type="button" onClick={handleCreateProduct}>
                  Salvar Produto
                </Button>
              </CardFooter>
            </Card>
          </div>
        )}

        {/* Footer */}
        <p className="text-center text-sm text-gray-500">
          Seus dados são processados de forma segura e confidencial
        </p>
      </div>
    </div>
  )
}
