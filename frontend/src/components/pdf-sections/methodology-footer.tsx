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
      <div className="mt-6 rounded-xl border border-slate-200 bg-slate-50 p-4">
        <p className="text-sm text-slate-900">
          Próximo passo: fale com nossa equipe no WhatsApp para análise completa.
        </p>
        <p className="mt-2 text-xs text-slate-600">{whatsappText}</p>
      </div>
    </section>
  )
}
