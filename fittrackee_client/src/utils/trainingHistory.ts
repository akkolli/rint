export interface TrainingWeek {
  week: string
  sport_id: number
  distance_m: number
  activities: number
  elapsed_s: number
}
export function dateKey(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}
export function recentWeeks(
  rows: TrainingWeek[],
  sport = 0,
  now = new Date(),
  count = 8
): TrainingWeek[] {
  const monday = new Date(now)
  monday.setHours(12, 0, 0, 0)
  monday.setDate(monday.getDate() - ((monday.getDay() + 6) % 7))
  return Array.from({ length: count }, (_, i) => {
    const date = new Date(monday)
    date.setDate(date.getDate() - (count - 1 - i) * 7)
    const week = dateKey(date)
    return rows
      .filter((row) => row.week === week && (!sport || row.sport_id === sport))
      .reduce(
        (sum, row) => ({
          ...sum,
          distance_m: sum.distance_m + row.distance_m,
          activities: sum.activities + row.activities,
          elapsed_s: sum.elapsed_s + row.elapsed_s,
        }),
        { week, sport_id: sport, distance_m: 0, activities: 0, elapsed_s: 0 }
      )
  })
}
export function effortDistance(meters: number): string {
  if (Math.abs(meters - 1609.344) < 0.01) return '1 mile'
  if (Math.abs(meters - 21097.5) < 0.01) return 'Half marathon'
  if (Math.abs(meters - 42195) < 0.01) return 'Marathon'
  return meters < 1000 ? `${meters} m` : `${meters / 1000} km`
}
