import { GrayBox, StepBox } from './pdf-shared'
import { PDF_COLORS } from './pdf-utils'

export function NextStepsPage({ isExtratoOnlyContext = false }: { isExtratoOnlyContext?: boolean }) {
  return (
    <section className="flex h-full flex-col" style={{ color: PDF_COLORS.textDark }}>
      {/* Steps */}
      <h2 className="text-[16px] font-bold" style={{ color: PDF_COLORS.darkBlue }}>
        Próximos Passos
      </h2>
      <p className="mt-0.5 mb-2 text-[10px]" style={{ color: PDF_COLORS.mediumGray }}>
        Entenda o que acontece a partir de agora caso você decida prosseguir.
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
          description={
            isExtratoOnlyContext
              ? 'Após a aceitação, assinamos o contrato de prestação de serviços e coletamos a documentação necessária (extrato INSS, RG/CPF, comprovante de residência).'
              : 'Após a aceitação, assinamos o contrato de prestação de serviços e coletamos a documentação necessária (contracheque, RG/CPF, comprovante de residência).'
          }
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

      <div
        className="mt-2 rounded-sm px-3 py-2"
        style={{
          backgroundColor: PDF_COLORS.warmGray,
          borderLeft: `4px solid ${PDF_COLORS.accentGreen}`,
          border: `1px solid ${PDF_COLORS.borderGray}`,
        }}
      >
        <p className="text-[10px] font-semibold" style={{ color: PDF_COLORS.textDark }}>
          Caso real - como funciona na prática:
        </p>
        <ul className="mt-1 space-y-0.5 text-[9px] leading-relaxed" style={{ color: PDF_COLORS.textSecondary }}>
          <li>Dia 1 - Cliente assinou o contrato com a Credilly</li>
          <li>Dia 7 - Ações revisionais protocoladas nos juizados</li>
          <li>Dia 18 - Liminar concedida para 4 dos 9 contratos</li>
          <li>Dia 35 - Liminares concedidas para os demais contratos</li>
          <li>Dia 40 - Novas parcelas já refletidas no contracheque</li>
        </ul>
        <p className="mt-1 text-[9px] font-semibold" style={{ color: PDF_COLORS.accentGreen }}>
          Resultado: parcelas reduzidas de R$ 2.800 para R$ 720/mês
        </p>
      </div>

      {/* Glossary */}
      <div className="mt-3">
        <h3 className="mb-1 text-[12px] font-bold" style={{ color: PDF_COLORS.darkBlue }}>
          Glossário
        </h3>
        <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-[9px]">
          <div>
            <span className="font-semibold" style={{ color: PDF_COLORS.textDark }}>Consignado:</span>{' '}
            <span style={{ color: PDF_COLORS.textSecondary }}>
              Empréstimo com desconto direto em folha de pagamento ou benefício.
            </span>
          </div>
          <div>
            <span className="font-semibold" style={{ color: PDF_COLORS.textDark }}>Parcela atual:</span>{' '}
            <span style={{ color: PDF_COLORS.textSecondary }}>
              {isExtratoOnlyContext
                ? 'Valor mensal descontado hoje no benefício.'
                : 'Valor mensal descontado hoje no contracheque.'}
            </span>
          </div>
          <div>
            <span className="font-semibold" style={{ color: PDF_COLORS.textDark }}>Nova parcela:</span>{' '}
            <span style={{ color: PDF_COLORS.textSecondary }}>
              Valor projetado após a revisão judicial do contrato.
            </span>
          </div>
          <div>
            <span className="font-semibold" style={{ color: PDF_COLORS.textDark }}>Saldo devedor:</span>{' '}
            <span style={{ color: PDF_COLORS.textSecondary }}>
              Total restante a ser pago considerando todas as parcelas futuras.
            </span>
          </div>
          <div>
            <span className="font-semibold" style={{ color: PDF_COLORS.textDark }}>Renegociação:</span>{' '}
            <span style={{ color: PDF_COLORS.textSecondary }}>
              Processo de revisão contratual visando melhores condições.
            </span>
          </div>
          <div>
            <span className="font-semibold" style={{ color: PDF_COLORS.textDark }}>Comprometimento:</span>{' '}
            <span style={{ color: PDF_COLORS.textSecondary }}>
              Percentual do salário/benefício usado para pagar empréstimos.
            </span>
          </div>
          <div>
            <span className="font-semibold" style={{ color: PDF_COLORS.textDark }}>
              {isExtratoOnlyContext ? 'Extrato INSS:' : 'Contracheque:'}
            </span>{' '}
            <span style={{ color: PDF_COLORS.textSecondary }}>
              {isExtratoOnlyContext
                ? 'Documento que detalha os contratos e descontos vinculados ao benefício.'
                : 'Documento que detalha os rendimentos e descontos do trabalhador.'}
            </span>
          </div>
          <div>
            <span className="font-semibold" style={{ color: PDF_COLORS.textDark }}>Rubrica:</span>{' '}
            <span style={{ color: PDF_COLORS.textSecondary }}>
              {isExtratoOnlyContext
                ? 'Código que identifica cada tipo de desconto no extrato INSS.'
                : 'Código que identifica cada tipo de desconto no contracheque.'}
            </span>
          </div>
        </div>
      </div>

      {/* Legal disclaimer */}
      <div className="mt-auto">
        <GrayBox title="Informações importantes">
          <p className="mb-1">
            Este relatório tem caráter exclusivamente informativo e não
            constitui aconselhamento financeiro, jurídico ou fiscal. Os valores e
            projeções apresentados são estimativas baseadas nas
            informações fornecidas pelo cliente e no histórico de
            resultados da Credilly.
          </p>
          <p className="mb-1">
            Resultados passados não garantem resultados futuros. As condições
            de renegociação dependem de fatores externos, incluindo
            decisões judiciais, políticas das instituições
            financeiras e a situação específica de cada contrato.
          </p>
          <p>
            Ao prosseguir, o cliente declara ciência de que os valores finais podem
            diferir das projeções e que a Credilly atuará com diligência
            para obter os melhores resultados possíveis dentro das
            possibilidades legais.
          </p>
        </GrayBox>

        <div
          className="mt-2 rounded-sm px-3 py-2"
          style={{
            backgroundColor: PDF_COLORS.warmGray,
            borderLeft: `4px solid ${PDF_COLORS.accentGreen}`,
            border: `1px solid ${PDF_COLORS.borderGray}`,
          }}
        >
          <p className="text-[10px] font-semibold" style={{ color: PDF_COLORS.textDark }}>
            Identificação da empresa
          </p>
          <div className="mt-1 space-y-0.5 text-[9px]" style={{ color: PDF_COLORS.textSecondary }}>
            <p>Credilly Soluções Financeiras Ltda.</p>
            <p>CNPJ: XX.XXX.XXX/0001-XX</p>
            <p>Endereço: Rua tal, nº tal, São Paulo/SP</p>
            <p>Telefone: (11) XXXX-XXXX</p>
            <p>E-mail: contato@credilly.com.br</p>
          </div>
        </div>
      </div>
    </section>
  )
}
