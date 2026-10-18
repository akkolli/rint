import { describe, expect, it } from 'vitest'

import { nearbyReading, routeIntensity } from '@/utils/routeIntensity'

describe('recorded intensity along private routes', () => {
  it('uses independent power samples and never draws across a privacy break', () => {
    const points = [
      { t: 0, d: 0, active: true, lat: 40, lon: -73 },
      { t: 5, d: 15, active: true, power: 100 },
      { t: 10, d: 30, active: true, lat: 40.001, lon: -73 },
      { t: 15, d: 45, active: true, power: 300 },
      { t: 20, d: 60, active: true, lat: 40.002, lon: -73 },
      { t: 22, d: 66, active: true, route_gap: true },
      { t: 25, d: 75, active: true, lat: 40.003, lon: -73 },
    ]
    const result = routeIntensity(points, 'power')
    expect(result.low).toBe(100)
    expect(result.high).toBe(300)
    expect(result.sections.map((r) => r.band)).toEqual([0, 4])
    expect(result.sections.map((r) => r.points.map((p) => p.t))).toEqual([
      [0, 10],
      [10, 20],
    ])
    expect(nearbyReading(result.readings, 50)).toBeUndefined()
  })
  it('keeps zero power valid and leaves a real sensor gap uncoloured', () => {
    const result = routeIntensity(
      [
        { t: 0, d: 0, active: true, lat: 40, lon: -73, power: 0 },
        { t: 10, d: 30, active: true, lat: 40.001, lon: -73 },
        { t: 100, d: 300, active: true, power: 200 },
      ],
      'power'
    )
    expect(result.low).toBe(0)
    expect(result.sections[0].band).toBeUndefined()
  })
})
