export interface Sample {
  t: number
  d: number
  active: boolean
  distance_gap?: boolean
  route_gap?: boolean
  lat?: number
  lon?: number
  heart_rate?: number
  cadence?: number
  power?: number
  elevation?: number
}
export interface Interval {
  start: number
  end: number
  elapsed_s: number
  moving_s: number
  active_s: number
  paused_s: number
  distance_m: number
  pace_s_km: number | null
  averages: Record<string, number>
  coverage_s: Record<string, number>
  complete?: boolean
  name?: string
  active_energy_kcal?: number
  health_reported_active_s?: number
}
export interface Analysis {
  method_version: string
  recording: {
    points: Sample[]
    started_at: string
    laps: Interval[]
    summary_only?: boolean
  }
  summary: Interval
  splits_km: Interval[]
  splits_mile: Interval[]
  laps: Interval[]
  best_efforts: {
    distance_m: number
    elapsed_s: number
    start: number
    end: number
  }[]
  warnings: string[]
}
export interface ImportItem {
  index: number
  title: string
  sport: string
  date: string
  status: 'pending' | 'imported' | 'duplicate' | 'error'
  error?: string
  warnings?: string[]
  workout_id?: string
  photos: string[]
}
export interface ImportBatch {
  id: string
  items: ImportItem[]
  total: number
  completed: number
  visibility: string
}
