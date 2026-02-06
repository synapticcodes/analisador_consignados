type UnknownsCtaProps = {
  whatsappText: string
}

export function UnknownsCta({ whatsappText }: UnknownsCtaProps) {
  return (
    <section className="space-y-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
      <h3 className="text-lg font-semibold text-slate-900">O que ainda não sabemos</h3>
      <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
        <li>Seu score de crédito real em bureaus.</li>
        <li>Negativações/protestos fora dos documentos enviados.</li>
        <li>Mapa completo de dívidas em todos os bancos.</li>
        <li>Custos ocultos de cheque especial e cartão rotativo.</li>
      </ul>
      <p className="text-sm text-slate-900">
        Próximo passo: fale com nossa equipe no WhatsApp para análise completa.
      </p>
      <p className="text-xs text-slate-600">{whatsappText}</p>
    </section>
  )
}
