'use client'

import { useLayoutEffect, useMemo, useRef, useState } from 'react'

import { formatCurrency, type ConsignadoLineDetail } from '@/types/api'

type ConsignadoBreakdownProps = {
  lines: ConsignadoLineDetail[]
}

const MAX_SECTION_HEIGHT = 940
const MIN_SCALE = 0.72

const DENSITY_STEPS = [
  {
    title: 'text-xl',
    row: 'px-4 py-2 text-sm',
    value: 'text-sm',
    total: 'px-4 py-3 text-sm',
  },
  {
    title: 'text-lg',
    row: 'px-3 py-1.5 text-xs',
    value: 'text-xs',
    total: 'px-3 py-2 text-xs',
  },
  {
    title: 'text-base',
    row: 'px-3 py-1 text-[11px]',
    value: 'text-[11px]',
    total: 'px-3 py-1.5 text-[11px]',
  },
  {
    title: 'text-sm',
    row: 'px-2 py-0.5 text-[10px]',
    value: 'text-[10px]',
    total: 'px-2 py-1 text-[10px]',
  },
] as const

function compactLineLabel(line: ConsignadoLineDetail, maxLength: number): string {
  const descricao =
    line.descricao_raw?.trim() ||
    line.descricao_canonica?.trim() ||
    line.descricao?.trim() ||
    'Sem descrição'
  const base = `${descricao} · Rub ${line.rubrica ?? '--'}`
  if (base.length <= maxLength) return base
  return `${base.slice(0, Math.max(0, maxLength - 1))}…`
}

export function ConsignadoBreakdown({ lines }: ConsignadoBreakdownProps) {
  if (lines.length === 0) return null

  const [densityIndex, setDensityIndex] = useState(0)
  const [scale, setScale] = useState(1)
  const [measuredHeight, setMeasuredHeight] = useState(0)
  const contentRef = useRef<HTMLDivElement | null>(null)

  useLayoutEffect(() => {
    setDensityIndex(0)
    setScale(1)
    setMeasuredHeight(0)
  }, [lines])

  useLayoutEffect(() => {
    const node = contentRef.current
    if (!node) return

    const rawHeight = node.scrollHeight
    if (!rawHeight) return

    setMeasuredHeight(rawHeight)

    if (rawHeight <= MAX_SECTION_HEIGHT) {
      if (scale !== 1) setScale(1)
      return
    }

    if (densityIndex < DENSITY_STEPS.length - 1) {
      setDensityIndex((current) => Math.min(current + 1, DENSITY_STEPS.length - 1))
      return
    }

    const neededScale = MAX_SECTION_HEIGHT / rawHeight
    const nextScale = Math.max(MIN_SCALE, Math.min(1, neededScale))
    if (Math.abs(nextScale - scale) > 0.01) {
      setScale(nextScale)
    }
  }, [lines, densityIndex, scale])

  const lineTextLimit = useMemo(() => {
    if (densityIndex === 0) return 92
    if (densityIndex === 1) return 84
    if (densityIndex === 2) return 76
    return 68
  }, [densityIndex])

  const displayLines = useMemo(
    () =>
      lines.map((line) => ({
        ...line,
        compactLabel: compactLineLabel(line, lineTextLimit),
      })),
    [lineTextLimit, lines]
  )

  const density = DENSITY_STEPS[densityIndex]
  const total = lines.reduce((acc, item) => acc + item.valor_cent, 0)
  const scaledHeight = measuredHeight ? Math.ceil(measuredHeight * scale) : undefined

  return (
    <section className="space-y-2">
      <div style={scaledHeight ? { height: scaledHeight } : undefined} className="overflow-hidden">
        <div
          ref={contentRef}
          className="origin-top-left"
          style={
            scale < 1
              ? {
                  transform: `scale(${scale})`,
                }
              : undefined
          }
        >
          <h3 className={`${density.title} mb-2 font-semibold text-slate-900`}>
            Linhas do Contracheque
          </h3>
          <div className="rounded-xl border border-slate-200">
            {displayLines.map((line, index) => (
              <div
                key={`${
                  line.descricao_raw ?? line.descricao_canonica ?? line.descricao
                }-${index}`}
                className={`flex items-center justify-between gap-3 border-b border-slate-100 ${density.row} last:border-b-0`}
              >
                <p className="min-w-0 flex-1 truncate font-medium leading-tight text-slate-900">
                  {line.compactLabel}
                </p>
                <p className={`shrink-0 whitespace-nowrap font-semibold text-slate-900 ${density.value}`}>
                  {formatCurrency(line.valor_cent)}
                </p>
              </div>
            ))}
            <div
              className={`flex items-center justify-between bg-slate-50 font-semibold text-slate-900 ${density.total}`}
            >
              <p>Total consignados</p>
              <p>{formatCurrency(total)}</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
