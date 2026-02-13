import { GrayBox, StepBox } from './pdf-shared'
import { PDF_COLORS } from './pdf-utils'

export function NextStepsPage() {
  return (
    <section className="flex h-full flex-col" style={{ color: PDF_COLORS.textDark }}>
      {/* Steps */}
      <h2 className="text-[16px] font-bold" style={{ color: PDF_COLORS.darkBlue }}>
        Pr&oacute;ximos Passos
      </h2>
      <p className="mt-0.5 mb-2 text-[10px]" style={{ color: PDF_COLORS.mediumGray }}>
        Entenda o que acontece a partir de agora caso voc&ecirc; decida prosseguir.
      </p>

      <div className="space-y-1.5">
        <StepBox
          stepNumber={1}
          title="Proposta formal"
          description="Você recebe a proposta detalhada com os valores de honorários e condições do serviço. Sem surpresas: tudo documentado antes de começar."
        />
        <StepBox
          stepNumber={2}
          title="Formalização"
          description="Após a aceitação, assinamos o contrato de prestação de serviços e coletamos a documentação necessária (contracheque, RG/CPF, comprovante de residência)."
        />
        <StepBox
          stepNumber={3}
          title="Início do processo judicial"
          description="Nossa equipe jurídica ingressa com a ação revisional nos juizados competentes, solicitando a redução imediata das parcelas em folha."
        />
        <StepBox
          stepNumber={4}
          title="Levantamento junto aos bancos"
          description="Entramos em contato com as instituições financeiras para negociar os termos da revisão e acompanhar o andamento do processo."
        />
        <StepBox
          stepNumber={5}
          title="Primeiros resultados*"
          description="Com as liminares concedidas, as novas parcelas passam a ser descontadas em folha, gerando alívio imediato no seu orçamento."
        />
      </div>
      <p className="mt-1 text-[8px]" style={{ color: PDF_COLORS.mediumGray }}>
        * Prazos podem variar conforme o tribunal e a complexidade de cada caso.
      </p>

      {/* Glossary */}
      <div className="mt-3">
        <h3 className="mb-1 text-[12px] font-bold" style={{ color: PDF_COLORS.darkBlue }}>
          Gloss&aacute;rio
        </h3>
        <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-[9px]">
          <div>
            <span className="font-semibold" style={{ color: PDF_COLORS.textDark }}>Consignado:</span>{' '}
            <span style={{ color: PDF_COLORS.textSecondary }}>
              Empr&eacute;stimo com desconto direto em folha de pagamento ou benef&iacute;cio.
            </span>
          </div>
          <div>
            <span className="font-semibold" style={{ color: PDF_COLORS.textDark }}>Parcela atual:</span>{' '}
            <span style={{ color: PDF_COLORS.textSecondary }}>
              Valor mensal descontado hoje no contracheque.
            </span>
          </div>
          <div>
            <span className="font-semibold" style={{ color: PDF_COLORS.textDark }}>Nova parcela:</span>{' '}
            <span style={{ color: PDF_COLORS.textSecondary }}>
              Valor projetado ap&oacute;s a revis&atilde;o judicial do contrato.
            </span>
          </div>
          <div>
            <span className="font-semibold" style={{ color: PDF_COLORS.textDark }}>Saldo devedor:</span>{' '}
            <span style={{ color: PDF_COLORS.textSecondary }}>
              Total restante a ser pago considerando todas as parcelas futuras.
            </span>
          </div>
          <div>
            <span className="font-semibold" style={{ color: PDF_COLORS.textDark }}>Renegocia&ccedil;&atilde;o:</span>{' '}
            <span style={{ color: PDF_COLORS.textSecondary }}>
              Processo de revis&atilde;o contratual visando melhores condi&ccedil;&otilde;es.
            </span>
          </div>
          <div>
            <span className="font-semibold" style={{ color: PDF_COLORS.textDark }}>Comprometimento:</span>{' '}
            <span style={{ color: PDF_COLORS.textSecondary }}>
              Percentual do sal&aacute;rio/benef&iacute;cio usado para pagar empr&eacute;stimos.
            </span>
          </div>
          <div>
            <span className="font-semibold" style={{ color: PDF_COLORS.textDark }}>Contracheque:</span>{' '}
            <span style={{ color: PDF_COLORS.textSecondary }}>
              Documento que detalha os rendimentos e descontos do trabalhador.
            </span>
          </div>
          <div>
            <span className="font-semibold" style={{ color: PDF_COLORS.textDark }}>Rubrica:</span>{' '}
            <span style={{ color: PDF_COLORS.textSecondary }}>
              C&oacute;digo que identifica cada tipo de desconto no contracheque.
            </span>
          </div>
        </div>
      </div>

      {/* Legal disclaimer */}
      <div className="mt-auto">
        <GrayBox title="Informações importantes">
          <p className="mb-1">
            Este relat&oacute;rio tem car&aacute;ter exclusivamente informativo e n&atilde;o
            constitui aconselhamento financeiro, jur&iacute;dico ou fiscal. Os valores e
            proje&ccedil;&otilde;es apresentados s&atilde;o estimativas baseadas nas
            informa&ccedil;&otilde;es fornecidas pelo cliente e no hist&oacute;rico de
            resultados da Credilly.
          </p>
          <p className="mb-1">
            Resultados passados n&atilde;o garantem resultados futuros. As condi&ccedil;&otilde;es
            de renegocia&ccedil;&atilde;o dependem de fatores externos, incluindo
            decis&otilde;es judiciais, pol&iacute;ticas das institui&ccedil;&otilde;es
            financeiras e a situa&ccedil;&atilde;o espec&iacute;fica de cada contrato.
          </p>
          <p>
            Ao prosseguir, o cliente declara ci&ecirc;ncia de que os valores finais podem
            diferir das proje&ccedil;&otilde;es e que a Credilly atuar&aacute; com dilig&ecirc;ncia
            para obter os melhores resultados poss&iacute;veis dentro das
            possibilidades legais.
          </p>
        </GrayBox>

        <p className="mt-2 text-center text-[9px] font-semibold" style={{ color: PDF_COLORS.mediumGray }}>
          Credilly Solu&ccedil;&otilde;es Financeiras Ltda.
        </p>
      </div>
    </section>
  )
}
