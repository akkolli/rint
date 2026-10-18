import type { Sample } from '@/types/rint'
import { metricSeries, routeSegments } from '@/utils/activityStream'
import type { ChartValue } from '@/utils/activityStream'

export const routePalette = [
  'var(--r-route-0)',
  'var(--r-route-1)',
  'var(--r-route-2)',
  'var(--r-route-3)',
  'var(--r-route-4)',
]
export function nearbyReading(
  rows: ChartValue[],
  time: number
): ChartValue | undefined {
  if (!rows.length || time < rows[0].t || time > rows[rows.length - 1].t) return
  let lo = 0,
    hi = rows.length
  while (lo < hi) {
    const mid = (lo + hi) >>> 1
    if (rows[mid].t < time) lo = mid + 1
    else hi = mid
  }
  const a = rows[Math.max(0, lo - 1)],
    b = rows[Math.min(rows.length - 1, lo)]
  if (
    time !== a.t &&
    time !== b.t &&
    (b.t - a.t > 60 || a.segment !== b.segment)
  )
    return
  const nearest = Math.abs(a.t - time) <= Math.abs(b.t - time) ? a : b
  return Math.abs(nearest.t - time) <= 15 ? nearest : undefined
}
export function routeIntensity(
  points: Sample[],
  metric: string,
  sampled = false
) {
  const readings = metricSeries(points, metric)
  const values = readings.map((p) => p.v)
  const low = values.reduce((a, b) => Math.min(a, b), Infinity),
    high = values.reduce((a, b) => Math.max(a, b), -Infinity)
  const sections: { points: Sample[]; band?: number }[] = []
  for (const segment of routeSegments(points, sampled)) {
    const stride = Math.max(1, Math.ceil(segment.length / 500))
    const fixes = segment.filter(
      (_, i) => i === 0 || i === segment.length - 1 || i % stride === 0
    )
    for (let i = 1; i < fixes.length; i++) {
      const a = fixes[i - 1],
        b = fixes[i],
        reading = nearbyReading(readings, (a.t + b.t) / 2)
      const band = reading
        ? Math.min(
            4,
            Math.max(
              0,
              Math.floor(((reading.v - low) / Math.max(0.001, high - low)) * 5)
            )
          )
        : undefined
      const last = sections[sections.length - 1]
      if (
        last &&
        last.band === band &&
        last.points[last.points.length - 1] === a
      )
        last.points.push(b)
      else sections.push({ points: [a, b], band })
    }
  }
  return {
    readings,
    low: Number.isFinite(low) ? low : 0,
    high: Number.isFinite(high) ? high : 0,
    sections,
  }
}
