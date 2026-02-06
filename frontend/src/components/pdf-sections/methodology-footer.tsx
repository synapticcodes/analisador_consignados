import { UnknownsCta } from './unknowns-cta'

type MethodologyFooterProps = {
  whatsappText: string
}

export function MethodologyFooter({ whatsappText }: MethodologyFooterProps) {
  return (
    <section className="flex h-full flex-col justify-between">
      <div>
        <h2 className="text-2xl font-semibold text-slate-900">Metodologia e Próximos Passos</h2>
        <p className="mt-3 text-sm leading-relaxed text-slate-700">
          Esta análise foi baseada exclusivamente nos documentos enviados pelo cliente
          (contracheque e/ou extrato INSS). Os valores apresentados como confirmados
          vêm desses documentos. Simulações são estimativas e dependem de negociação.
        </p>
      </div>
      <div className="mt-6">
        <UnknownsCta whatsappText={whatsappText} />
      </div>
    </section>
  )
}
