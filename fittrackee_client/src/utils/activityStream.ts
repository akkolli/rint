import type { Sample } from '@/types/rint'

export interface ChartValue {
  t: number
  v: number
  segment: number
}

export function metricSeries(
  points: Sample[],
  metric: string,
  distanceUnit = 1000
): ChartValue[] {
  const result: ChartValue[] = []
  let segment = 0,
    last = -Infinity,
    interrupted = false,
    windowStart = 0
  points.forEach((p, i) => {
    const previous = points[i - 1]
    let v: unknown = p[metric as keyof Sample]
    if (metric === 'pace') {
      v = null
      if (
        previous?.active &&
        !p.distance_gap &&
        !previous.distance_gap &&
        p.d > previous.d &&
        p.t - previous.t <= 60
      ) {
        while (windowStart < i - 1 && points[windowStart + 1].t <= p.t - 30)
          windowStart++
        const anchor = points[windowStart],
          next = points[windowStart + 1]
        const target = Math.max(anchor.t, p.t - 30)
        const anchorDistance =
          anchor.d +
          (next && next.t > anchor.t
            ? ((next.d - anchor.d) * (target - anchor.t)) / (next.t - anchor.t)
            : 0)
        const dt = p.t - target,
          distance = p.d - anchorDistance
        if (dt >= 5 && distance / dt >= 0.3)
          v = ((dt / distance) * distanceUnit) / 60
      } else windowStart = i
    }
    if (typeof v !== 'number' || !Number.isFinite(v)) {
      if (metric === 'pace') interrupted = true
      return
    }
    if (p.t - last > 60 || interrupted) segment++
    result.push({ t: p.t, v, segment })
    last = p.t
    interrupted = false
  })
  return result
}

export function seriesBounds(
  rows: ChartValue[],
  metric: string,
  fullRange = false
): [number, number] {
  const values = rows
    .map((p) => p.v)
    .filter(Number.isFinite)
    .sort((a, b) => a - b)
  if (!values.length) return [0, 1]
  const lo = values[0]
  let hi = values[values.length - 1]
  if (metric === 'pace' && !fullRange && values.length >= 20) {
    const q1 = values[Math.floor(values.length / 4)],
      q3 = values[Math.floor((values.length * 3) / 4)]
    hi = Math.min(hi, Math.max(q3 + Math.max(1, (q3 - q1) * 3), q3 * 1.25))
  }
  const padding = Math.max(0.5, (hi - lo) * 0.12)
  return [Math.max(0, lo - padding), hi + padding]
}

export function routeSegments(points: Sample[], sampled = false): Sample[][] {
  const result: Sample[][] = []
  let row: Sample[] = []
  for (const p of points) {
    const located = Number.isFinite(p.lat) && Number.isFinite(p.lon)
    if (
      p.route_gap ||
      (located && !sampled && row.length && p.t - row[row.length - 1].t > 60)
    ) {
      if (row.length > 1) result.push(row)
      row = []
    }
    if (located) row.push(p)
  }
  if (row.length > 1) result.push(row)
  return result
}

// Keep first/last/min/max in each time bucket so short peaks survive rendering.
// Segment IDs are assigned before reducing samples; no visual gap is bridged.
export function sampleEnvelope(
  rows: ChartValue[],
  buckets = 750
): ChartValue[] {
  if (rows.length <= buckets * 4) return rows
  const origin = rows[0].t,
    duration = rows[rows.length - 1].t - origin || 1
  const result: ChartValue[] = []
  let first = 0
  for (let i = 1; i <= rows.length; i++) {
    if (
      i < rows.length &&
      Math.floor(((rows[i].t - origin) / duration) * buckets) ===
        Math.floor(((rows[first].t - origin) / duration) * buckets)
    )
      continue
    let min = first,
      max = first
    for (let j = first + 1; j < i; j++) {
      if (rows[j].v < rows[min].v) min = j
      if (rows[j].v > rows[max].v) max = j
    }
    for (const index of [...new Set([first, min, max, i - 1])].sort(
      (a, b) => a - b
    ))
      result.push(rows[index])
    first = i
  }
  return result
}

export function nearestValue(
  rows: ChartValue[],
  time: number
): ChartValue | null {
  if (!rows.length) return null
  let lo = 0,
    hi = rows.length
  while (lo < hi) {
    const mid = Math.floor((lo + hi) / 2)
    if (rows[mid].t < time) lo = mid + 1
    else hi = mid
  }
  const a = rows[Math.max(0, lo - 1)],
    b = rows[Math.min(rows.length - 1, lo)]
  if (time < rows[0].t || time > rows[rows.length - 1].t) return null
  if (
    time !== a.t &&
    time !== b.t &&
    (b.t - a.t > 60 || a.segment !== b.segment)
  )
    return null
  const point = Math.abs(a.t - time) <= Math.abs(b.t - time) ? a : b
  return Math.abs(point.t - time) <= 60 ? point : null
}
