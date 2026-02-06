import { formatCurrency, type Offer } from '@/types/api'

type OffersSectionProps = {
  offers: Offer[]
}

const OFFER_ORDER = ['REDUZIDA', 'PRINCIPAL', 'SUPER']

export function OffersSection({ offers }: OffersSectionProps) {
  if (offers.length === 0) return null

  const ordered = [...offers].sort(
    (a, b) => OFFER_ORDER.indexOf(a.kind) - OFFER_ORDER.indexOf(b.kind)
  )

  return (
    <section className="space-y-3">
      <h3 className="text-xl font-semibold text-slate-900">Ofertas de Renegociação</h3>
      <div className="grid grid-cols-3 gap-3">
        {ordered.map((offer) => (
          <div
            key={offer.id}
            className={`rounded-xl border p-3 text-sm ${
              offer.kind === 'PRINCIPAL'
                ? 'border-emerald-400 bg-emerald-50'
                : 'border-slate-200 bg-white'
            }`}
          >
            <p className="text-xs uppercase tracking-wide text-slate-500">{offer.kind}</p>
            <p className="mt-2 text-lg font-semibold text-slate-900">
              {offer.installment_count}x de {formatCurrency(offer.installment_value_cent)}
            </p>
            <p className="text-slate-700">Total: {formatCurrency(offer.total_value_cent)}</p>
            <p className="text-slate-600">Pagamento: {offer.payment_method}</p>
          </div>
        ))}
      </div>
    </section>
  )
}
