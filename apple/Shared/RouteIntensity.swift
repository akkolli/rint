import Foundation

struct IntensitySection: Identifiable {
  let id: Int
  var points: [Sample]
  let band: Int?
}
struct RouteIntensity {
  let metric: String
  let readings: [ChartReading]
  let low: Double
  let high: Double
  let sections: [IntensitySection]

  static func available(_ points: [Sample]) -> [String] {
    ["power", "heart_rate", "pace"].filter { !ChartStream.values(points, metric: $0).isEmpty }
  }
  static func build(_ points: [Sample], metric: String, sampled: Bool = false) -> Self {
    let readings = ChartStream.values(points, metric: metric)
    let low = readings.map(\.value).min() ?? 0
    let high = readings.map(\.value).max() ?? 0
    var sections: [IntensitySection] = []
    for segment in RouteStream.segments(points, sampled: sampled) {
      let stride = max(1, Int(ceil(Double(segment.count) / 500)))
      let fixes = segment.enumerated().filter {
        $0.offset == 0 || $0.offset == segment.count - 1 || $0.offset % stride == 0
      }.map(\.element)
      for pair in zip(fixes, fixes.dropFirst()) {
        let time = (pair.0.t + pair.1.t) / 2
        let reading = Self.reading(readings, at: time)
        let fraction = reading.map { ($0.value - low) / max(0.001, high - low) }
        let band = fraction.map { min(4, max(0, Int($0 * 5))) }
        if let last = sections.last, last.band == band, last.points.last == pair.0 {
          sections[sections.count - 1].points.append(pair.1)
        } else {
          sections.append(
            IntensitySection(id: sections.count, points: [pair.0, pair.1], band: band))
        }
      }
    }
    return Self(metric: metric, readings: readings, low: low, high: high, sections: sections)
  }
  static func reading(_ readings: [ChartReading], at time: Double) -> ChartReading? {
    guard let reading = ChartStream.nearest(readings, at: time), abs(reading.t - time) <= 15 else {
      return nil
    }
    return reading
  }
}
