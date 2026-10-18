import { describe, expect, it } from 'vitest'

import {
  metricSeries,
  nearestValue,
  sampleEnvelope,
  routeSegments,
  seriesBounds,
} from '@/utils/activityStream'

describe('activity streams on mobile charts', () => {
  it('preserves a one-sample sensor peak and a real gap during reduction', () => {
    const points = Array.from({ length: 10000 }, (_, i) => ({
      t: i < 5000 ? i : i + 120,
      d: i,
      active: true,
      heart_rate: i === 3241 ? 220 : 140,
    }))
    const rows = sampleEnvelope(metricSeries(points, 'heart_rate'))
    expect(rows.length).toBeLessThanOrEqual(3004)
    expect(rows.some((p) => p.v === 220)).toBe(true)
    expect(rows.find((p) => p.t >= 5120)?.segment).not.toBe(rows[0].segment)
    expect(nearestValue(metricSeries(points, 'heart_rate'), 5060)).toBeNull()
  })
  it('keeps zero power, skips unobserved pace and breaks at a pause', () => {
    const points = [
      { t: 0, d: 0, active: true, power: 0 },
      { t: 10, d: 50, active: false },
      { t: 20, d: 50, active: true },
      { t: 30, d: 100, active: true },
    ]
    expect(metricSeries(points, 'power')[0].v).toBe(0)
    const pace = metricSeries(points, 'pace')
    expect(pace).toHaveLength(2)
    expect(pace[0].segment).not.toBe(pace[1].segment)
  })
})

describe('readable pace and independent route streams', () => {
  it('keeps GPS continuous across sensors and breaks at privacy and GPS gaps', () => {
    const points = [
      { t: 0, d: 0, active: true, lat: 40, lon: -73 },
      { t: 3, d: 0, active: true, heart_rate: 140 },
      { t: 10, d: 30, active: true, lat: 40.001, lon: -73 },
      { t: 15, d: 30, active: true, route_gap: true },
      { t: 20, d: 60, active: true, lat: 40.002, lon: -73 },
      { t: 30, d: 90, active: true, lat: 40.003, lon: -73 },
      { t: 120, d: 100, active: true, lat: 40.004, lon: -73 },
    ]
    expect(routeSegments(points).map((row) => row.map((p) => p.t))).toEqual([
      [0, 10],
      [20, 30],
    ])
  })
  it('uses a rolling window so tiny distance increments do not flatten the pace chart', () => {
    const points = Array.from({ length: 121 }, (_, i) => ({
      t: i,
      d: Math.floor(i / 10) * 30 + (i % 10) * 0.0001,
      active: true,
    }))
    const curve = metricSeries(points, 'pace')
    expect(curve.filter((p) => p.t > 30).every((p) => p.v < 10)).toBe(true)
    const noisy = [...curve, { t: 200, v: 150, segment: 1 }]
    expect(seriesBounds(noisy, 'pace')[1]).toBeLessThan(20)
    expect(seriesBounds(noisy, 'pace', true)[1]).toBeGreaterThan(150)
  })
})
